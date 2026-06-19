from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class Archivo(models.Model):
    id = models.BigAutoField(db_column='arc_id', primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='archivos',
        null=True,
        blank=True
    )
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='arc_creado_por',
        related_name='archivos_creados',
        null=True,
        blank=True
    )
    nombre_original = models.CharField(db_column='arc_nombre_original', max_length=250)
    nombre_interno = models.CharField(db_column='arc_nombre_interno', max_length=250)
    extension = models.CharField(db_column='arc_extension', max_length=10)
    tipo_mime = models.CharField(db_column='arc_tipo_mime', max_length=100)
    tamano_bytes = models.BigIntegerField(db_column='arc_tamano_bytes')
    hash_sha256 = models.CharField(db_column='arc_hash_sha256', max_length=64)
    ruta_storage = models.CharField(db_column='arc_ruta_storage', max_length=500)
    proveedor_storage = models.CharField(db_column='arc_proveedor_storage', max_length=50)
    contenedor = models.CharField(db_column='arc_contenedor', max_length=100)
    es_publico = models.BooleanField(db_column='arc_es_publico', default=False)
    version = models.IntegerField(db_column='arc_version', default=1)
    estado = models.CharField(db_column='arc_estado', max_length=20, default='CARGANDO')
    fecha_creacion = models.DateTimeField(db_column='arc_fecha_creacion', auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(db_column='arc_fecha_eliminacion', null=True, blank=True)
    eliminado = models.BooleanField(db_column='arc_eliminado', default=False)

    class Meta:
        managed = False
        db_table = 'pdg"."arc_archivo'

    def __str__(self):
        return f"Archivo {self.id}: {self.nombre_original} ({self.estado})"
