from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.processing.models.procesamiento import Procesamiento

class ProcesamientoIntento(models.Model):
    id = models.BigAutoField(db_column='pri_id', primary_key=True)
    procesamiento = models.ForeignKey(
        Procesamiento,
        on_delete=models.DO_NOTHING,
        db_column='pro_id',
        related_name='intentos'
    )
    pri_numero_intento = models.IntegerField(db_column='pri_numero_intento')
    pri_estado = models.CharField(db_column='pri_estado', max_length=30, default='CREADO')
    pri_worker_id = models.CharField(db_column='pri_worker_id', max_length=150, null=True, blank=True)
    pri_tarea_externa_id = models.CharField(db_column='pri_tarea_externa_id', max_length=200, null=True, blank=True)
    pri_fecha_encolado = models.DateTimeField(db_column='pri_fecha_encolado', null=True, blank=True)
    pri_fecha_inicio = models.DateTimeField(db_column='pri_fecha_inicio', null=True, blank=True)
    pri_fecha_fin = models.DateTimeField(db_column='pri_fecha_fin', null=True, blank=True)
    pri_duracion_segundos = models.IntegerField(db_column='pri_duracion_segundos', null=True, blank=True)
    pri_paginas_generadas = models.IntegerField(db_column='pri_paginas_generadas', default=0)
    pri_pico_memoria_mb = models.IntegerField(db_column='pri_pico_memoria_mb', null=True, blank=True)
    pri_resultado = models.CharField(db_column='pri_resultado', max_length=30, null=True, blank=True)
    pri_reintentable = models.BooleanField(db_column='pri_reintentable', default=False)
    pri_motivo_reintento = models.CharField(db_column='pri_motivo_reintento', max_length=500, null=True, blank=True)
    pri_solicitado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='pri_solicitado_por',
        null=True,
        blank=True,
        related_name='intentos_solicitados'
    )
    pri_fecha_creacion = models.DateTimeField(db_column='pri_fecha_creacion', auto_now_add=True)
    edi_id = models.BigIntegerField(db_column='edi_id')

    class Meta:
        managed = False
        db_table = 'pdg\".\"pri_procesamiento_intento'
        unique_together = (('procesamiento', 'pri_numero_intento'),)

    def __str__(self):
        return f"Intento {self.pri_numero_intento} (Proceso {self.procesamiento_id})"
