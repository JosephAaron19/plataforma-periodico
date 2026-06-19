import logging
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.constants import EstadoUsuarioEmpresaRol
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def set_member_primary_role(
    *,
    uep_id: int,
    emp_id: int,
    uer_id: int,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresaRol:
    """
    Sets a specific active and current role as the member's primary role.
    Clears the primary flag from all other roles assigned to the member in that company.
    Locks the records using select_for_update to prevent race conditions.
    """
    now = timezone.now()

    try:
        with transaction.atomic(using='periodico_db'):
            # 1. Retrieve the target role and lock it
            try:
                uer = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().get(
                    id=uer_id,
                    usuario_empresa_id=uep_id,
                    usuario_empresa__empresa_id=emp_id
                )
            except UsuarioEmpresaRol.DoesNotExist:
                raise ValidationError("La asignación de rol especificada no existe para este miembro.")

            # 2. Check if the role is active and current
            is_active = (uer.estado == EstadoUsuarioEmpresaRol.ACTIVO)
            is_current = (uer.fecha_inicio <= now) and (uer.fecha_fin is None or uer.fecha_fin >= now)
            if not is_active or not is_current:
                raise ValidationError("El rol especificado debe estar activo y vigente para ser establecido como principal.")

            # Privilege escalation check for changing primary role
            from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
            from apps.authorization.models.rol_permiso import RolPermiso
            from apps.authorization.constants import EstadoRol
            
            if not is_platform_superadmin(solicitante):
                role_perms = set(
                    RolPermiso.objects.using('periodico_db').filter(
                        rol=uer.rol,
                        estado=True,
                        permiso__estado=EstadoRol.ACTIVO
                    ).values_list('permiso__codigo', flat=True)
                )
                requester_perms = calculate_effective_permissions(solicitante.id, emp_id)
                missing_perms = role_perms - requester_perms
                if missing_perms:
                    AuditService.record_event(
                        usuario=solicitante,
                        emp_id=emp_id,
                        modulo=AuditoriaModulo.M04,
                        accion='ESCALAMIENTO_PRIVILEGIOS_DENEGADO',
                        entidad='UsuarioEmpresaRol',
                        entidad_id=str(uer.id),
                        valores_anteriores=None,
                        valores_nuevos={"requested_role": uer.rol.codigo},
                        resultado=AuditoriaResultado.RECHAZADO,
                        motivo=f"Intento de cambiar rol principal a {uer.rol.codigo} que contiene permisos que el solicitante no posee.",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        throw_on_error=False
                    )
                    raise ValidationError("No puedes cambiar al miembro a un rol principal que contiene permisos que tú mismo no posees.")

            if uer.es_principal:
                # Already principal, nothing to do
                return uer

            # 3. Retrieve and lock all roles of this member to clear principal status safely
            all_member_roles = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().filter(
                usuario_empresa_id=uep_id
            )

            previous_principal_uer = None
            for member_uer in all_member_roles:
                if member_uer.es_principal:
                    previous_principal_uer = member_uer
                    member_uer.es_principal = False
                    member_uer.save(using='periodico_db')

            # 4. Set target as principal
            uer.es_principal = True
            uer.save(using='periodico_db')

            # 5. Log history
            historial = RolHistorial(
                usuario_empresa_id=uep_id,
                rol=uer.rol,
                tipo_evento='CAMBIO_ROL_PRINCIPAL',
                valor_anterior={
                    "rol_anterior_principal": previous_principal_uer.rol.codigo if previous_principal_uer else None,
                    "es_principal": False
                },
                valor_nuevo={
                    "rol_nuevo_principal": uer.rol.codigo,
                    "es_principal": True
                },
                motivo="Establecido administrativamente como rol principal",
                realizado_por=solicitante,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 6. Audit event
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='ROL_PRINCIPAL_CAMBIADO',
                entidad='UsuarioEmpresaRol',
                entidad_id=str(uer.id),
                valores_anteriores={
                    "rol_anterior_principal": previous_principal_uer.rol.codigo if previous_principal_uer else None,
                    "es_principal": False
                },
                valores_nuevos={
                    "rol_nuevo_principal": uer.rol.codigo,
                    "es_principal": True
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Rol principal cambiado a {uer.rol.codigo} para el miembro {uep_id}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uer

    except IntegrityError as e:
        logger.error(f"Error de integridad al establecer rol principal: {str(e)}")
        raise ValidationError(f"Error de integridad al establecer rol principal: {str(e)}")
    except Exception as e:
        logger.error(f"Error setting primary role assignment {uer_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo establecer el rol como principal: {str(e)}")
