from usuarios.models import Notificacion


def registrar_movimiento(usuario, tipo, moneda, monto, descripcion="", admin=None, saldo_antes=None, saldo_despues=None):
    from .models import Movimiento

    Movimiento.objects.create(
        usuario=usuario,
        tipo=tipo,
        moneda=moneda,
        monto=monto,
        descripcion=descripcion,
        admin_responsable=admin,
        saldo_antes=saldo_antes,
        saldo_despues=saldo_despues
    )


def crear_notificacion(usuario, mensaje):
    Notificacion.objects.create(usuario=usuario, mensaje=mensaje)