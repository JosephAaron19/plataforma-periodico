import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.services.token_service import generate_verification_token
from apps.accounts.services.email_service import send_verification_email
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
    ip_address: str = None
) -> Usuario:
    """
    Registers a new user, creates their email verification record, and triggers the async email task.
    """
    # 1. Input Sanitization & Normalization
    if not email:
        raise ValidationError({"email": "El correo electrónico es obligatorio"})
    if not password or len(password) < 8:
        raise ValidationError({"password": "La contraseña debe tener al menos 8 caracteres"})
    if not nombres:
        raise ValidationError({"nombres": "Los nombres son obligatorios"})
        
    normalized_email = email.strip().lower()
    
    # 2. Check for Duplicate Emails
    if Usuario.objects.filter(usr_correo=normalized_email).exists():
        raise ValidationError({"email": "El correo electrónico ya se encuentra registrado"})
        
    # Check for Duplicate Document Number if provided
    if numero_documento and Usuario.objects.filter(numero_documento=numero_documento).exists():
        raise ValidationError({"numero_documento": "El número de documento ya se encuentra registrado"})

    # 3. Create User and Verification Record in a Transaction
    logger.info(f"Iniciando registro de usuario para {normalized_email}")
    
    with transaction.atomic(using='periodico_db'):
        # Instantiate Usuario (managed = False)
        # Note: password hash is set via set_password or managers
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
        
        # Generate verification token
        plain_token, hashed_token, expires_at = generate_verification_token()
        
        # Instantiate and save VerificacionCorreo record
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
        
        logger.info(f"Usuario {user.id} y verificación creados exitosamente")

    # 4. Trigger Async Verification Email outside of the atomic transaction block
    send_verification_email(
        email=user.usr_correo,
        nombres=user.nombres,
        plain_token=plain_token
    )
    
    return user
