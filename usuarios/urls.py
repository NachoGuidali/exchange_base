from django.urls import path
from .views import registro, dashboard, panel_admin, cambiar_estado_verificacion, agregar_saldo, panel_depositos, aprobar_deposito, historial_usuario, operar, enviar_retiro, aprobar_retiro, solicitar_retiro, exportar_historial_usuario, exportar_movimientos_admin, exportar_movimientos_usuario
urlpatterns = [
    path('registro/', registro, name='registro'),
    path('dashboard/', dashboard, name='dashboard'),
    path('admin-dashboard/', panel_admin, name='panel_admin'),
    path('admin-dashboard/cambiar-estado/<int:user_id>/', cambiar_estado_verificacion, name='cambiar_estado_verificacion'),
    path('agregar-saldo/', agregar_saldo, name='agregar_saldo'),
    path('admin-dashboard/admin-depositos/', panel_depositos, name='panel_depositos'),
    path('admin-dashboard/aprobar-deposito/<int:deposito_id>/', aprobar_deposito, name='aprobar_deposito'),
    path('historial-usuario/<int:user_id>/', historial_usuario, name='historial_usuario'),
    path('operar/', operar, name='operar'),
    path('admin-dashboard/retiro/aprobar/<int:id>/', aprobar_retiro, name='aprobar_retiro'),
    path('admin-dashboard/retiro/enviar/<int:id>/', enviar_retiro, name='enviar_retiro'),

    path('solicitar-retiro/', solicitar_retiro, name='solicitar_retiro'),
    path('exportar-movimientos/', exportar_movimientos_usuario, name='exportar_movimientos_usuario'),
    path('admin-dashboard/exportar-movimientos/', exportar_movimientos_admin, name='exportar_movimientos_admin'),
    path('admin-dashboard/historial-usuario/<int:user_id>/exportar/', exportar_historial_usuario, name='exportar_historial_usuario'),


]
