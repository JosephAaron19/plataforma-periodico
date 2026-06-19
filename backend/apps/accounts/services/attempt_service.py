import logging
from django.utils import timezone
from apps.accounts.models.intento_acceso import IntentoAcceso
from apps.accounts.models.usuario import Usuario

logger = logging.getLogger(__name__)

def record_login_attempt(
    *,
    user: Usuario = None,
    email_entered: str = None,
    resultado: str,
    motivo: str = None,
    bloqueo_generado: bool = False,
    ip_address: str = None,
    user_agent: str = None
) -> IntentoAcceso:
    """
    Saves an entry in pdg.ina_intento_acceso for security auditing.
    """
    if email_entered:
        email_entered = email_entered[:150]
    if motivo:
        motivo = motivo[:150]
    resultado = resultado[:30]

    attempt = IntentoAcceso(
        usuario=user,
        correo_ingresado=email_entered,
        direccion_ip=ip_address,
        agente_usuario=user_agent,
        resultado=resultado,
        motivo=motivo,
        bloqueo_generado=bloqueo_generado
    )
    attempt.save(using='periodico_db')
    return attempt
