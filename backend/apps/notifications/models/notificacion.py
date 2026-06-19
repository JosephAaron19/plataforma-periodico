from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class Notificacion(models.Model):
    id = models.BigAutoField(db_column='not_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='notificaciones'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='notificaciones',
        null=True,
        blank=True
    )
    tipo = models.CharField(db_column='not_tipo', max_length=50)
    titulo = models.CharField(db_column='not_titulo', max_length=180)
    mensaje = models.CharField(db_column='not_mensaje', max_length=500)
    entidad = models.CharField(db_column='not_entidad', max_length=120, null=True, blank=True)
    entidad_id = models.CharField(db_column='not_entidad_id', max_length=100, null=True, blank=True)
    estado = models.CharField(db_column='not_estado', max_length=20, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(db_column='not_fecha_creacion', auto_now_add=True)
    fecha_envio = models.DateTimeField(db_column='not_fecha_envio', null=True, blank=True)
    fecha_lectura = models.DateTimeField(db_column='not_fecha_lectura', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."not_notificacion'

    def __str__(self):
        return f"Notificacion {self.id}: {self.titulo} ({self.estado})"
