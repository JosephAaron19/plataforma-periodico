import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def reactivate_company_member(
    *,
    uep_id: int,
    empresa_id: int,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresa:
    """
    Reactivates a suspended company member relationship.
    Restores the member relationship and their associated roles back to 'ACTIVO'.
    """
    # 1. Check permissions of requester
    if not is_platform_superadmin(solicitante):
        perms = calculate_effective_permissions(solicitante.id, empresa_id)
        if 'USUARIO_GESTIONAR' not in perms:
            raise ValidationError("No tienes permisos (USUARIO_GESTIONAR) para gestionar miembros.")

    try:
        with transaction.atomic(using='periodico_db'):
            # 2. Retrieve relationship with select_for_update inside the transaction
            try:
                uep = UsuarioEmpresa.objects.using('periodico_db').select_for_update().get(
                    id=uep_id,
                    empresa_id=empresa_id
                )
            except UsuarioEmpresa.DoesNotExist:
                raise ValidationError("La relación miembro-empresa especificada no existe.")

            if uep.estado != 'SUSPENDIDO':
                raise ValidationError(f"La relación se encuentra en estado '{uep.estado}', no se puede reactivar.")

            # Save previous state
            estado_anterior = uep.estado
            now = timezone.now()
            
            # Reactivate uep state
            uep.estado = 'ACTIVO'
            uep.motivo = 'Reactivación de miembro'
            uep.fecha_actualizacion = now
            uep.save(using='periodico_db')

            # Reactivate suspended roles of this relation that are still active (not expired)
            from django.db.models import Q
            suspended_roles = UsuarioEmpresaRol.objects.using('periodico_db').filter(
                usuario_empresa=uep,
                estado='SUSPENDIDO'
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)
            )
            
            for uer in suspended_roles:
                uer.estado = 'ACTIVO'
                uer.save(using='periodico_db')

                # Log role reactivation to RolHistorial
                historial = RolHistorial(
                    usuario_empresa=uep,
                    rol=uer.rol,
                    tipo_evento='ASIGNACION_ROL',
                    motivo="Rol reactivado junto con la relación miembro",
                    realizado_por=solicitante,
                    direccion_ip=ip_address
                )
                historial.save(using='periodico_db')

            # Log audit record
            AuditService.record_event(
                usuario=solicitante,
                emp_id=empresa_id,
                modulo=AuditoriaModulo.M04,
                accion='MIEMBRO_REACTIVADO',
                entidad='UsuarioEmpresa',
                entidad_id=str(uep.id),
                valores_anteriores={
                    "estado": estado_anterior
                },
                valores_nuevos={
                    "estado": "ACTIVO"
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Miembro reactivado exitosamente',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uep

    except Exception as e:
        logger.error(f"Error reactivating member relationship {uep_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo reactivar al miembro: {str(e)}")
