import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def update_company(
    *,
    empresa: Empresa,
    actualizado_por: Usuario,
    razon_social: str = None,
    nombre_comercial: str = None,
    descripcion: str = None,
    correo: str = None,
    telefono: str = None,
    direccion: str = None,
    sitio_web: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> Empresa:
    """
    Updates general mutable information of a company.
    Captures old values, saves modifications, and logs history and audit records.
    """
    # 1. Capture old values before any modifications
    valores_anteriores = {
        "razon_social": empresa.razon_social,
        "nombre_comercial": empresa.nombre_comercial,
        "descripcion": empresa.descripcion,
        "correo": empresa.correo,
        "telefono": empresa.telefono,
        "direccion": empresa.direccion,
        "sitio_web": empresa.sitio_web,
    }

    # 2. Track updates
    updates = {}
    if razon_social is not None and razon_social != empresa.razon_social:
        empresa.razon_social = razon_social
        updates["razon_social"] = razon_social
    if nombre_comercial is not None and nombre_comercial != empresa.nombre_comercial:
        empresa.nombre_comercial = nombre_comercial
        updates["nombre_comercial"] = nombre_comercial
    if descripcion is not None and descripcion != empresa.descripcion:
        empresa.descripcion = descripcion
        updates["descripcion"] = descripcion
    if correo is not None and correo != empresa.correo:
        empresa.correo = correo
        updates["correo"] = correo
    if telefono is not None and telefono != empresa.telefono:
        empresa.telefono = telefono
        updates["telefono"] = telefono
    if direccion is not None and direccion != empresa.direccion:
        empresa.direccion = direccion
        updates["direccion"] = direccion
    if sitio_web is not None and sitio_web != empresa.sitio_web:
        empresa.sitio_web = sitio_web
        updates["sitio_web"] = sitio_web

    # If nothing changed, return early
    if not updates:
        return empresa

    empresa.fecha_actualizacion = timezone.now()

    try:
        with transaction.atomic(using='periodico_db'):
            empresa.save(using='periodico_db')

            # Create EmpresaHistorial entry
            historial = EmpresaHistorial(
                empresa=empresa,
                tipo_evento='CAMBIO_DATOS',
                estado_anterior=empresa.estado,
                estado_nuevo=empresa.estado,
                motivo='Actualización de información general',
                detalle_anterior={k: v for k, v in valores_anteriores.items() if k in updates},
                detalle_nuevo=updates,
                realizado_por=actualizado_por,
                direccion_ip=ip_address,
                resultado='EXITOSO'
            )
            historial.save(using='periodico_db')

            # Record event via AuditService under savepoint (graceful failure)
            AuditService.record_event(
                usuario=actualizado_por,
                emp_id=empresa.id,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.EMPRESA_ACTUALIZADA,
                entidad='Empresa',
                entidad_id=str(empresa.id),
                valores_anteriores={k: v for k, v in valores_anteriores.items() if k in updates},
                valores_nuevos=updates,
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Información general actualizada',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return empresa
    except Exception as e:
        logger.error(f"Error updating company {empresa.id}: {str(e)}")
        raise ValidationError(f"No se pudo actualizar la empresa: {str(e)}")
