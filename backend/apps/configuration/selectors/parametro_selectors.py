import logging
from apps.configuration.models.parametro_sistema import ParametroSistema

logger = logging.getLogger(__name__)

def get_system_parameter_value(clave: str, fallback_value):
    """
    Safely retrieves the value of a system parameter by its key from the periodico_db connection.
    If the parameter does not exist, is inactive, or has an error,
    returns fallback_value and logs a generic warning.
    """
    try:
        param = ParametroSistema.objects.using('periodico_db').get(clave=clave, estado='ACTIVO')
        if param.tipo == 'NUMERO' and param.valor_numero is not None:
            return float(param.valor_numero)
        elif param.tipo == 'TEXTO' and param.valor_texto is not None:
            return param.valor_texto
        elif param.tipo == 'BOOLEANO' and param.valor_booleano is not None:
            return param.valor_booleano
        return fallback_value
    except Exception:
        logger.warning("Advertencia al recuperar parametro de configuracion. Usando valor por defecto.")
        return fallback_value
