from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cotizacion, RetiroARS
from django.utils.translation import gettext_lazy as _


# Register your models here.

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    model = Usuario

    fieldsets = UserAdmin.fieldsets + (
        (_('Verificación'), {
            'fields': (
                'dni_frente',
                'dni_dorso',
                'estado_verificacion',
            )
        }),
        (_('Saldos'), {
            'fields': (
                'saldo_ars', 
                'saldo_usdt',
            )
        }),
    )

    list_display = (
        'username', 'email', 'is_active', 'estado_verificacion', 'saldo_ars', 'saldo_usdt'
    )

    search_fields = ('username', 'email')


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('moneda', 'compra', 'venta', 'fecha')
    list_filter = ('moneda',)
    ordering = ('-fecha',)


@admin.register(RetiroARS)
class RetiroARSAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'monto', 'alias', 'cbu', 'estado', 'fecha_solicitud')
    list_filter = ('estado',)
    actions = ['aprobar_retiros', 'marcar_como_enviado']

    def aprobar_retiros(self, request, queryset):
        for retiro in queryset.filter(estado='pendiente'):
            retiro.estado = 'aprobado'
            retiro.save()
    aprobar_retiros.short_description = "Aprobar retiros seleccionados"

    def marcar_como_enviado(self, request, queryset):
        for retiro in queryset.filter(estado='aprobado'):
            retiro.estado = 'enviado'
            retiro.save()
    marcar_como_enviado.short_description = "Marcar como enviados"