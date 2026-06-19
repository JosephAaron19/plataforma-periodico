import logging
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.audit.models.auditoria import Auditoria

logger = logging.getLogger(__name__)

def sanitize_dict(d: dict) -> dict:
    """
    Recursively redacts sensitive keys in the given dictionary.
    Guarantees no mutation of the original object by returning a new dictionary.
    Case-insensitive, covers nested lists and dictionaries, and matches partial/sub-keys.
    """
    if not isinstance(d, dict):
        return d
    
    redacted_keys = {
        'password', 'password_confirmation', 'token', 'access', 'refresh', 
        'usr_clave_hash', 'ver_token_hash', 'authorization', 'cookie',
        'access_token', 'refresh_token'
    }
    
    def matches_sensitive(key: str) -> bool:
        if not isinstance(key, str):
            return False
        k_lower = key.lower()
        if k_lower in redacted_keys:
            return True
        for red in {'password', 'token', 'auth', 'cookie'}:
            if red in k_lower:
                return True
        return False

    sanitized = {}
    for k, v in d.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_dict(item) if isinstance(item, dict) else item for item in v]
        elif matches_sensitive(k):
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
        Saves under an independent savepoint to prevent aborting active transactions.
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
            
            try:
                with transaction.atomic(using='periodico_db', savepoint=True):
                    audit_log.save(using='periodico_db')
            except Exception as save_err:
                raise save_err
                
            return audit_log
            
        except Exception as e:
            logger.error(
                f"Error al registrar evento de auditoria (Modulo: {modulo}, Accion: {accion}, Resultado: {resultado}): {str(e)}",
                exc_info=True
            )
            if throw_on_error:
                raise e
            return None
