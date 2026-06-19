import uuid
from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.authorization.models.rol import Rol

class InvitacionUsuario(models.Model):
    id = models.UUIDField(db_column='inv_id', primary_key=True, default=uuid.uuid4)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='invitaciones'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='invitaciones_recibidas',
        null=True,
        blank=True
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.DO_NOTHING,
        db_column='rol_id',
        related_name='invitaciones_rol'
    )
    correo = models.CharField(db_column='inv_correo', max_length=150)
    token_hash = models.CharField(db_column='inv_token_hash', max_length=255, unique=True)
    invitado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='inv_invitado_por',
        related_name='invitaciones_enviadas'
    )
    fecha_envio = models.DateTimeField(db_column='inv_fecha_envio', auto_now_add=True)
    fecha_expiracion = models.DateTimeField(db_column='inv_fecha_expiracion')
    fecha_aceptacion = models.DateTimeField(db_column='inv_fecha_aceptacion', null=True, blank=True)
    estado = models.CharField(db_column='inv_estado', max_length=20, default='PENDIENTE')
    mensaje = models.CharField(db_column='inv_mensaje', max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."inv_invitacion_usuario'

    def __str__(self):
        # Safe string format without exposing hashes
        return f"Invitacion a {self.correo} en Empresa {self.empresa_id} ({self.estado})"
