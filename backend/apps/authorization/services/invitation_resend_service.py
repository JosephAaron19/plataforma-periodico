import logging
import secrets
import hashlib
import redis
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.authorization.tasks import send_company_invitation_email_task
from apps.audit.models.auditoria import Auditoria
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

# Script Lua para liberar la reserva de forma atómica.
# Comprueba que la clave existe, que el contador es mayor que cero, y decrementa solo en ese caso,
# conservando el TTL actual y sin crear una clave nueva ni permitir valores negativos.
LUA_RELEASE_SCRIPT = """
local key = KEYS[1]
local current = redis.call('get', key)
if current then
    local val = tonumber(current)
    if val > 0 then
        return redis.call('decr', key)
    else
        return 0
    end
else
    return 0
end
"""

class RedisUnavailableException(Exception):
    pass

class RateLimitExceededException(Exception):
    def __init__(self, retry_after=None):
        self.retry_after = retry_after

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

    # 5. Cooldown checks using physical database fields
    now = timezone.now()
    if invitacion.fecha_envio and (now - invitacion.fecha_envio) < timedelta(seconds=60):
        raise ValidationError("Debe esperar al menos 60 segundos entre reenvíos.")

    # 5b. Redis rate limiting checks (max 5 resends in 24 hours en ventana fija, el TTL original no se reinicia)
    email_clean = invitacion.correo.strip().lower()
    email_hash = hashlib.sha256(email_clean.encode('utf-8')).hexdigest()
    redis_key = f"invitation:resend:{empresa_id}:{invitation_id}:{email_hash}"
    
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=3)
        r.ping()
    except Exception as re:
        logger.warning(f"Error de conexion con Redis al verificar rate limit de reenvio: {str(re)}")
        raise RedisUnavailableException("Servicio de rate limit no disponible.")

    # Atomic evaluation using Lua script to prevent race conditions.
    # Límite Redis en ventana fija de 24 horas iniciada con el primer reenvío, no ventana móvil.
    lua_script = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local ttl = tonumber(ARGV[2])
    
    local current = redis.call('get', key)
    if current then
        if tonumber(current) >= limit then
            return 0
        else
            return redis.call('incr', key)
        end
    else
        redis.call('set', key, 1)
        redis.call('expire', key, ttl)
        return 1
    end
    """
    
    try:
        # Limit is 5 resends, TTL is 24 hours (86400 seconds)
        eval_res = r.eval(lua_script, 1, redis_key, 5, 86400)
    except Exception as re:
        logger.warning(f"Error al ejecutar script Lua en Redis: {str(re)}")
        raise RedisUnavailableException("Servicio de rate limit no disponible.")
        
    if eval_res == 0:
        # Get remaining TTL to compute Retry-After
        try:
            ttl = r.ttl(redis_key)
            retry_after = max(0, ttl) if ttl > 0 else 86400
        except Exception:
            retry_after = 86400
        # Register limited resend event in Audit
        AuditService.record_event(
            usuario=solicitante,
            emp_id=empresa_id,
            modulo=AuditoriaModulo.M04,
            accion='REENVIO_VERIFICACION_LIMITADO',
            entidad='InvitacionUsuario',
            entidad_id=str(invitacion.id),
            valores_anteriores={"estado": invitacion.estado},
            valores_nuevos=None,
            resultado=AuditoriaResultado.RECHAZADO,
            motivo='Límite de 5 reenvíos en 24 horas superado',
            ip_address=ip_address,
            user_agent=user_agent,
            throw_on_error=False
        )
        raise RateLimitExceededException(retry_after=retry_after)

    # 6. Regenerate token
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()

    # 7. Update fields (physically updating fecha_envio to track the last sent timestamp)
    estado_anterior = invitacion.estado
    invitacion.token_hash = token_hash
    invitacion.fecha_expiracion = now + timedelta(hours=72)
    invitacion.fecha_envio = now
    invitacion.estado = 'REENVIADA'

    redis_reserved = True
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
                    "estado": estado_anterior
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
        # Liberar la reserva en Redis si falla la transacción PostgreSQL
        if redis_reserved:
            try:
                # Usar script Lua atómico para liberar la reserva de forma segura
                r.eval(LUA_RELEASE_SCRIPT, 1, redis_key)
            except Exception as re:
                logger.error(f"Error al liberar reserva de Redis tras fallo DB: {str(re)}")
        
        logger.error(f"Error resending invitation {invitation_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo reenviar la invitación: {str(e)}")
