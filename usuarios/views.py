from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from .forms import RegistroUsuarioForm, DepositoARSForm
from django.contrib import messages
from django.urls import reverse
from .models import Usuario, DepositoARS, Movimiento, Cotizacion, RetiroARS, Notificacion
from decimal import Decimal
import logging
import csv
from django.http import HttpResponse
from django.db.models import Q
from datetime import datetime
from django.utils.timezone import localtime
from .utils import registrar_movimiento, crear_notificacion


logger = logging.getLogger(__name__)



# Create your views here.

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.estado_verificacion = 'pendiente'
            user.is_active = False
            user.save()
            messages.success(request, 'Registro exitoso. Tu cuenta está en pendiente de validación')
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'usuarios/registro.html', {'form': form})    


@login_required
def dashboard(request):
    if request.user.estado_verificacion != 'aprobado':
        return render(request, 'usuarios/no_verificado.html')
    
    movimientos = Movimiento.objects.filter(usuario=request.user).order_by('-fecha')
    cot_usdt = Cotizacion.objects.filter(moneda='USDT').order_by('-fecha').first()
    cot_usd = Cotizacion.objects.filter(moneda='USD').order_by('-fecha').first()
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')[:10]


    return render(request, 'usuarios/dashboard.html', {
        'movimientos': movimientos,
        'cot_usdt': cot_usdt,
        'cot_usd': cot_usd,
        'notificaciones': notificaciones,
    })


def es_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(es_admin)
def panel_admin(request):
    usuarios = Usuario.objects.all().order_by('-date_joined')
    retiros = RetiroARS.objects.all().order_by('-fecha_solicitud')
    depositos = DepositoARS.objects.all().order_by('-fecha')
    movimientos = Movimiento.objects.all().order_by('-fecha')[:50]  # los últimos 50

    return render(request, 'usuarios/panel_admin.html', {
        'usuarios': usuarios,
        'retiros': retiros,
        'depositos': depositos,
        'movimientos': movimientos
    })

