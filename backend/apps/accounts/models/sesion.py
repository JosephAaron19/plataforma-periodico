from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoSesion

class Sesion(models.Model):
    id = models.UUIDField(db_column='ses_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='sesiones'
    )
    token_hash = models.CharField(db_column='ses_token_hash', max_length=255, unique=True)
    direccion_ip = models.GenericIPAddressField(db_column='ses_direccion_ip', null=True, blank=True)
    agente_usuario = models.TextField(db_column='ses_agente_usuario', null=True, blank=True)
    dispositivo = models.CharField(db_column='ses_dispositivo', max_length=100, null=True, blank=True)
    sistema_operativo = models.CharField(db_column='ses_sistema_operativo', max_length=100, null=True, blank=True)
    fecha_inicio = models.DateTimeField(db_column='ses_fecha_inicio', auto_now_add=True)
    fecha_ultimo_uso = models.DateTimeField(db_column='ses_fecha_ultimo_uso', null=True, blank=True)
    fecha_expiracion = models.DateTimeField(db_column='ses_fecha_expiracion')
    fecha_cierre = models.DateTimeField(db_column='ses_fecha_cierre', null=True, blank=True)
    motivo_cierre = models.CharField(db_column='ses_motivo_cierre', max_length=100, null=True, blank=True)
    estado = models.CharField(
        db_column='ses_estado',
        max_length=20,
        choices=EstadoSesion.CHOICES,
        default=EstadoSesion.ACTIVA
    )

    class Meta:
        managed = False
        db_table = 'pdg"."ses_sesion'

    def __str__(self):
        return f"Sesión {self.id} - {self.usuario.usr_correo} ({self.estado})"
