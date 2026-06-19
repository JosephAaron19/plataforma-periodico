from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.authorization.models.rol import Rol
from apps.authorization.models.permiso import Permiso

class RolPermiso(models.Model):
    id = models.BigAutoField(db_column='rpe_id', primary_key=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.DO_NOTHING,
        db_column='rol_id',
        related_name='permisos_rol'
    )
    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.DO_NOTHING,
        db_column='per_id',
        related_name='roles_permiso'
    )
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='rpe_asignado_por',
        related_name='permisos_rol_asignados',
        null=True,
        blank=True
    )
    fecha_asignacion = models.DateTimeField(db_column='rpe_fecha_asignacion', auto_now_add=True)
    estado = models.BooleanField(db_column='rpe_estado', default=True)

    class Meta:
        managed = False
        db_table = 'pdg"."rpe_rol_permiso'
        unique_together = (('rol', 'permiso'),)

    def __str__(self):
        return f"RolPermiso: Rol {self.rol_id} - Permiso {self.permiso_id} ({self.estado})"
