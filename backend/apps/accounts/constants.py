class EstadoUsuario:
    PENDIENTE = 'PENDIENTE'
    ACTIVO = 'ACTIVO'
    BLOQUEADO = 'BLOQUEADO'
    SUSPENDIDO = 'SUSPENDIDO'
    INACTIVO = 'INACTIVO'

    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (ACTIVO, 'Activo'),
        (BLOQUEADO, 'Bloqueado'),
        (SUSPENDIDO, 'Suspendido'),
        (INACTIVO, 'Inactivo'),
    ]

class EstadoSesion:
    ACTIVA = 'ACTIVA'
    VENCIDA = 'VENCIDA'
    CERRADA = 'CERRADA'
    REVOCADA = 'REVOCADA'
    BLOQUEADA = 'BLOQUEADA'

    CHOICES = [
        (ACTIVA, 'Activa'),
        (VENCIDA, 'Vencida'),
        (CERRADA, 'Cerrada'),
        (REVOCADA, 'Revocada'),
        (BLOQUEADA, 'Bloqueada'),
    ]

class EstadoRecuperacion:
    SOLICITADA = 'SOLICITADA'
    ENVIADA = 'ENVIADA'
    UTILIZADA = 'UTILIZADA'
    VENCIDA = 'VENCIDA'
    INVALIDADA = 'INVALIDADA'

    CHOICES = [
        (SOLICITADA, 'Solicitada'),
        (ENVIADA, 'Enviada'),
        (UTILIZADA, 'Utilizada'),
        (VENCIDA, 'Vencida'),
        (INVALIDADA, 'Invalidada'),
    ]

class ResultadoIntentoAcceso:
    EXITOSO = 'EXITOSO'
    CREDENCIALES_INVALIDAS = 'CREDENCIALES_INVALIDAS'
    USUARIO_INACTIVO = 'USUARIO_INACTIVO'
    USUARIO_BLOQUEADO = 'USUARIO_BLOQUEADO'
    EMPRESA_INACTIVA = 'EMPRESA_INACTIVA'
    ERROR = 'ERROR'

    CHOICES = [
        (EXITOSO, 'Exitoso'),
        (CREDENCIALES_INVALIDAS, 'Credenciales Inválidas'),
        (USUARIO_INACTIVO, 'Usuario Inactivo'),
        (USUARIO_BLOQUEADO, 'Usuario Bloqueado'),
        (EMPRESA_INACTIVA, 'Empresa Inactiva'),
        (ERROR, 'Error'),
    ]

class EstadoVerificacion:
    PENDIENTE = 'PENDIENTE'
    ENVIADA = 'ENVIADA'
    VERIFICADA = 'VERIFICADA'
    VENCIDA = 'VENCIDA'
    INVALIDADA = 'INVALIDADA'

    CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (ENVIADA, 'Enviada'),
        (VERIFICADA, 'Verificada'),
        (VENCIDA, 'Vencida'),
        (INVALIDADA, 'Invalidada'),
    ]
