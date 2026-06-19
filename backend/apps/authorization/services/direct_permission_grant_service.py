import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.constants import TipoPermisoDirecto, EstadoUsuarioEmpresa
from apps.authorization.selectors.permission_management_selectors import PLATFORM_EXCLUSIVE_PERMISSIONS
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def grant_direct_permission(
    *,
    uep_id: int,
    emp_id: int,
    permission_code: str,
    motivo: str,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresaPermiso:
    """
    Grants a direct permission to a company member (concesión directa exception).
    Includes platform-exclusive checks and requester privilege escalation checks.
    Logs to RolHistorial and AuditService.
    """
    if not motivo:
        raise ValidationError({"motivo": "El motivo de la concesión es requerido."})

    now = timezone.now()

    # 1. Resolve permission
    try:
        permiso = Permiso.objects.using('periodico_db').get(codigo=permission_code)
    except Permiso.DoesNotExist:
        raise ValidationError({"permission_code": "El permiso especificado no existe."})

    if permiso.estado != 'ACTIVO':
        raise ValidationError({"permission_code": "El permiso especificado se encuentra inactivo."})

    if permission_code in PLATFORM_EXCLUSIVE_PERMISSIONS:
        raise ValidationError({"permission_code": "No se pueden conceder permisos exclusivos de la plataforma a nivel empresarial."})

    # 2. Privilege escalation check
    if not is_platform_superadmin(solicitante):
        requester_perms = calculate_effective_permissions(solicitante.id, emp_id)
        if permission_code not in requester_perms:
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='ESCALAMIENTO_PRIVILEGIOS_DENEGADO',
                entidad='UsuarioEmpresaPermiso',
                entidad_id=None,
                valores_anteriores=None,
                valores_nuevos={"requested_permission": permission_code},
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Intento del miembro de conceder permiso {permission_code} que no posee.",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )
            raise ValidationError({"permission_code": "No puedes conceder un permiso que tú mismo no posees."})

    try:
        with transaction.atomic(using='periodico_db'):
            # 3. Retrieve target member and lock it
            try:
                uep = UsuarioEmpresa.objects.using('periodico_db').select_for_update().get(
                    id=uep_id,
                    empresa_id=emp_id
                )
            except UsuarioEmpresa.DoesNotExist:
                raise ValidationError("El miembro especificado no existe o no pertenece a la empresa.")

            if uep.estado != EstadoUsuarioEmpresa.ACTIVO:
                raise ValidationError(f"El miembro se encuentra en estado '{uep.estado}', no se le pueden asignar excepciones directas.")

            # 4. Check for existing direct permission exception row
            existing_uepr = UsuarioEmpresaPermiso.objects.using('periodico_db').select_for_update().filter(
                usuario_empresa=uep,
                permiso=permiso
            ).first()

            if existing_uepr:
                is_active = existing_uepr.estado
                is_concession = (existing_uepr.tipo == TipoPermisoDirecto.CONCEDER)
                is_current = (existing_uepr.fecha_inicio <= now) and (existing_uepr.fecha_fin is None or existing_uepr.fecha_fin >= now)
                
                if is_active and is_concession and is_current:
                    raise ValidationError("El miembro ya posee este permiso concedido directamente.")
                
                # Reactivate/update existing exception row
                valores_anteriores = {"tipo": existing_uepr.tipo, "estado": existing_uepr.estado}
                
                uepr = existing_uepr
                uepr.tipo = TipoPermisoDirecto.CONCEDER
                uepr.motivo = motivo
                uepr.asignado_por = solicitante
                uepr.estado = True
                uepr.fecha_inicio = now
                uepr.fecha_fin = None
            else:
                valores_anteriores = None
                uepr = UsuarioEmpresaPermiso(
                    usuario_empresa=uep,
                    permiso=permiso,
                    tipo=TipoPermisoDirecto.CONCEDER,
                    motivo=motivo,
                    asignado_por=solicitante,
                    estado=True,
                    fecha_inicio=now,
                    fecha_fin=None
                )

            uepr.save(using='periodico_db')

            # 5. Log history
            historial = RolHistorial(
                usuario_empresa_id=uep_id,
                permiso=permiso,
                tipo_evento='CONCESION_PERMISO',
                valor_anterior=valores_anteriores,
                valor_nuevo={"tipo": "CONCEDER", "estado": True},
                motivo=motivo,
                realizado_por=solicitante,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 6. Audit event
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='PERMISO_DIRECTO_CONCEDIDO',
                entidad='UsuarioEmpresaPermiso',
                entidad_id=str(uepr.id),
                valores_anteriores=valores_anteriores,
                valores_nuevos={"tipo": "CONCEDER", "permiso": permiso.codigo},
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Permiso {permiso.codigo} concedido al miembro {uep_id}. Motivo: {motivo}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uepr

    except Exception as e:
        logger.error(f"Error granting permission {permission_code} to member {uep_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo conceder el permiso: {str(e)}")
