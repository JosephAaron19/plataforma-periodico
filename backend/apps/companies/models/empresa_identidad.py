from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class EmpresaIdentidad(models.Model):
    id = models.BigAutoField(db_column='evi_id', primary_key=True)
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='identidad'
    )
    nombre_publico = models.CharField(db_column='evi_nombre_publico', max_length=180)
    descripcion_corta = models.CharField(db_column='evi_descripcion_corta', max_length=300, null=True, blank=True)
    descripcion_larga = models.TextField(db_column='evi_descripcion_larga', null=True, blank=True)
    logo_archivo_id = models.BigIntegerField(db_column='evi_logo_archivo_id', null=True, blank=True)
    logo_reducido_archivo_id = models.BigIntegerField(db_column='evi_logo_reducido_archivo_id', null=True, blank=True)
    favicon_archivo_id = models.BigIntegerField(db_column='evi_favicon_archivo_id', null=True, blank=True)
    portada_archivo_id = models.BigIntegerField(db_column='evi_portada_archivo_id', null=True, blank=True)
    color_primario = models.CharField(db_column='evi_color_primario', max_length=7, null=True, blank=True)
    color_secundario = models.CharField(db_column='evi_color_secundario', max_length=7, null=True, blank=True)
    color_acento = models.CharField(db_column='evi_color_acento', max_length=7, null=True, blank=True)
    tipografia = models.CharField(db_column='evi_tipografia', max_length=100, null=True, blank=True)
    sitio_web = models.CharField(db_column='evi_sitio_web', max_length=250, null=True, blank=True)
    facebook = models.CharField(db_column='evi_facebook', max_length=250, null=True, blank=True)
    instagram = models.CharField(db_column='evi_instagram', max_length=250, null=True, blank=True)
    tiktok = models.CharField(db_column='evi_tiktok', max_length=250, null=True, blank=True)
    youtube = models.CharField(db_column='evi_youtube', max_length=250, null=True, blank=True)
    whatsapp = models.CharField(db_column='evi_whatsapp', max_length=20, null=True, blank=True)
    correo_publico = models.CharField(db_column='evi_correo_publico', max_length=150, null=True, blank=True)
    estado = models.CharField(db_column='evi_estado', max_length=20, default='BORRADOR')
    fecha_creacion = models.DateTimeField(db_column='evi_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='evi_fecha_actualizacion', null=True, blank=True)
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='evi_actualizado_por',
        related_name='identidades_actualizadas',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'pdg"."evi_empresa_identidad'

    def __str__(self):
        return f"Identidad Pública: {self.nombre_publico}"
