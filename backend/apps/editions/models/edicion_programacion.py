from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion

class EdicionProgramacion(models.Model):
    id = models.BigAutoField(db_column='epr_id', primary_key=True)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='programaciones'
    )
    fecha_programada = models.DateTimeField(db_column='epr_fecha_programada')
    zona_horaria = models.CharField(db_column='epr_zona_horaria', max_length=50, default='America/Lima')
    estado = models.CharField(db_column='epr_estado', max_length=20, default='PENDIENTE')
    programado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='epr_programado_por',
        related_name='programaciones_creadas'
    )
    fecha_creacion = models.DateTimeField(db_column='epr_fecha_creacion', auto_now_add=True)
    fecha_ejecucion = models.DateTimeField(db_column='epr_fecha_ejecucion', null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(db_column='epr_fecha_cancelacion', null=True, blank=True)
    cancelado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='epr_cancelado_por',
        null=True,
        blank=True,
        related_name='programaciones_canceladas'
    )
    motivo_cancelacion = models.CharField(db_column='epr_motivo_cancelacion', max_length=500, null=True, blank=True)
    resultado = models.CharField(db_column='epr_resultado', max_length=30, null=True, blank=True)
    detalle_error = models.TextField(db_column='epr_detalle_error', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"epr_edicion_programacion'

    def __str__(self):
        return f"EdicionProgramacion {self.id}: Edicion {self.edicion_id} @ {self.fecha_programada} ({self.estado})"
