import logging
import secrets
import hashlib
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.authorization.tasks import send_company_invitation_email_task
from apps.audit.models.auditoria import Auditoria
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def resend_company_invitation(
    *,
    invitation_id: str,
    empresa_id: int,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> InvitacionUsuario:
    """
    Resends a pending company invitation if rate limits allow.
    Invalidates the previous token, extends expiration by 72 hours, 
    and dispatches a new invitation email.
    """
    # 1. Check permission of solicitor
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

    # 3. Check current state - only pending/resent can be resent
    if invitacion.estado not in ['PENDIENTE', 'REENVIADA']:
        raise ValidationError(f"No se puede reenviar una invitación en estado '{invitacion.estado}'.")

    # 4. Check if invitation has been accepted
    if invitacion.fecha_aceptacion is not None:
        raise ValidationError("La invitación ya ha sido aceptada.")

    # 5. Rate limiting checks via audit logs
    now = timezone.now()
    
    # 5a. Minimum 60 seconds interval
    recent_send = Auditoria.objects.using('periodico_db').filter(
        entidad='InvitacionUsuario',
        entidad_id=str(invitacion.id),
        accion__in=['INVITACION_CREADA', 'INVITACION_REENVIADA'],
        resultado='EXITOSO',
        fecha__gte=now - timedelta(seconds=60)
    ).exists()
    
    if recent_send:
        raise ValidationError("Debe esperar al menos 60 segundos entre reenvíos.")

    # 5b. Maximum 5 resends in 24 hours
    daily_resends = Auditoria.objects.using('periodico_db').filter(
        entidad='InvitacionUsuario',
        entidad_id=str(invitacion.id),
        accion='INVITACION_REENVIADA',
        resultado='EXITOSO',
        fecha__gte=now - timedelta(hours=24)
    ).count()

    if daily_resends >= 5:
        raise ValidationError("Se ha superado el límite de 5 reenvíos en 24 horas para esta invitación.")

    # 6. Regenerate token
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()

    # 7. Update fields
    invitacion.token_hash = token_hash
    invitacion.fecha_expiracion = now + timedelta(hours=72)
    invitacion.estado = 'REENVIADA'

    try:
        with transaction.atomic(using='periodico_db'):
            invitacion.save(using='periodico_db')

            # Log audit record
            AuditService.record_event(
                usuario=solicitante,
                emp_id=empresa_id,
                modulo=AuditoriaModulo.M04,
                accion='INVITACION_REENVIADA',
                entidad='InvitacionUsuario',
                entidad_id=str(invitacion.id),
                valores_anteriores={
                    "estado": invitacion.estado
                },
                valores_nuevos={
                    "estado": "REENVIADA",
                    "fecha_expiracion": str(invitacion.fecha_expiracion)
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Invitación reenviada exitosamente',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

            # Enqueue the Celery email task on transaction commit
            transaction.on_commit(
                lambda: send_company_invitation_email_task.delay(str(invitacion.id), plain_token),
                using='periodico_db'
            )

        return invitacion

    except Exception as e:
        logger.error(f"Error resending invitation {invitation_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo reenviar la invitación: {str(e)}")
