class AuditoriaModulo:
    M01 = 'M01'
    M02 = 'M02'  # accounts / auth
    M03 = 'M03'
    M04 = 'M04'
    M05 = 'M05'
    M06 = 'M06'
    M07 = 'M07'
    M08 = 'M08'
    M09 = 'M09'
    M10 = 'M10'
    M11 = 'M11'
    M12 = 'M12'

    CHOICES = [
        (M01, 'M01'),
        (M02, 'M02'),
        (M03, 'M03'),
        (M04, 'M04'),
        (M05, 'M05'),
        (M06, 'M06'),
        (M07, 'M07'),
        (M08, 'M08'),
        (M09, 'M09'),
        (M10, 'M10'),
        (M11, 'M11'),
        (M12, 'M12'),
    ]


class AuditoriaResultado:
    EXITOSO = 'EXITOSO'
    RECHAZADO = 'RECHAZADO'
    ERROR = 'ERROR'

    CHOICES = [
        (EXITOSO, 'EXITOSO'),
        (RECHAZADO, 'RECHAZADO'),
        (ERROR, 'ERROR'),
    ]


class AuditoriaAccion:
    REGISTRO_USUARIO = 'REGISTRO_USUARIO'
    VERIFICACION_CORREO_EXITOSA = 'VERIFICACION_CORREO_EXITOSA'
    VERIFICACION_CORREO_FALLIDA = 'VERIFICACION_CORREO_FALLIDA'
    TOKEN_VERIFICACION_VENCIDO = 'TOKEN_VERIFICACION_VENCIDO'
    TOKEN_VERIFICACION_REUTILIZADO = 'TOKEN_VERIFICACION_REUTILIZADO'
