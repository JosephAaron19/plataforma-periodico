from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.permiso import Permiso

class UsuarioEmpresaPermiso(models.Model):
    id = models.BigAutoField(db_column='uepr_id', primary_key=True)
    usuario_empresa = models.ForeignKey(
        UsuarioEmpresa,
        on_delete=models.DO_NOTHING,
        db_column='uep_id',
        related_name='permisos_directos'
    )
    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.DO_NOTHING,
        db_column='per_id',
        related_name='usuarios_directos'
    )
    tipo = models.CharField(db_column='uepr_tipo', max_length=20)  # CONCEDER or REVOCAR
    motivo = models.CharField(db_column='uepr_motivo', max_length=500)
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='uepr_asignado_por',
        related_name='permisos_directos_asignados'
    )
    fecha_inicio = models.DateTimeField(db_column='uepr_fecha_inicio', auto_now_add=True)
    fecha_fin = models.DateTimeField(db_column='uepr_fecha_fin', null=True, blank=True)
    estado = models.BooleanField(db_column='uepr_estado', default=True)

    class Meta:
        managed = False
        db_table = 'pdg"."uepr_usuario_empresa_permiso'
        unique_together = (('usuario_empresa', 'permiso'),)

    def __str__(self):
        return f"PermisoDirecto: Relacion {self.usuario_empresa_id} - Permiso {self.permiso_id} ({self.tipo})"
