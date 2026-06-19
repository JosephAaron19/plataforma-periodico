import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.models.rol_historial import RolHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def remove_direct_permission_exception(
    *,
    uep_id: int,
    emp_id: int,
    permission_code: str,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresaPermiso:
    """
    Retracts (removes) a direct permission concession or revocation exception.
    Instead of physical deletion, sets the status logically to inactive (estado=False, fecha_fin=now).
    Logs to RolHistorial and AuditService.
    """
    now = timezone.now()

    # 1. Resolve permission
    try:
        permiso = Permiso.objects.using('periodico_db').get(codigo=permission_code)
    except Permiso.DoesNotExist:
        raise ValidationError({"permission_code": "El permiso especificado no existe."})

    try:
        with transaction.atomic(using='periodico_db'):
            # 2. Retrieve and lock relationship
            try:
                uep = UsuarioEmpresa.objects.using('periodico_db').select_for_update().get(
                    id=uep_id,
                    empresa_id=emp_id
                )
            except UsuarioEmpresa.DoesNotExist:
                raise ValidationError("El miembro especificado no existe o no pertenece a la empresa.")

            # 3. Retrieve and lock active exception row
            try:
                uepr = UsuarioEmpresaPermiso.objects.using('periodico_db').select_for_update().get(
                    usuario_empresa=uep,
                    permiso=permiso,
                    estado=True
                )
            except UsuarioEmpresaPermiso.DoesNotExist:
                raise ValidationError("El miembro no tiene una excepción activa para este permiso.")

            # 4. Logical delete/inactivation
            tipo_anterior = uepr.tipo
            uepr.estado = False
            uepr.fecha_fin = now
            uepr.save(using='periodico_db')

            # 5. Log history
            historial = RolHistorial(
                usuario_empresa_id=uep_id,
                permiso=permiso,
                tipo_evento='REACTIVACION_PERMISO',
                valor_anterior={"tipo": tipo_anterior, "estado": True},
                valor_nuevo={"estado": False},
                motivo="Excepción directa de permiso retirada administrativamente.",
                realizado_por=solicitante,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 6. Audit event
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='EXCEPCION_PERMISO_RETIRADA',
                entidad='UsuarioEmpresaPermiso',
                entidad_id=str(uepr.id),
                valores_anteriores={"tipo": tipo_anterior, "estado": True},
                valores_nuevos={"estado": False},
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Excepción de permiso {permiso.codigo} retirada para el miembro {uep_id}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uepr

    except Exception as e:
        logger.error(f"Error removing permission exception {permission_code} for member {uep_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo retirar la excepción de permiso: {str(e)}")