@login_required
@user_passes_test(es_admin)
def cambiar_estado_verificacion(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in ['pendiente', 'aprobado', 'rechazado']:
            usuario.estado_verificacion = nuevo_estado
            if nuevo_estado == 'aprobado':
                usuario.is_active = True
            usuario.save()
    return redirect('panel_admin')


@login_required
def agregar_saldo(request):
    if request.method == 'POST':
        form = DepositoARSForm(request.POST, request.FILES)
        if form.is_valid():
            deposito = form.save(commit=False)
            deposito.usuario = request.user
            deposito.estado = 'pendiente'
            deposito.save()

            saldo_actual = request.user.saldo_ars
            registrar_movimiento(
                usuario=request.user,
                tipo='deposito',
                moneda='ARS',
                monto=deposito.monto,
                descripcion='Solicitud de depósito enviada. En revisión.',
                saldo_antes=saldo_actual,
                saldo_despues=saldo_actual
            )
            messages.success(request, 'Solicitud enviada. En breve será verificada')
            return redirect('dashboard')
    else:
        form = DepositoARSForm()

    datos_bancarios = {
        'alias' : 'alias.usuario',
        'cbu' : '0000003100000001234567',
        'banco' : 'banco',
    }        

    return render(request, 'usuarios/agregar_saldo.html', {
        'form': form,
        'datos_bancarios' : datos_bancarios
    })

@login_required
@user_passes_test(es_admin)
def panel_depositos(request):
    depositos = DepositoARS.objects.all().order_by('-fecha')
    return render(request, 'usuarios/panel_depositos.html', {'depositos':depositos})

@login_required
@user_passes_test(es_admin)
def aprobar_deposito(request, deposito_id):
    deposito = get_object_or_404(DepositoARS, id=deposito_id)
    if request.method == 'POST' and deposito.estado == 'pendiente':
        deposito.estado = 'aprobado'
        deposito.save()
        usuario = deposito.usuario
        saldo_antes = usuario.saldo_ars
        usuario.saldo_ars += deposito.monto
        usuario.save()
        saldo_despues = usuario.saldo_ars

        registrar_movimiento(
            usuario=usuario,
            tipo='deposito',
            moneda='ARS',
            monto=deposito.monto,
            descripcion='Depósito aprobado por admin',
            admin=request.user,
            saldo_antes=saldo_antes,
            saldo_despues=saldo_despues
        )
        crear_notificacion(deposito.usuario, f"Tu depósito de ${deposito.monto} ARS fue aprobado.")
        
    return redirect('panel_depositos')    





@login_required
@user_passes_test(es_admin)
def historial_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    movimientos = Movimiento.objects.filter(usuario=usuario).order_by('-fecha')
    return render(request, 'usuarios/historial_usuario.html', {
        'usuario': usuario,
        'movimientos': movimientos
    })

@login_required
@user_passes_test(es_admin)
def rechazar_deposito(request, deposito_id):
    deposito = get_object_or_404(DepositoARS, id=deposito_id)
    if deposito.estado == 'pendiente':
        deposito.estado = 'rechazado'
        deposito.save()
        registrar_movimiento(
            usuario=deposito.usuario,
            tipo='ajuste',
            moneda='ARS',
            monto=0,
            descripcion=f'Depósito rechazado por admin. Monto solicitado: ${deposito.monto}'
        )
    return redirect('panel_depositos')



# @login_required
# def operar(request):
#     cot_usdt = Cotizacion.objects.filter(moneda='USDT').order_by('-fecha').first()
#     cot_usd = Cotizacion.objects.filter(moneda='USD').order_by('-fecha').first()

#     if request.method == 'POST':
#         operacion = request.POST.get('operacion')  # 'compra' o 'venta'
#         moneda = request.POST.get('moneda')        # 'USDT' o 'USD'

#         try:
#             if operacion == 'compra':
#                 monto_ars = Decimal(request.POST.get('monto'))
#                 cot = cot_usdt if moneda == 'USDT' else cot_usd
#                 monto_moneda = monto_ars / cot.venta

#                 if request.user.saldo_ars < monto_ars:
#                     return HttpResponse("Saldo ARS insuficiente", status=400)

#                 # Descontar saldo ARS y acreditar moneda
#                 request.user.saldo_ars -= monto_ars
#                 if moneda == 'USDT':
#                     request.user.saldo_usdt += monto_moneda
#                 else:
#                     request.user.saldo_usd += monto_moneda
#                 request.user.save()

#                 # Movimientos 
#                 Movimiento.objects.create(
#                     usuario=request.user,
#                     tipo='compra',
#                     moneda='ARS',
#                     monto=-monto_ars,
#                     descripcion=f'Compra de {moneda} a ${cot.venta}'
#                 )
#                 Movimiento.objects.create(
#                     usuario=request.user,
#                     tipo='compra',
#                     moneda=moneda,
#                     monto=monto_moneda,
#                     descripcion=f'Compra de {moneda} con ${monto_ars} ARS'
#                 )

#             elif operacion == 'venta':
#                 monto_moneda = Decimal(request.POST.get('monto'))
#                 cot = cot_usdt if moneda == 'USDT' else cot_usd
#                 monto_ars = monto_moneda * cot.compra

#                 if moneda == 'USDT' and request.user.saldo_usdt < monto_moneda:
#                     return HttpResponse("Saldo USDT insuficiente", status=400)
#                 elif moneda == 'USD' and request.user.saldo_usd < monto_moneda:
#                     return HttpResponse("Saldo USD insuficiente", status=400)

#                 # Descontar moneda y acreditar ARS
#                 if moneda == 'USDT':
#                     request.user.saldo_usdt -= monto_moneda
#                 else:
#                     request.user.saldo_usd -= monto_moneda
#                 request.user.saldo_ars += monto_ars
#                 request.user.save()

#                 # Movimientos 
#                 Movimiento.objects.create(
#                     usuario=request.user,
#                     tipo='venta',
#                     moneda=moneda,
#                     monto=-monto_moneda,
#                     descripcion=f'Venta de {moneda} a ${cot.compra}'
#                 )
#                 Movimiento.objects.create(
#                     usuario=request.user,
#                     tipo='venta',
#                     moneda='ARS',
#                     monto=monto_ars,
#                     descripcion=f'Venta de {moneda}. ARS acreditado.'
#                 )

#             return redirect('dashboard')

#         except Exception as e:
#             logger.error(f"[OPERAR ERROR] Usuario: {request.user.username} - Error: {str(e)}")
#             return HttpResponse("Ocurrió un error al procesar la operación.", status=400)


#     return render(request, 'usuarios/operar.html', {
#         'cot_usdt': cot_usdt,
#         'cot_usd': cot_usd,
#     })

@login_required
def operar(request):
    # Obtener última cotización ya con comisión aplicada
    cot_usdt = Cotizacion.objects.filter(moneda='USDT').order_by('-fecha').first()
    cot_usd = Cotizacion.objects.filter(moneda='USD').order_by('-fecha').first()

    if not cot_usdt or not cot_usd:
        return HttpResponse("No hay cotización disponible. Intentá más tarde.", status=503)

    # Usar directamente los valores de la BD (ya tienen comisión aplicada)
    cot_usdt_compra = cot_usdt.compra
    cot_usdt_venta = cot_usdt.venta
    cot_usd_compra = cot_usd.compra
    cot_usd_venta = cot_usd.venta

    if request.method == 'POST':
        operacion = request.POST.get('operacion')
        moneda = request.POST.get('moneda')

        try:
            monto = Decimal(request.POST.get('monto'))

            if operacion == 'compra':
                cot = cot_usdt_venta if moneda == 'USDT' else cot_usd_venta
                exito, error = procesar_compra(request.user, moneda, monto, cot)
            elif operacion == 'venta':
                cot = cot_usdt_compra if moneda == 'USDT' else cot_usd_compra
                exito, error = procesar_venta(request.user, moneda, monto, cot)
            else:
                return HttpResponse("Operación no válida", status=400)

            if not exito:
                return HttpResponse(error, status=400)

            return redirect('dashboard')

        except Exception as e:
            logger.error(f"[OPERAR ERROR] Usuario: {request.user.username} - Error: {str(e)}")
            return HttpResponse("Ocurrió un error al procesar la operación.", status=400)

    return render(request, 'usuarios/operar.html', {
        'cot_usdt': {'compra': cot_usdt_compra, 'venta': cot_usdt_venta},
        'cot_usd': {'compra': cot_usd_compra, 'venta': cot_usd_venta},
    })



def procesar_compra(usuario, moneda, monto_ars, cotizacion_venta):
    if usuario.saldo_ars < monto_ars:
        return False, "Saldo ARS insuficiente"

    monto_moneda = monto_ars / cotizacion_venta
    # Guardamos saldo actual (en ARS) antes de descontar
    saldo_antes_ars = usuario.saldo_ars
    usuario.saldo_ars -= monto_ars
    if moneda == 'USDT':
        # Para la moneda, capturamos saldo antes (asumiendo que el registro de USDT se hace)
        saldo_antes_moneda = usuario.saldo_usdt
        usuario.saldo_usdt += monto_moneda
        saldo_despues_moneda = usuario.saldo_usdt
    else:
        saldo_antes_moneda = usuario.saldo_usd
        usuario.saldo_usd += monto_moneda
        saldo_despues_moneda = usuario.saldo_usd
    usuario.save()
    saldo_despues_ars = usuario.saldo_ars

    # Registrar movimiento de ARS (descuento)
    registrar_movimiento(
        usuario=usuario,
        tipo='compra',
        moneda='ARS',
        monto=-monto_ars,
        descripcion=f'Compra de {moneda} a ${cotizacion_venta}',
        saldo_antes=saldo_antes_ars,
        saldo_despues=saldo_despues_ars
    )
    # Registrar movimiento de la moneda adquirida (crédito)
    registrar_movimiento(
        usuario=usuario,
        tipo='compra',
        moneda=moneda,
        monto=monto_moneda,
        descripcion=f'Compra de {moneda} con ${monto_ars} ARS',
        saldo_antes=saldo_antes_moneda,
        saldo_despues=saldo_despues_moneda
    )

    return True, None

def procesar_venta(usuario, moneda, monto_moneda, cotizacion_compra):
    if moneda == 'USDT' and usuario.saldo_usdt < monto_moneda:
        return False, "Saldo USDT insuficiente"
    elif moneda == 'USD' and usuario.saldo_usd < monto_moneda:
        return False, "Saldo USD insuficiente"

    # Determinar saldo y actualizar la moneda
    if moneda == 'USDT':
        saldo_antes_moneda = usuario.saldo_usdt
        usuario.saldo_usdt -= monto_moneda
        saldo_despues_moneda = usuario.saldo_usdt
    else:
        saldo_antes_moneda = usuario.saldo_usd
        usuario.saldo_usd -= monto_moneda
        saldo_despues_moneda = usuario.saldo_usd

    monto_ars = monto_moneda * cotizacion_compra
    saldo_antes_ars = usuario.saldo_ars
    usuario.saldo_ars += monto_ars
    usuario.save()
    saldo_despues_ars = usuario.saldo_ars

    # Registrar movimiento de la moneda (descuento)
    registrar_movimiento(
        usuario=usuario,
        tipo='venta',
        moneda=moneda,
        monto=-monto_moneda,
        descripcion=f'Venta de {moneda} a ${cotizacion_compra}',
        saldo_antes=saldo_antes_moneda,
        saldo_despues=saldo_despues_moneda
    )
    # Registrar movimiento en ARS (acreditación)
    registrar_movimiento(
        usuario=usuario,
        tipo='venta',
        moneda='ARS',
        monto=monto_ars,
        descripcion=f'Venta de {moneda}. ARS acreditado.',
        saldo_antes=saldo_antes_ars,
        saldo_despues=saldo_despues_ars
    )

    return True, None


@login_required
def solicitar_retiro(request):
    if request.method == 'POST':
        alias = request.POST.get('alias')
        cbu = request.POST.get('cbu')
        banco = request.POST.get('banco')
        monto = Decimal(request.POST.get('monto'))

        if monto <= 0 or request.user.saldo_ars < monto:
            return HttpResponse("Saldo insuficiente o monto inválido", status=400)

        # Registrar solicitud
        RetiroARS.objects.create(
            usuario=request.user,
            alias=alias,
            cbu=cbu,
            banco=banco,
            monto=monto
        )

        # Registrar movimiento: descontar saldo
        saldo_antes = request.user.saldo_ars
        request.user.saldo_ars -= monto
        request.user.save()
        saldo_despues = request.user.saldo_ars

        registrar_movimiento(
            usuario=request.user,
            tipo='retiro',
            moneda='ARS',
            monto=-monto,
            descripcion=f'Solicitud de retiro ARS ({alias})',
            saldo_antes=saldo_antes,
            saldo_despues=saldo_despues
        )

        return redirect('dashboard')

    return render(request, 'usuarios/solicitar_retiro.html')

@login_required
def historial_retiros(request):
    retiros = RetiroARS.objects.filter(usuario=request.user).order_by('-fecha_solicitud')
    return render(request, 'historial_retiros.html', {'retiros': retiros})

@login_required
@user_passes_test(es_admin)
def aprobar_retiro(request, id):
    retiro = get_object_or_404(RetiroARS, id=id)
    if request.method == 'POST' and retiro.estado == 'pendiente':
        retiro.estado = 'aprobado'
        retiro.save()
    return HttpResponseRedirect(reverse('panel_admin'))

@login_required
@user_passes_test(es_admin)
def enviar_retiro(request, id):
    retiro = get_object_or_404(RetiroARS, id=id)
    if request.method == 'POST' and retiro.estado == 'aprobado':
        retiro.estado = 'enviado'
        retiro.save()
        saldo_actual = retiro.usuario.saldo_ars
        registrar_movimiento(
            usuario=retiro.usuario,
            tipo='retiro',
            moneda='ARS',
            monto=retiro.monto,
            descripcion=f'Retiro de ${retiro.monto} ARS enviado por admin',
            saldo_antes=saldo_actual,
            saldo_despues=saldo_actual
        )
        crear_notificacion(retiro.usuario, f"Tu retiro de ${retiro.monto} ARS fue enviado.")
    return HttpResponseRedirect(reverse('panel_admin'))



@login_required
def exportar_movimientos_usuario(request):
    movimientos = Movimiento.objects.filter(usuario=request.user).order_by('-fecha')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="movimientos_usuario.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID','Fecha', 'Tipo', 'Moneda', 'Monto', 'Saldo antes', 'Saldo después', 'Descripción'])

    for m in movimientos:
        writer.writerow([
            localtime(m.fecha).strftime('%Y-%m-%d %H:%M'),
            m.codigo,
            m.tipo,
            m.moneda,
            m.monto,
            m.saldo_antes,
            m.saldo_despues,
            m.descripcion
        ])

    return response


@login_required
@user_passes_test(es_admin)
def exportar_movimientos_admin(request):
    movimientos = Movimiento.objects.all()

    # Filtros
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')
    moneda = request.GET.get('moneda')
    tipo = request.GET.get('tipo')

    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    if moneda:
        movimientos = movimientos.filter(moneda=moneda)
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    movimientos = movimientos.order_by('-fecha')

    # CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="movimientos_todos.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID','Usuario', 'Fecha', 'Tipo', 'Moneda', 'Monto', 'Saldo antes', 'Saldo después', 'Descripción'])

    for m in movimientos:
        writer.writerow([
            m.codigo,
            m.usuario.username,
            localtime(m.fecha).strftime('%Y-%m-%d %H:%M'),
            m.tipo,
            m.moneda,
            m.monto,
            m.saldo_antes,
            m.saldo_despues,
            m.descripcion
        ])

    return response

@login_required
@user_passes_test(es_admin)
def exportar_historial_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    movimientos = Movimiento.objects.filter(usuario=usuario).order_by('-fecha')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="movimientos_{usuario.username}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Tipo', 'Moneda', 'Monto', 'Saldo antes', 'Saldo después', 'Descripción'])

    for m in movimientos:
        writer.writerow([
            localtime(m.fecha).strftime('%Y-%m-%d %H:%M'),
            m.tipo,
            m.moneda,
            m.monto,
            m.saldo_antes,
            m.saldo_despues,
            m.descripcion
        ])

    return response
