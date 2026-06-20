from django.db import models
from apps.editions.models.edicion import Edicion
from apps.processing.models.procesamiento_intento import ProcesamientoIntento
from apps.files.models.archivo import Archivo

class EdicionPagina(models.Model):
    id = models.BigAutoField(db_column='edp_id', primary_key=True)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='paginas'
    )
    intento = models.ForeignKey(
        ProcesamientoIntento,
        on_delete=models.DO_NOTHING,
        db_column='pri_id',
        related_name='paginas'
    )
    archivo = models.ForeignKey(
        Archivo,
        on_delete=models.DO_NOTHING,
        db_column='arc_id',
        related_name='paginas_edicion'
    )
    edp_numero_pagina = models.IntegerField(db_column='edp_numero_pagina')
    edp_ancho_px = models.IntegerField(db_column='edp_ancho_px', null=True, blank=True)
    edp_alto_px = models.IntegerField(db_column='edp_alto_px', null=True, blank=True)
    edp_tamano_bytes = models.BigIntegerField(db_column='edp_tamano_bytes', null=True, blank=True)
    edp_hash_sha256 = models.CharField(db_column='edp_hash_sha256', max_length=64, null=True, blank=True)
    edp_es_muestra = models.BooleanField(db_column='edp_es_muestra', default=False)
    edp_es_actual = models.BooleanField(db_column='edp_es_actual', default=True)
    edp_estado = models.CharField(db_column='edp_estado', max_length=20, default='GENERADA')
    edp_fecha_generacion = models.DateTimeField(db_column='edp_fecha_generacion', auto_now_add=True)
    edp_fecha_invalidacion = models.DateTimeField(db_column='edp_fecha_invalidacion', null=True, blank=True)
    edp_motivo_invalidacion = models.CharField(db_column='edp_motivo_invalidacion', max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"edp_edicion_pagina'

    def __str__(self):
        return f"Pagina {self.edp_numero_pagina} (Edicion {self.edicion_id})"
