from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
import uuid
from django.conf import settings

# Create your models here.
class Usuario(AbstractUser):
    dni_frente = models.ImageField(upload_to='documentos/', null=True, blank=True)
    dni_dorso = models.ImageField(upload_to='documentos/', null=True, blank=True)
    estado_verificacion = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('aprobado', 'Aprobado'),
            ('rechazado', 'Rechazado')
        ],
        default='pendiente'
    )

    saldo_ars = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    saldo_usdt = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    saldo_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)



    def __str__(self):
        return self.username
    

class DepositoARS(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]    

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    comprobante = models.ImageField(upload_to='comprobantes/')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - ${self.monto} - {self.estado}"
    

class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('deposito', 'Depósito'),
        ('retiro', 'Retiro'),
        ('compra', 'Compra'),
        ('ajuste', 'Ajuste manual'),
    ]

    MONEDA_CHOICES = [
        ('ARS', 'Pesos ARS'),
        ('USDT', 'USDT'),
        ('USD', 'USD'),
    ]

    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    moneda = models.CharField(max_length=10, choices=MONEDA_CHOICES)
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    saldo_antes = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    saldo_despues = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    admin_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acciones_admin'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} - {self.moneda} {self.monto}"


class Cotizacion(models.Model):
    MONEDAS = [
        ('USDT', 'USDT'),
        ('USD', 'USD'),
    ]

    moneda = models.CharField(max_length=10, choices=MONEDAS)
    compra = models.DecimalField(max_digits=20, decimal_places=2)  
    venta = models.DecimalField(max_digits=20, decimal_places=2)   
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.moneda} - Compra: {self.compra} / Venta: {self.venta}"

class RetiroARS(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('enviado', 'Enviado'),
        ('rechazado', 'Reachazado'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alias = models.CharField(max_length=50)
    cbu = models.CharField(max_length=30, blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)


class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=now)

    def __str__(self):
        return f"[{self.usuario.username}] {self.mensaje[:40]}"    