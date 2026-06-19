from django.db import models
from apps.accounts.models.usuario import Usuario

class Plan(models.Model):
    id = models.BigAutoField(db_column='pla_id', primary_key=True)
    codigo = models.CharField(db_column='pla_codigo', max_length=50, unique=True)
    nombre = models.CharField(db_column='pla_nombre', max_length=120, unique=True)
    descripcion = models.TextField(db_column='pla_descripcion', null=True, blank=True)
    precio = models.DecimalField(db_column='pla_precio', max_digits=12, decimal_places=2, default=0.00)
    moneda = models.CharField(db_column='pla_moneda', max_length=3, default='PEN')
    periodicidad = models.CharField(db_column='pla_periodicidad', max_length=20)
    limite_usuarios = models.IntegerField(db_column='pla_limite_usuarios', null=True, blank=True)
    limite_ediciones_mes = models.IntegerField(db_column='pla_limite_ediciones_mes', null=True, blank=True)
    limite_storage_mb = models.BigIntegerField(db_column='pla_limite_storage_mb', null=True, blank=True)
    limite_pdf_mb = models.IntegerField(db_column='pla_limite_pdf_mb', null=True, blank=True)
    limite_paginas_pdf = models.IntegerField(db_column='pla_limite_paginas_pdf', null=True, blank=True)
    es_publico = models.BooleanField(db_column='pla_es_publico', default=True)
    orden = models.IntegerField(db_column='pla_orden', default=0)
    estado = models.CharField(db_column='pla_estado', max_length=20, default='ACTIVO')
    fecha_creacion = models.DateTimeField(db_column='pla_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='pla_fecha_actualizacion', null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='pla_creado_por',
        related_name='planes_creados',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'pdg"."pla_plan'

    def __str__(self):
        return f"Plan: {self.nombre} [{self.codigo}]"
