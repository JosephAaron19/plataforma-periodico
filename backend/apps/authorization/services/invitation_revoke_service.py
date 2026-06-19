import logging
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def revoke_company_invitation(
    *,
    invitation_id: str,
    empresa_id: int,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> InvitacionUsuario:
    """
    Revokes a pending or resent company invitation.
    Marks its state as 'REVOCADA' and logs the audit event.
    """
    # 1. Check permissions of solicitor
    if not is_platform_superadmin(solicitante):
        perms = calculate_effective_permissions(solicitante.id, empresa_id)
        if 'USUARIO_GESTIONAR' not in perms:
            raise ValidationError("No tienes permisos (USUARIO_GESTIONAR) para gestionar invitaciones.")

    # 2. Retrieve invitation
    try:
        invitacion = InvitacionUsuario.objects.using('periodico_db').get(
            id=invitation_id,
            empresa_id=empresa_id
        )
    except InvitacionUsuario.DoesNotExist:
        raise ValidationError("La invitación especificada no existe.")

    # 3. Check current state - can only revoke pending or resent
    if invitacion.estado not in ['PENDIENTE', 'REENVIADA']:
        raise ValidationError(f"No se puede revocar una invitación en estado '{invitacion.estado}'.")

    # 4. Perform update
    estado_anterior = invitacion.estado
    invitacion.estado = 'REVOCADA'

    try:
        with transaction.atomic(using='periodico_db'):
            invitacion.save(using='periodico_db')

            # Log audit record
            AuditService.record_event(
                usuario=solicitante,
                emp_id=empresa_id,
                modulo=AuditoriaModulo.M04,
                accion='INVITACION_REVOCADA',
                entidad='InvitacionUsuario',
                entidad_id=str(invitacion.id),
                valores_anteriores={
                    "estado": estado_anterior
                },
                valores_nuevos={
                    "estado": "REVOCADA"
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Invitación revocada exitosamente',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return invitacion

    except Exception as e:
        logger.error(f"Error revoking invitation {invitation_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo revocar la invitación: {str(e)}")
