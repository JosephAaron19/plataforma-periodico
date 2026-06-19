from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoRecuperacion

class RecuperacionCuenta(models.Model):
    id = models.UUIDField(db_column='rec_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='recuperaciones'
    )
    token_hash = models.CharField(db_column='rec_token_hash', max_length=255, unique=True)
    fecha_solicitud = models.DateTimeField(db_column='rec_fecha_solicitud', auto_now_add=True)
    fecha_expiracion = models.DateTimeField(db_column='rec_fecha_expiracion')
    fecha_uso = models.DateTimeField(db_column='rec_fecha_uso', null=True, blank=True)
    ip_solicitud = models.GenericIPAddressField(db_column='rec_ip_solicitud', null=True, blank=True)
    intentos = models.IntegerField(db_column='rec_intentos', default=0)
    estado = models.CharField(
        db_column='rec_estado',
        max_length=20,
        choices=EstadoRecuperacion.CHOICES,
        default=EstadoRecuperacion.SOLICITADA
    )
    motivo_invalidacion = models.CharField(db_column='rec_motivo_invalidacion', max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."rec_recuperacion_cuenta'

    def __str__(self):
        return f"Recuperación {self.id} - {self.usuario.usr_correo} ({self.estado})"
