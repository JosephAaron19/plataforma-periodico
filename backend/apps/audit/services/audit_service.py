import logging
from django.core.exceptions import ValidationError
from apps.audit.models.auditoria import Auditoria

logger = logging.getLogger(__name__)

def sanitize_dict(d: dict) -> dict:
    """
    Recursively redacts sensitive keys in the given dictionary.
    """
    if not isinstance(d, dict):
        return d
    
    redacted_keys = {
        'password', 'password_confirmation', 'token', 'access', 'refresh', 
        'usr_clave_hash', 'ver_token_hash', 'authorization', 'cookie'
    }
    
    sanitized = {}
    for k, v in d.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_dict(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(k, str) and k.lower() in redacted_keys:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return sanitized

def truncate_value(val: str, max_len: int) -> str:
    if not val:
        return val
    val_str = str(val)
    if len(val_str) > max_len:
        logger.warning(f"Auditoria: truncando campo de longitud {len(val_str)} a {max_len}")
        return val_str[:max_len]
    return val_str

class AuditService:
    @staticmethod
    def record_event(
        *,
        usuario=None,
        emp_id=None,
        modulo: str,
        accion: str,
        entidad: str,
        entidad_id: str = None,
        valores_anteriores: dict = None,
        valores_nuevos: dict = None,
        resultado: str,
        motivo: str = None,
        ip_address: str = None,
        user_agent: str = None,
        proceso_origen: str = None,
        throw_on_error: bool = False
    ) -> Auditoria:
        """
        Validates, sanitizes, and records an audit log to pdg.aud_auditoria.
        Handles errors gracefully to prevent breaking transaction-critical paths unless throw_on_error is True.
        """
        try:
            # Python-side constraint checks to avoid triggering DB integrity errors that break transactions
            # 1. ck_aud_origen
            if not usuario and not proceso_origen:
                raise ValidationError("La auditoria requiere al menos un usuario (usr_id) o un proceso de origen (proceso_origen).")
            
            # 2. ck_aud_modulo
            allowed_modulos = {f"M{str(i).zfill(2)}" for i in range(1, 13)}
            if modulo not in allowed_modulos:
                raise ValidationError(f"Modulo '{modulo}' invalido. Debe estar entre M01 y M12.")
                
            # 3. ck_aud_resultado
            allowed_resultados = {'EXITOSO', 'RECHAZADO', 'ERROR'}
            if resultado not in allowed_resultados:
                raise ValidationError(f"Resultado '{resultado}' invalido. Debe ser EXITOSO, RECHAZADO o ERROR.")
                
            # Truncations
            modulo = truncate_value(modulo, 10)
            accion = truncate_value(accion, 100)
            entidad = truncate_value(entidad, 120)
            entidad_id = truncate_value(entidad_id, 100)
            resultado = truncate_value(resultado, 20)
            motivo = truncate_value(motivo, 500)
            proceso_origen = truncate_value(proceso_origen, 100)
            
            # Sanitization
            sanit_anteriores = sanitize_dict(valores_anteriores) if valores_anteriores is not None else None
            sanit_nuevos = sanitize_dict(valores_nuevos) if valores_nuevos is not None else None
            
            # Save inside database
            audit_log = Auditoria(
                usuario=usuario,
                emp_id=emp_id,
                modulo=modulo,
                accion=accion,
                entidad=entidad,
                entidad_id=entidad_id,
                valores_anteriores=sanit_anteriores,
                valores_nuevos=sanit_nuevos,
                resultado=resultado,
                motivo=motivo,
                direccion_ip=ip_address,
                agente_usuario=user_agent,
                proceso_origen=proceso_origen
            )
            audit_log.save(using='periodico_db')
            return audit_log
            
        except Exception as e:
            logger.error(
                f"Error al registrar evento de auditoria (Modulo: {modulo}, Accion: {accion}, Resultado: {resultado}): {str(e)}",
                exc_info=True
            )
            if throw_on_error:
                raise e
            return None
