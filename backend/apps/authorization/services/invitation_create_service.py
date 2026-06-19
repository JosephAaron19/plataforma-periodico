import logging
import secrets
import hashlib
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.rol import Rol
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.authorization.tasks import send_company_invitation_email_task
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def create_company_invitation(
    *,
    empresa_id: int,
    email: str,
    role_code: str,
    invitado_por: Usuario,
    mensaje: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> InvitacionUsuario:
    """
    Creates a new company user invitation.
    Validates permissions, active company status, user uniqueness, role bounds, 
    and enqueues the email dispatch Celery task after commit.
    """
    # 1. Normalize email
    if not email:
        raise ValidationError({"email": "El correo electrónico es requerido."})
    email_clean = email.strip().lower()

    # 2. Check permissions of requester
    if not is_platform_superadmin(invitado_por):
        perms = calculate_effective_permissions(invitado_por.id, empresa_id)
        if 'USUARIO_GESTIONAR' not in perms:
            raise ValidationError("No tienes permisos (USUARIO_GESTIONAR) para invitar usuarios a esta empresa.")

    # 3. Resolve active company
    try:
        empresa = Empresa.objects.using('periodico_db').get(id=empresa_id, eliminado=False)
    except Empresa.DoesNotExist:
        raise ValidationError("La empresa especificada no existe.")
    
    if empresa.estado != 'ACTIVA':
        raise ValidationError("No se pueden enviar invitaciones para una empresa que no está activa.")

    # 4. Resolve and validate the target role
    try:
        rol = Rol.objects.using('periodico_db').get(codigo=role_code, estado='ACTIVO')
    except Rol.DoesNotExist:
        raise ValidationError({"role_code": f"El rol '{role_code}' no existe o no está activo."})

    if rol.tipo != 'EMPRESA':
        raise ValidationError({"role_code": "Solo se pueden asignar roles de tipo empresarial por invitación."})
        
    if rol.codigo == 'SUPERADMIN':
        raise ValidationError({"role_code": "No se puede invitar usuarios con el rol SUPERADMIN."})

    # 5. Check if user is already an active member of this company
    already_member = UsuarioEmpresa.objects.using('periodico_db').filter(
        empresa_id=empresa_id,
        usuario__usr_correo=email_clean,
        estado='ACTIVO'
    ).exists()
    if already_member:
        raise ValidationError({"email": "El usuario ya es un miembro activo de esta empresa."})

    # 6. Check if an active pending/resent invitation already exists
    pending_exists = InvitacionUsuario.objects.using('periodico_db').filter(
        empresa_id=empresa_id,
        correo=email_clean,
        estado__in=['PENDIENTE', 'REENVIADA'],
        fecha_expiracion__gt=timezone.now()
    ).exists()
    if pending_exists:
        raise ValidationError({"email": "Ya existe una invitación vigente para este correo en esta empresa."})

    # 7. Generate secure token
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()
    
    # 8. Setup expiration date (defaulting to 72 hours)
    fecha_expiracion = timezone.now() + timedelta(hours=72)

    # Resolve target user if they already exist in system
    target_user = Usuario.objects.using('periodico_db').filter(
        usr_correo=email_clean,
        eliminado=False
    ).first()

    try:
        with transaction.atomic(using='periodico_db'):
            invitacion = InvitacionUsuario(
                empresa=empresa,
                usuario=target_user,
                rol=rol,
                correo=email_clean,
                token_hash=token_hash,
                invitado_por=invitado_por,
                fecha_expiracion=fecha_expiracion,
                estado='PENDIENTE',
                mensaje=mensaje
            )
            invitacion.save(using='periodico_db')

            # Log audit record
            AuditService.record_event(
                usuario=invitado_por,
                emp_id=empresa_id,
                modulo=AuditoriaModulo.M04,
                accion=AuditoriaAccion.INVITACION_CREADA if not hasattr(AuditoriaAccion, 'INVITACION_CREADA') else 'INVITACION_CREADA',
                entidad='InvitacionUsuario',
                entidad_id=str(invitacion.id),
                valores_anteriores=None,
                valores_nuevos={
                    "correo": email_clean,
                    "rol": rol.codigo,
                    "fecha_expiracion": str(fecha_expiracion)
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Invitación creada exitosamente',
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
        logger.error(f"Error creating company invitation to {email_clean}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo crear la invitación: {str(e)}")
