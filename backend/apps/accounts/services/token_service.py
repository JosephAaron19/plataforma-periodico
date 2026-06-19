import uuid
import hashlib
from django.utils import timezone
from datetime import timedelta
from apps.configuration.selectors.parametro_selectors import get_system_parameter_value

def generate_verification_token() -> tuple[str, str, timezone.datetime]:
    """
    Generates a secure, non-predictable plain token, its SHA256 hash, and the dynamic configuration expiration datetime.
    Returns:
        (plain_token, hashed_token, expires_at)
    """
    plain_token = uuid.uuid4().hex
    hashed_token = hash_token(plain_token)
    hours = get_system_parameter_value('VIGENCIA_VERIFICACION_CORREO_HORAS', 24)
    expires_at = timezone.now() + timedelta(hours=hours)
    return plain_token, hashed_token, expires_at

def hash_token(plain_token: str) -> str:
    """
    Computes a SHA256 hash of the plain token to be safely stored in the database.
    """
    if not plain_token:
        raise ValueError("El token no puede estar vacío")
    return hashlib.sha256(plain_token.encode('utf-8')).hexdigest()
