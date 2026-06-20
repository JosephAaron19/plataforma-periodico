from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.files.models.archivo import Archivo

class SeoMetadato(models.Model):
    id = models.BigAutoField(db_column='seo_id', primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        null=True,
        blank=True,
        related_name='metadatos_seo'
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        null=True,
        blank=True,
        related_name='metadatos_seo'
    )
    archivo = models.ForeignKey(
        Archivo,
        on_delete=models.DO_NOTHING,
        db_column='arc_id',
        null=True,
        blank=True,
        related_name='metadatos_seo'
    )
    tipo_entity = models.CharField(db_column='seo_tipo_entidad', max_length=20)
    titulo = models.CharField(db_column='seo_titulo', max_length=200)
    descripcion = models.CharField(db_column='seo_descripcion', max_length=500, null=True, blank=True)
    palabras_clave = models.CharField(db_column='seo_palabras_clave', max_length=500, null=True, blank=True)
    slug = models.CharField(db_column='seo_slug', max_length=250)
    url_canonica = models.CharField(db_column='seo_url_canonica', max_length=500, null=True, blank=True)
    og_titulo = models.CharField(db_column='seo_og_titulo', max_length=200, null=True, blank=True)
    og_descripcion = models.CharField(db_column='seo_og_descripcion', max_length=500, null=True, blank=True)
    og_tipo = models.CharField(db_column='seo_og_tipo', max_length=50, default='website')
    indexable = models.BooleanField(db_column='seo_indexable', default=True)
    seguir_enlaces = models.BooleanField(db_column='seo_seguir_enlaces', default=True)
    estado = models.CharField(db_column='seo_estado', max_length=20, default='ACTIVO')
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='seo_creado_por',
        related_name='seo_creados'
    )
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='seo_actualizado_por',
        related_name='seo_actualizados',
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(db_column='seo_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='seo_fecha_actualizacion', null=True, blank=True)
    con_id = models.BigIntegerField(db_column='con_id', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"seo_metadato'

    def __str__(self):
        return f"SeoMetadato {self.id}: {self.tipo_entity} - {self.titulo}"
