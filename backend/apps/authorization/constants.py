class EstadoEmpresa:
    PENDIENTE = 'PENDIENTE'
    ACTIVA = 'ACTIVA'
    SUSPENDIDA = 'SUSPENDIDA'
    INACTIVA = 'INACTIVA'

    CHOICES = (
        (PENDIENTE, 'Pendiente'),
        (ACTIVA, 'Activa'),
        (SUSPENDIDA, 'Suspendida'),
        (INACTIVA, 'Inactiva'),
    )


class EstadoUsuarioEmpresa:
    PENDIENTE = 'PENDIENTE'
    ACTIVO = 'ACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'
    FINALIZADO = 'FINALIZADO'

    CHOICES = (
        (PENDIENTE, 'Pendiente'),
        (ACTIVO, 'Activo'),
        (SUSPENDIDO, 'Suspendido'),
        (FINALIZADO, 'Finalizado'),
    )


class TipoRol:
    PLATAFORMA = 'PLATAFORMA'
    EMPRESA = 'EMPRESA'
    LECTOR = 'LECTOR'

    CHOICES = (
        (PLATAFORMA, 'Plataforma'),
        (EMPRESA, 'Empresa'),
        (LECTOR, 'Lector'),
    )


class EstadoRol:
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'

    CHOICES = (
        (ACTIVO, 'Activo'),
        (INACTIVO, 'Inactivo'),
    )


class EstadoUsuarioEmpresaRol:
    ACTIVO = 'ACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'
    FINALIZADO = 'FINALIZADO'

    CHOICES = (
        (ACTIVO, 'Activo'),
        (SUSPENDIDO, 'Suspendido'),
        (FINALIZADO, 'Finalizado'),
    )


class TipoPermisoDirecto:
    CONCEDER = 'CONCEDER'
    REVOCAR = 'REVOCAR'

    CHOICES = (
        (CONCEDER, 'Conceder'),
        (REVOCAR, 'Revocar'),
    )


class ModuloPermiso:
    M01 = 'M01'
    M02 = 'M02'
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

    CHOICES = tuple((f"M{str(i).zfill(2)}", f"Módulo {str(i).zfill(2)}") for i in range(1, 13))


class AccionPermiso:
    VER = 'VER'
    CREAR = 'CREAR'
    EDITAR = 'EDITAR'
    ELIMINAR = 'ELIMINAR'
    PUBLICAR = 'PUBLICAR'
    SUSPENDER = 'SUSPENDER'
    REACTIVAR = 'REACTIVAR'
    APROBAR = 'APROBAR'
    EXPORTAR = 'EXPORTAR'
    GESTIONAR = 'GESTIONAR'
    SUPERVISAR = 'SUPERVISAR'

    CHOICES = (
        (VER, 'Ver'),
        (CREAR, 'Crear'),
        (EDITAR, 'Editar'),
        (ELIMINAR, 'Eliminar'),
        (PUBLICAR, 'Publicar'),
        (SUSPENDER, 'Suspender'),
        (REACTIVAR, 'Reactivar'),
        (APROBAR, 'Aprobar'),
        (EXPORTAR, 'Exportar'),
        (GESTIONAR, 'Gestionar'),
        (SUPERVISAR, 'Supervisar'),
    )
