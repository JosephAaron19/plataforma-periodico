from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion

class EdicionHistorial(models.Model):
    id = models.BigAutoField(db_column='ehi_id', primary_key=True)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='historiales'
    )
    tipo_evento = models.CharField(db_column='ehi_tipo_evento', max_length=50)
    estado_anterior = models.CharField(db_column='ehi_estado_anterior', max_length=30, null=True, blank=True)
    estado_nuevo = models.CharField(db_column='ehi_estado_nuevo', max_length=30, null=True, blank=True)
    valores_anteriores = models.JSONField(db_column='ehi_valores_anteriores', null=True, blank=True)
    valores_nuevos = models.JSONField(db_column='ehi_valores_nuevos', null=True, blank=True)
    motivo = models.CharField(db_column='ehi_motivo', max_length=500, null=True, blank=True)
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='ehi_realizado_por',
        null=True,
        blank=True,
        related_name='historiales_edicion'
    )
    proceso_origen = models.CharField(db_column='ehi_proceso_origen', max_length=100, null=True, blank=True)
    fecha = models.DateTimeField(db_column='ehi_fecha', auto_now_add=True)
    direccion_ip = models.GenericIPAddressField(db_column='ehi_direccion_ip', null=True, blank=True)
    resultado = models.CharField(db_column='ehi_resultado', max_length=20, default='EXITOSO')

    class Meta:
        managed = False
        db_table = 'pdg\".\"ehi_edicion_historial'

    def __str__(self):
        return f"EdicionHistorial {self.id}: Edicion {self.edicion_id} - Evento {self.tipo_evento} ({self.resultado})"
