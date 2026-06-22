from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.access.models.acceso_tipo import AccesoTipo

class AccesoEdicion(models.Model):
    id = models.BigAutoField(db_column='acc_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='accesos_contenido'
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='accesos_contenido'
    )
    compra_id = models.BigIntegerField(db_column='com_id', null=True, blank=True)
    tipo_acceso = models.ForeignKey(
        AccesoTipo,
        on_delete=models.DO_NOTHING,
        db_column='atr_id',
        related_name='accesos_contenido'
    )
    fecha_inicio = models.DateTimeField(db_column='acc_fecha_inicio')
    fecha_fin = models.DateTimeField(db_column='acc_fecha_fin', null=True, blank=True)
    estado = models.CharField(db_column='acc_estado', max_length=20, default='ACTIVO')
    origen_referencia = models.CharField(db_column='acc_origen_referencia', max_length=150, null=True, blank=True)
    otorgado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='acc_otorgado_por',
        related_name='accesos_otorgados',
        null=True,
        blank=True
    )
    motivo = models.CharField(db_column='acc_motivo', max_length=500, null=True, blank=True)
    fecha_creacion = models.DateTimeField(db_column='acc_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='acc_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"acc_acceso_contenido'

    def __str__(self):
        return f"Acceso {self.id}: Usuario {self.usuario_id} -> Edicion {self.edicion_id} ({self.estado})"
