from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class Edicion(models.Model):
    id = models.BigAutoField(db_column='edi_id', primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='ediciones'
    )
    codigo = models.CharField(db_column='edi_codigo', max_length=50)
    titulo = models.CharField(db_column='edi_titulo', max_length=250)
    slug = models.CharField(db_column='edi_slug', max_length=250)
    descripcion_corta = models.CharField(db_column='edi_descripcion_corta', max_length=500, null=True, blank=True)
    descripcion_larga = models.TextField(db_column='edi_descripcion_larga', null=True, blank=True)
    fecha_edicion = models.DateField(db_column='edi_fecha_edicion')
    fecha_publicacion = models.DateTimeField(db_column='edi_fecha_publicacion', null=True, blank=True)
    modalidad = models.CharField(db_column='edi_modalidad', max_length=20, default='PAGO')
    precio = models.DecimalField(db_column='edi_precio', max_digits=12, decimal_places=2, default=0.00)
    moneda = models.CharField(db_column='edi_moneda', max_length=3, default='PEN')
    numero_paginas = models.IntegerField(db_column='edi_numero_paginas', null=True, blank=True)
    es_destacada = models.BooleanField(db_column='edi_es_destacada', default=False)
    permite_compra = models.BooleanField(db_column='edi_permite_compra', default=True)
    permite_muestra = models.BooleanField(db_column='edi_permite_muestra', default=False)
    paginas_muestra = models.IntegerField(db_column='edi_paginas_muestra', null=True, blank=True)
    estado = models.CharField(db_column='edi_estado', max_length=30, default='BORRADOR')
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='edi_creado_por',
        related_name='ediciones_creadas'
    )
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='edi_actualizado_por',
        related_name='ediciones_actualizadas',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(db_column='edi_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='edi_fecha_actualizacion', null=True, blank=True)
    eliminado = models.BooleanField(db_column='edi_eliminado', default=False)
    fecha_eliminacion = models.DateTimeField(db_column='edi_fecha_eliminacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"edi_edicion'

    def __str__(self):
        return f"Edicion {self.id}: {self.titulo} ({self.estado})"
