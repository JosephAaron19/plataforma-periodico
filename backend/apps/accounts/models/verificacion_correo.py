from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoVerificacion

class VerificacionCorreo(models.Model):
    id = models.UUIDField(db_column='ver_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='verificaciones_correo'
    )
    token_hash = models.CharField(db_column='ver_token_hash', max_length=255, unique=True)
    fecha_solicitud = models.DateTimeField(db_column='ver_fecha_solicitud', auto_now_add=True)
    fecha_expiracion = models.DateTimeField(db_column='ver_fecha_expiracion')
    fecha_verificacion = models.DateTimeField(db_column='ver_fecha_verificacion', null=True, blank=True)
    intentos = models.IntegerField(db_column='ver_intentos', default=0)
    estado = models.CharField(
        db_column='ver_estado',
        max_length=20,
        choices=EstadoVerificacion.CHOICES,
        default=EstadoVerificacion.PENDIENTE
    )
    direccion_ip = models.GenericIPAddressField(db_column='ver_direccion_ip', null=True, blank=True)
    motivo_invalidacion = models.CharField(db_column='ver_motivo_invalidacion', max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."ver_verificacion_correo'

    def __str__(self):
        return f"Verificación Correo {self.id} - {self.usuario.usr_correo} ({self.estado})"
