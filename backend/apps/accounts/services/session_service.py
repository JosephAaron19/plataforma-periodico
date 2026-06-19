import logging
import uuid
import hashlib
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models.sesion import Sesion
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoSesion
from apps.configuration.selectors.parametro_selectors import get_system_parameter_value

logger = logging.getLogger(__name__)

def hash_refresh_token(token_str: str) -> str:
    """
    Computes a SHA256 hash of the refresh token.
    """
    if not token_str:
        raise ValueError("El token no puede estar vacío")
    return hashlib.sha256(token_str.encode('utf-8')).hexdigest()

def extract_device_and_os(user_agent: str) -> tuple[str, str]:
    if not user_agent:
        return "Unknown", "Unknown"
    
    ua = user_agent.lower()
    os_name = "Unknown"
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"

    device_name = "Desktop"
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_name = "Mobile"
    elif "ipad" in ua or "tablet" in ua:
        device_name = "Tablet"
        
    return device_name, os_name

def create_user_session(
    *,
    user: Usuario,
    plain_refresh_token: str,
    ip_address: str = None,
    user_agent: str = None
) -> Sesion:
    """
    Creates a new session record in pdg.ses_sesion.
    """
    session_id = uuid.uuid4()
    token_hash = hash_refresh_token(plain_refresh_token)
    
    # Read duration from par_parametro_sistema or fallback to 120 minutes
    duration_min = get_system_parameter_value('DURACION_SESION_MINUTOS', 120)
    expires_at = timezone.now() + timedelta(minutes=float(duration_min))
    
    device, os_name = extract_device_and_os(user_agent)
    
    session = Sesion(
        id=session_id,
        usuario=user,
        token_hash=token_hash,
        direccion_ip=ip_address,
        agente_usuario=user_agent,
        dispositivo=device[:150] if device else None,
        sistema_operativo=os_name[:100] if os_name else None,
        fecha_expiracion=expires_at,
        estado=EstadoSesion.ACTIVA
    )
    session.save(using='periodico_db')
    return session

def revoke_user_session(
    *,
    session: Sesion,
    motivo: str
) -> None:
    """
    Marks a session as REVOCADA or CERRADA.
    """
    session.estado = EstadoSesion.REVOCADA
    session.fecha_cierre = timezone.now()
    session.motivo_cierre = motivo[:100]
    session.save(using='periodico_db')
