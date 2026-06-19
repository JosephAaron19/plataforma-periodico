from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.files.models.archivo import Archivo

class EdicionArchivo(models.Model):
    id = models.BigAutoField(db_column='eda_id', primary_key=True)
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='archivos_asociados'
    )
    archivo = models.ForeignKey(
        Archivo,
        on_delete=models.DO_NOTHING,
        db_column='arc_id',
        related_name='ediciones_asociadas'
    )
    tipo_archivo = models.CharField(db_column='eda_tipo_archivo', max_length=30)
    version = models.IntegerField(db_column='eda_version', default=1)
    es_actual = models.BooleanField(db_column='eda_es_actual', default=True)
    estado = models.CharField(db_column='eda_estado', max_length=20, default='ACTIVO')
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='eda_asignado_por',
        related_name='archivos_asignados'
    )
    fecha_asignacion = models.DateTimeField(db_column='eda_fecha_asignacion', auto_now_add=True)
    fecha_reemplazo = models.DateTimeField(db_column='eda_fecha_reemplazo', null=True, blank=True)
    motivo_reemplazo = models.CharField(db_column='eda_motivo_reemplazo', max_length=500, null=True, blank=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='ediciones_archivos'
    )

    class Meta:
        managed = False
        db_table = 'pdg\".\"eda_edicion_archivo'

    def __str__(self):
        return f"EdicionArchivo {self.id}: Edicion {self.edicion_id} - Archivo {self.archivo_id} ({self.tipo_archivo})"
