import logging
import hashlib
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.accounts.services.password_service import hash_password
from apps.companies.models.empresa import Empresa
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.authorization.models.rol_historial import RolHistorial
from apps.notifications.models.notificacion import Notificacion
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
from apps.plans.services.plan_limit_service import check_user_limit

logger = logging.getLogger(__name__)

def accept_company_invitation(
    *,
    plain_token: str,
    password: str = None,
    nombres: str = None,
    apellidos: str = None,
    logged_in_user: Usuario = None,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresa:
    """
    Accepts a company invitation using the plain token.
    Runs inside a transaction with select_for_update for concurrency safety.
    """
    if not plain_token:
        raise ValidationError({"token": "El token de invitación es requerido."})

    # 1. Compute SHA-256 hash of the plain token
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()

    try:
        with transaction.atomic(using='periodico_db'):
            # Lock invitation record using select_for_update to handle race conditions
            try:
                invitacion = InvitacionUsuario.objects.using('periodico_db').select_for_update().get(
                    token_hash=token_hash
                )
            except InvitacionUsuario.DoesNotExist:
                # Anti-enumeration/Generic security error
                raise ValidationError("El token de invitación es inválido, ha expirado o ya fue procesado.")

            # 2. Check current state and expiration
            if invitacion.estado not in ['PENDIENTE', 'REENVIADA']:
                raise ValidationError("La invitación ya ha sido aceptada, rechazada o revocada.")
                
            if invitacion.fecha_expiracion < timezone.now():
                invitacion.estado = 'VENCIDA'
                invitacion.save(using='periodico_db')
                raise ValidationError("El token de invitación ha expirado.")

            email_clean = invitacion.correo.strip().lower()

            # 3. Resolve or create user
            user = Usuario.objects.using('periodico_db').filter(
                usr_correo=email_clean,
                eliminado=False
            ).first()

            is_new_user = False
            if user:
                # Existing user checks: must be active, authenticated, matching email, and not passing password
                if (user.estado != 'ACTIVO' or 
                    not logged_in_user or 
                    logged_in_user.usr_correo.strip().lower() != email_clean or 
                    password is not None):
                    raise ValidationError("El token de invitación es inválido, ha expirado o ya fue procesado.")
                user = logged_in_user
            else:
                # New user creation - password, nombres and apellidos required
                if not password:
                    raise ValidationError({"password": "La contraseña es requerida para el registro del nuevo usuario."})
                if not nombres:
                    raise ValidationError({"nombres": "Los nombres son requeridos."})
                
                # Validate password strength using existing validators
                from django.contrib.auth.password_validation import validate_password
                temp_user = Usuario(usr_correo=email_clean, nombres=nombres, apellidos=apellidos)
                try:
                    validate_password(password, temp_user)
                except ValidationError as e:
                    raise ValidationError({"password": list(e.messages)})
                
                is_new_user = True
                user = Usuario(
                    usr_correo=email_clean,
                    nombres=nombres,
                    apellidos=apellidos,
                    password=hash_password(password),
                    estado='ACTIVO',
                    correo_verificado=True
                )
                user.save(using='periodico_db')
                
                # Create profile when corresponding
                from apps.accounts.models.perfil import Perfil
                perfil = Perfil(usuario=user, idioma='es')
                perfil.save(using='periodico_db')
                
                # Link user to invitation instance
                invitacion.usuario = user

            # 4. Check for existing active relationship to prevent duplicate links
            active_rel = UsuarioEmpresa.objects.using('periodico_db').filter(
                usuario=user,
                empresa=invitacion.empresa,
                estado='ACTIVO'
            ).exists()
            if active_rel:
                raise ValidationError("Ya eres un miembro activo de esta empresa.")

            # Check user limit for the company plan
            uep_exists = UsuarioEmpresa.objects.using('periodico_db').filter(
                usuario=user,
                empresa=invitacion.empresa,
                estado__in=['ACTIVO', 'PENDIENTE', 'SUSPENDIDO']
            ).exists()
            if not uep_exists:
                limit_result = check_user_limit(invitacion.empresa)
                if not limit_result["allowed"]:
                    raise ValidationError(limit_result["message"])

            # 5. Create or reactivate UsuarioEmpresa relationship
            uep = UsuarioEmpresa.objects.using('periodico_db').filter(
                usuario=user,
                empresa=invitacion.empresa
            ).first()

            if uep:
                # Reactivate existing physical relationship to respect UNIQUE constraint
                uep.estado = 'ACTIVO'
                uep.es_principal = True
                uep.asignado_por = invitacion.invitado_por
                uep.motivo = 'Invitación aceptada'
                uep.fecha_actualizacion = timezone.now()
                uep.save(using='periodico_db')
            else:
                uep = UsuarioEmpresa(
                    usuario=user,
                    empresa=invitacion.empresa,
                    es_principal=True,
                    estado='ACTIVO',
                    asignado_por=invitacion.invitado_por,
                    motivo='Invitación aceptada'
                )
                uep.save(using='periodico_db')

            # 6. Create or reactivate UsuarioEmpresaRol relationship
            uer = UsuarioEmpresaRol.objects.using('periodico_db').filter(
                usuario_empresa=uep,
                rol=invitacion.rol
            ).first()

            if uer:
                uer.estado = 'ACTIVO'
                uer.es_principal = True
                uer.asignado_por = invitacion.invitado_por
                uer.fecha_inicio = timezone.now()
                uer.fecha_fin = None
                uer.save(using='periodico_db')
            else:
                uer = UsuarioEmpresaRol(
                    usuario_empresa=uep,
                    rol=invitacion.rol,
                    es_principal=True,
                    asignado_por=invitacion.invitado_por,
                    estado='ACTIVO'
                )
                uer.save(using='periodico_db')

            # 7. Update invitation status
            invitacion.estado = 'ACEPTADA'
            invitacion.fecha_aceptacion = timezone.now()
            invitacion.save(using='periodico_db')

            # 8. Create RolHistorial entry
            historial = RolHistorial(
                usuario_empresa=uep,
                rol=invitacion.rol,
                tipo_evento='ASIGNACION_ROL',
                motivo='Asignación de rol inicial al aceptar la invitación',
                realizado_por=invitacion.invitado_por,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 11. Create Notificacion entry (tolerant creation after commit)
            def send_system_notification():
                try:
                    notif = Notificacion(
                        usuario=user,
                        empresa=invitacion.empresa,
                        tipo='SEGURIDAD',
                        titulo='Invitación Aceptada',
                        mensaje=f'Te has unido exitosamente a la empresa {invitacion.empresa.nombre_comercial} con el rol de {invitacion.rol.nombre}.',
                        estado='PENDIENTE'
                    )
                    notif.save(using='periodico_db')
                except Exception as ne:
                    logger.warning(f"Error secundario al crear la notificación del sistema tras commit: {str(ne)}")

            transaction.on_commit(send_system_notification, using='periodico_db')

            # 10. Audit event logging (under savepoint/safe failure)
            AuditService.record_event(
                usuario=user,
                emp_id=invitacion.empresa.id,
                modulo=AuditoriaModulo.M04,
                accion='INVITACION_ACEPTADA',
                entidad='InvitacionUsuario',
                entidad_id=str(invitacion.id),
                valores_anteriores={"estado": "PENDIENTE"},
                valores_nuevos={"estado": "ACEPTADA"},
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Invitación aceptada exitosamente',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )
            
            AuditService.record_event(
                usuario=user,
                emp_id=invitacion.empresa.id,
                modulo=AuditoriaModulo.M04,
                accion='USUARIO_VINCULADO_EMPRESA',
                entidad='UsuarioEmpresa',
                entidad_id=str(uep.id),
                valores_anteriores=None,
                valores_nuevos={"estado": "ACTIVO", "rol": invitacion.rol.codigo},
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Usuario vinculado a empresa tras aceptar invitación',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uep

    except IntegrityError as ie:
        logger.error(f"IntegrityError accepting invitation with token_hash {token_hash}: {str(ie)}")
        raise ValidationError("No se pudo procesar la aceptación debido a un conflicto de duplicados.")
    except Exception as e:
        logger.error(f"Error accepting invitation: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Error al aceptar la invitación: {str(e)}")
