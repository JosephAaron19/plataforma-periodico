from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.rol import Rol

class UsuarioEmpresaRol(models.Model):
    id = models.BigAutoField(db_column='uer_id', primary_key=True)
    usuario_empresa = models.ForeignKey(
        UsuarioEmpresa,
        on_delete=models.DO_NOTHING,
        db_column='uep_id',
        related_name='roles_asignados'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.DO_NOTHING,
        db_column='rol_id',
        related_name='usuario_empresas'
    )
    es_principal = models.BooleanField(db_column='uer_es_principal', default=False)
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='uer_asignado_por',
        related_name='roles_asignados_por_mi'
    )
    fecha_inicio = models.DateTimeField(db_column='uer_fecha_inicio', auto_now_add=True)
    fecha_fin = models.DateTimeField(db_column='uer_fecha_fin', null=True, blank=True)
    estado = models.CharField(db_column='uer_estado', max_length=20, default='ACTIVO')

    class Meta:
        managed = False
        db_table = 'pdg"."uer_usuario_empresa_rol'
        unique_together = (('usuario_empresa', 'rol'),)

    def __str__(self):
        return f"Asignación Rol: {self.rol_id} en Relación: {self.usuario_empresa_id} ({self.estado})"
