from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.processing.models.procesamiento_intento import ProcesamientoIntento

class ProcesamientoError(models.Model):
    id = models.BigAutoField(db_column='pre_id', primary_key=True)
    intento = models.ForeignKey(
        ProcesamientoIntento,
        on_delete=models.DO_NOTHING,
        db_column='pri_id',
        related_name='errores'
    )
    pre_codigo = models.CharField(db_column='pre_codigo', max_length=100)
    pre_categoria = models.CharField(db_column='pre_categoria', max_length=50)
    pre_mensaje_usuario = models.CharField(db_column='pre_mensaje_usuario', max_length=500, null=True, blank=True)
    pre_mensaje_tecnico = models.TextField(db_column='pre_mensaje_tecnico', null=True, blank=True)
    pre_numero_pagina = models.IntegerField(db_column='pre_numero_pagina', null=True, blank=True)
    pre_reintentable = models.BooleanField(db_column='pre_reintentable', default=False)
    pre_severidad = models.CharField(db_column='pre_severidad', max_length=20, default='ERROR')
    pre_contexto = models.JSONField(db_column='pre_contexto', null=True, blank=True)
    pre_fecha = models.DateTimeField(db_column='pre_fecha', auto_now_add=True)
    pre_resuelto = models.BooleanField(db_column='pre_resuelto', default=False)
    pre_fecha_resolucion = models.DateTimeField(db_column='pre_fecha_resolucion', null=True, blank=True)
    pre_resuelto_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='pre_resuelto_por',
        null=True,
        blank=True,
        related_name='errores_resueltos'
    )
    pre_observacion_resolucion = models.CharField(db_column='pre_observacion_resolucion', max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"pre_procesamiento_error'

    def __str__(self):
        return f"Error {self.pre_codigo} (Intento {self.intento_id})"
