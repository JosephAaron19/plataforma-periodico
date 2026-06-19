from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class UsuarioEmpresa(models.Model):
    id = models.BigAutoField(db_column='uep_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='usuario_empresas'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='usuario_empresas'
    )
    es_principal = models.BooleanField(db_column='uep_es_principal', default=False)
    fecha_asignacion = models.DateTimeField(db_column='uep_fecha_asignacion', auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(db_column='uep_fecha_finalizacion', null=True, blank=True)
    estado = models.CharField(db_column='uep_estado', max_length=20, default='PENDIENTE')
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='uep_asignado_por',
        related_name='asignaciones_realizadas'
    )
    motivo = models.CharField(db_column='uep_motivo', max_length=300, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(db_column='uep_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."uep_usuario_empresa'
        unique_together = (('usuario', 'empresa'),)

    def __str__(self):
        return f"Relación Usuario: {self.usuario_id} - Empresa: {self.empresa_id} ({self.estado})"
