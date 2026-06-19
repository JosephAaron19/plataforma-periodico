from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo

class Procesamiento(models.Model):
    id = models.BigAutoField(db_column='pro_id', primary_key=True)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='procesamientos'
    )
    archivo_edicion = models.ForeignKey(
        EdicionArchivo,
        on_delete=models.DO_NOTHING,
        db_column='eda_id',
        null=True,
        blank=True,
        related_name='procesamientos'
    )
    version = models.IntegerField(db_column='pro_version', default=1)
    estado = models.CharField(db_column='pro_estado', max_length=30, default='PENDIENTE')
    total_paginas_esperadas = models.IntegerField(db_column='pro_total_paginas_esperadas', null=True, blank=True)
    total_paginas_generadas = models.IntegerField(db_column='pro_total_paginas_generadas', default=0)
    porcentaje_avance = models.DecimalField(db_column='pro_porcentaje_avance', max_digits=5, decimal_places=2, default=0.00)
    prioridad = models.IntegerField(db_column='pro_prioridad', default=5)
    solicitado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='pro_solicitado_por',
        related_name='procesamientos_solicitados'
    )
    fecha_solicitud = models.DateTimeField(db_column='pro_fecha_solicitud', auto_now_add=True)
    fecha_inicio = models.DateTimeField(db_column='pro_fecha_inicio', null=True, blank=True)
    fecha_fin = models.DateTimeField(db_column='pro_fecha_fin', null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(db_column='pro_fecha_cancelacion', null=True, blank=True)
    motivo_cancelacion = models.CharField(db_column='pro_motivo_cancelacion', max_length=500, null=True, blank=True)
    es_actual = models.BooleanField(db_column='pro_es_actual', default=True)
    resultado_resumen = models.CharField(db_column='pro_resultado_resumen', max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"pro_procesamiento'

    def __str__(self):
        return f"Procesamiento {self.id}: Edicion {self.edicion_id} ({self.estado})"
