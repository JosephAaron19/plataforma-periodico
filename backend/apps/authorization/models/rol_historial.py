from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.rol import Rol
from apps.authorization.models.permiso import Permiso

class RolHistorial(models.Model):
    id = models.BigAutoField(db_column='rho_id', primary_key=True)
    usuario_empresa = models.ForeignKey(
        UsuarioEmpresa,
        on_delete=models.DO_NOTHING,
        db_column='uep_id',
        related_name='historiales_rol'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.DO_NOTHING,
        db_column='rol_id',
        related_name='historiales_asignados',
        null=True,
        blank=True
    )
    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.DO_NOTHING,
        db_column='per_id',
        related_name='historiales_permisos',
        null=True,
        blank=True
    )
    tipo_evento = models.CharField(db_column='rho_tipo_evento', max_length=50)
    valor_anterior = models.JSONField(db_column='rho_valor_anterior', null=True, blank=True)
    valor_nuevo = models.JSONField(db_column='rho_valor_nuevo', null=True, blank=True)
    motivo = models.CharField(db_column='rho_motivo', max_length=500)
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='rho_realizado_por',
        related_name='roles_modificados'
    )
    fecha = models.DateTimeField(db_column='rho_fecha', auto_now_add=True)
    direccion_ip = models.GenericIPAddressField(db_column='rho_direccion_ip', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."rho_rol_historial'

    def __str__(self):
        return f"RolHistorial {self.id} - Evento: {self.tipo_evento}"
