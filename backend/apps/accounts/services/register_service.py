import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.services.token_service import generate_verification_token
from apps.accounts.services.email_service import send_verification_email
from apps.accounts.utils.log_utils import mask_email
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
import uuid

logger = logging.getLogger(__name__)

def register_user(
    *,
    email: str,
    password: str,
    nombres: str,
    apellidos: str = None,
    tipo_documento: str = None,
    numero_documento: str = None,
    telefono: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> Usuario:
    """
    Registers a new user, or handles existing accounts securely to prevent account enumeration.
    """
    # 1. Validation checks
    if not email:
        raise ValidationError({"email": "El correo electrónico es obligatorio"})
    if not password or len(password) < 8:
        raise ValidationError({"password": "La contraseña debe tener al menos 8 caracteres"})
    if not nombres:
        raise ValidationError({"nombres": "Los nombres son obligatorios"})
        
    normalized_email = email.strip().lower()
    masked = mask_email(normalized_email)
    
    # 2. Check for existing user in periodico_db
    existing_user = Usuario.objects.using('periodico_db').filter(usr_correo=normalized_email).first()
    
    if existing_user:
        # Policy for ACTIVO user: simulate success without sending mail or writing anything
        if existing_user.estado == EstadoUsuario.ACTIVO:
            logger.info(f"Registro solicitado para correo ACTIVO {masked}. Simulando respuesta exitosa.")
            return existing_user
            
        # Policy for PENDIENTE user: invalid prior tokens, generate new token and resend email
        if existing_user.estado == EstadoUsuario.PENDIENTE:
            logger.info(f"Registro solicitado para correo PENDIENTE {masked}. Regenerando token de verificación.")
            
            # Capture old values before they are modified in-place
            old_values = {
                'nombres': existing_user.nombres,
                'apellidos': existing_user.apellidos,
                'tipo_documento': existing_user.tipo_documento,
                'numero_documento': existing_user.numero_documento,
                'telefono': existing_user.telefono,
                'usr_estado': existing_user.estado,
                'usr_correo_verificado': existing_user.correo_verificado
            }
            
            with transaction.atomic(using='periodico_db'):
                # Reset details and password
                existing_user.nombres = nombres
                existing_user.apellidos = apellidos
                existing_user.tipo_documento = tipo_documento
                existing_user.numero_documento = numero_documento
                existing_user.telefono = telefono
                existing_user.set_password(password)
                existing_user.save(using='periodico_db')
                
                # Invalid prior pending verification tokens
                VerificacionCorreo.objects.using('periodico_db').filter(
                    usuario=existing_user,
                    estado=EstadoVerificacion.PENDIENTE
                ).update(
                    estado=EstadoVerificacion.INVALIDADA,
                    motivo_invalidacion="Re-registro o solicitud de nuevo enlace"
                )
                
                # Generate new token
                plain_token, hashed_token, expires_at = generate_verification_token()
                
                verification = VerificacionCorreo(
                    id=uuid.uuid4(),
                    usuario=existing_user,
                    token_hash=hashed_token,
                    fecha_expiracion=expires_at,
                    estado=EstadoVerificacion.PENDIENTE,
                    direccion_ip=ip_address,
                    intentos=0
                )
                verification.save(using='periodico_db')
                
                # Record audit log
                AuditService.record_event(
                    usuario=existing_user,
                    modulo=AuditoriaModulo.M02,
                    accion=AuditoriaAccion.REGISTRO_USUARIO,
                    entidad='usr_usuario',
                    entidad_id=str(existing_user.id),
                    valores_anteriores=old_values,
                    valores_nuevos={
                        'nombres': nombres,
                        'apellidos': apellidos,
                        'tipo_documento': tipo_documento,
                        'numero_documento': numero_documento,
                        'telefono': telefono,
                        'usr_estado': existing_user.estado,
                        'usr_correo_verificado': existing_user.correo_verificado,
                        're_registro': True
                    },
                    resultado=AuditoriaResultado.EXITOSO,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    proceso_origen="Registro Web"
                )
                
                # Schedule Celery task on commit of periodico_db transaction
                transaction.on_commit(
                    lambda: send_verification_email(
                        email=normalized_email,
                        nombres=nombres,
                        plain_token=plain_token
                    ),
                    using='periodico_db'
                )
                
            return existing_user

    # Check for Duplicate Document Number for NEW users to avoid DB integrity errors
    if numero_documento and Usuario.objects.using('periodico_db').filter(numero_documento=numero_documento).exists():
        raise ValidationError({"numero_documento": "El número de documento ya se encuentra registrado"})

    # 3. Create New User
    logger.info(f"Iniciando registro de nuevo usuario para {masked}")
    
    with transaction.atomic(using='periodico_db'):
        user = Usuario(
            usr_correo=normalized_email,
            nombres=nombres,
            apellidos=apellidos,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            telefono=telefono,
            estado=EstadoUsuario.PENDIENTE,
            correo_verificado=False
        )
        user.set_password(password)
        user.save(using='periodico_db')
        
        plain_token, hashed_token, expires_at = generate_verification_token()
        
        verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=user,
            token_hash=hashed_token,
            fecha_expiracion=expires_at,
            estado=EstadoVerificacion.PENDIENTE,
            direccion_ip=ip_address,
            intentos=0
        )
        verification.save(using='periodico_db')
        
        # Record audit log
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REGISTRO_USUARIO,
            entidad='usr_usuario',
            entidad_id=str(user.id),
            valores_anteriores=None,
            valores_nuevos={
                'usr_correo': normalized_email,
                'nombres': nombres,
                'apellidos': apellidos,
                'tipo_documento': tipo_documento,
                'numero_documento': numero_documento,
                'telefono': telefono,
                'usr_estado': EstadoUsuario.PENDIENTE,
                'usr_correo_verificado': False
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Registro Web"
        )
        
        # Schedule Celery task on commit
        transaction.on_commit(
            lambda: send_verification_email(
                email=user.usr_correo,
                nombres=user.nombres,
                plain_token=plain_token
            ),
            using='periodico_db'
        )
        
    return user
