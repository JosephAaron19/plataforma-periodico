import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.companies.selectors.company_file_selectors import validate_company_file_reference
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def update_company_identity(
    *,
    empresa: Empresa,
    actualizado_por: Usuario,
    nombre_publico: str = None,
    descripcion_corta: str = None,
    descripcion_larga: str = None,
    logo_archivo_id: int = None,
    logo_reducido_archivo_id: int = None,
    favicon_archivo_id: int = None,
    portada_archivo_id: int = None,
    color_primario: str = None,
    color_secundario: str = None,
    color_acento: str = None,
    tipografia: str = None,
    sitio_web: str = None,
    facebook: str = None,
    instagram: str = None,
    tiktok: str = None,
    youtube: str = None,
    whatsapp: str = None,
    correo_publico: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> EmpresaIdentidad:
    """
    Updates company visual identity information.
    Validates that referenced file IDs belong to the company, exist, and are available.
    Captures old values, writes modifications, and logs history and audit records.
    """
    # 1. Fetch or create the EmpresaIdentidad record
    try:
        identidad = empresa.identidad
    except EmpresaIdentidad.DoesNotExist:
        identidad = EmpresaIdentidad(empresa=empresa, estado='BORRADOR')

    # 2. Validate file references
    file_fields = {
        "logo_archivo_id": logo_archivo_id,
        "logo_reducido_archivo_id": logo_reducido_archivo_id,
        "favicon_archivo_id": favicon_archivo_id,
        "portada_archivo_id": portada_archivo_id
    }
    
    for field_name, file_id in file_fields.items():
        if file_id is not None:
            if not validate_company_file_reference(file_id, empresa.id):
                raise ValidationError({
                    field_name: "El archivo seleccionado no existe, no pertenece a esta empresa o no está disponible."
                })

    # 3. Capture old values
    fields_to_track = [
        "nombre_publico", "descripcion_corta", "descripcion_larga",
        "logo_archivo_id", "logo_reducido_archivo_id", "favicon_archivo_id", "portada_archivo_id",
        "color_primario", "color_secundario", "color_acento", "tipografia",
        "sitio_web", "facebook", "instagram", "tiktok", "youtube", "whatsapp", "correo_publico"
    ]
    
    valores_anteriores = {field: getattr(identidad, field) for field in fields_to_track if hasattr(identidad, field)}

    # 4. Apply updates
    updates = {}
    
    # Text and other simple fields
    for field in fields_to_track:
        val = locals()[field]
        if val is not None and val != getattr(identidad, field):
            setattr(identidad, field, val)
            updates[field] = val

    # If no updates, return early
    if not updates:
        return identidad

    identidad.fecha_actualizacion = timezone.now()
    identidad.actualizado_por = actualizado_por

    # If it was in BORRADOR but now has name, we might want to check its state or keep it as is.
    # We respect model's allowed states.
    if nombre_publico and identidad.estado == 'BORRADOR':
        identidad.estado = 'ACTIVO'  # Mark active once filled or keep BORRADOR. Let's make it ACTIVO or default 'ACTIVO'.
        updates["estado"] = 'ACTIVO'

    try:
        with transaction.atomic(using='periodico_db'):
            identidad.save(using='periodico_db')

            # Write to EmpresaHistorial
            historial = EmpresaHistorial(
                empresa=empresa,
                tipo_evento='CAMBIO_IDENTIDAD',
                estado_anterior=empresa.estado,
                estado_nuevo=empresa.estado,
                motivo='Actualización de identidad visual',
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
                accion=AuditoriaAccion.IDENTIDAD_EMPRESA_ACTUALIZADA,
                entidad='EmpresaIdentidad',
                entidad_id=str(identidad.id),
                valores_anteriores={k: v for k, v in valores_anteriores.items() if k in updates},
                valores_nuevos=updates,
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Identidad visual de empresa actualizada',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return identidad
    except Exception as e:
        logger.error(f"Error updating company identity {empresa.id}: {str(e)}")
        raise ValidationError(f"No se pudo actualizar la identidad visual: {str(e)}")
