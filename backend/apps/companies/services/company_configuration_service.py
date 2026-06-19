import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

# Explicit whitelist of configuration fields that can be modified via PATCH
WHITELISTED_CONFIG_FIELDS = {
    'moneda',
    'zona_horaria',
    'idioma',
    'permite_ediciones_gratuitas',
    'permite_programacion',
    'requiere_aprobacion_publicacion',
    'max_sesiones_lector',
    'max_sesiones_empresarial',
    'marca_agua_activa',
    'texto_marca_agua',
    'mostrar_precio_publico',
    'notificaciones_internas'
}

def update_company_configuration(
    *,
    empresa: Empresa,
    actualizado_por: Usuario,
    config_data: dict,
    ip_address: str = None,
    user_agent: str = None
) -> EmpresaConfiguracion:
    """
    Updates company configuration.
    Accepts only whitelisted fields, captures previous values,
    saves the changes, and logs history and audit events.
    """
    # 1. Fetch or create the EmpresaConfiguracion record
    try:
        configuracion = empresa.configuracion
    except EmpresaConfiguracion.DoesNotExist:
        configuracion = EmpresaConfiguracion(empresa=empresa, estado='ACTIVA')

    # 2. Filter input data using the strict whitelist (ignore or reject arbitrary keys)
    filtered_data = {k: v for k, v in config_data.items() if k in WHITELISTED_CONFIG_FIELDS}
    
    # 3. Capture previous values for the updated fields
    valores_anteriores = {field: getattr(configuracion, field) for field in filtered_data.keys() if hasattr(configuracion, field)}

    # 4. Apply updates
    updates = {}
    for field, new_val in filtered_data.items():
        if new_val is not None and new_val != getattr(configuracion, field):
            setattr(configuracion, field, new_val)
            updates[field] = new_val

    # If no updates were actually made, return early
    if not updates:
        return configuracion

    configuracion.fecha_actualizacion = timezone.now()
    configuracion.actualizado_por = actualizado_por

    try:
        with transaction.atomic(using='periodico_db'):
            configuracion.save(using='periodico_db')

            # Write to EmpresaHistorial
            historial = EmpresaHistorial(
                empresa=empresa,
                tipo_evento='CAMBIO_CONFIGURACION',
                estado_anterior=empresa.estado,
                estado_nuevo=empresa.estado,
                motivo='Actualización de configuración empresarial',
                detalle_anterior={k: v for k, v in valores_anteriores.items() if k in updates},
                detalle_nuevo=updates,
                realizado_por=actualizado_por,
                direccion_ip=ip_address,
                resultado='EXITOSO'
            )
            historial.save(using='periodico_db')

            # Write Audit event under savepoint (graceful)
            AuditService.record_event(
                usuario=actualizado_por,
                emp_id=empresa.id,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.CONFIGURACION_EMPRESA_ACTUALIZADA,
                entidad='EmpresaConfiguracion',
                entidad_id=str(configuracion.id),
                valores_anteriores={k: v for k, v in valores_anteriores.items() if k in updates},
                valores_nuevos=updates,
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Configuración de empresa actualizada',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return configuracion
    except Exception as e:
        logger.error(f"Error updating company configuration {empresa.id}: {str(e)}")
        raise ValidationError(f"No se pudo actualizar la configuración: {str(e)}")
