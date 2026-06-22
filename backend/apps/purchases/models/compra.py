from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion


class Compra(models.Model):
    """
    Unmanaged model mapping to pdg.com_compra.
    Represents a purchase of a specific edition by a user.

    Physical states (com_estado):
      PENDIENTE  — purchase created, awaiting payment confirmation
      PAGADO     — payment confirmed, access granted
      CANCELADO  — purchase cancelled by user or system
      RECHAZADO  — payment rejected by provider
      ERROR      — internal processing error

    Unique constraint: com_referencia_interna (idempotency key).
    Composite unique: (com_id, usr_id, edi_id) via uq_com_id_usuario_edicion.
    """
    # Physical state choices — derived from schema defaults/flow (no DB CHECK observed)
    PENDIENTE = 'PENDIENTE'
    PAGADO = 'PAGADO'
    CANCELADO = 'CANCELADO'
    RECHAZADO = 'RECHAZADO'
    ERROR = 'ERROR'
    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (PAGADO, 'Pagado'),
        (CANCELADO, 'Cancelado'),
        (RECHAZADO, 'Rechazado'),
        (ERROR, 'Error'),
    ]

    ORIGEN_WEB = 'WEB'
    ORIGEN_CHOICES = [
        (ORIGEN_WEB, 'Web'),
    ]

    id = models.BigAutoField(db_column='com_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='compras'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='compras'
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='compras'
    )
    referencia_interna = models.CharField(
        db_column='com_referencia_interna', max_length=100, unique=True
    )
    precio_unitario = models.DecimalField(
        db_column='com_precio_unitario', max_digits=12, decimal_places=2
    )
    monto_total = models.DecimalField(
        db_column='com_monto_total', max_digits=12, decimal_places=2
    )
    moneda = models.CharField(db_column='com_moneda', max_length=3, default='PEN')
    estado = models.CharField(
        db_column='com_estado', max_length=20,
        choices=ESTADO_CHOICES, default=PENDIENTE
    )
    origen = models.CharField(
        db_column='com_origen', max_length=30,
        choices=ORIGEN_CHOICES, default=ORIGEN_WEB
    )
    fecha_creacion = models.DateTimeField(db_column='com_fecha_creacion', auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(db_column='com_fecha_confirmacion', null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(db_column='com_fecha_cancelacion', null=True, blank=True)
    motivo_cancelacion = models.CharField(
        db_column='com_motivo_cancelacion', max_length=500, null=True, blank=True
    )
    acceso_habilitado = models.BooleanField(db_column='com_acceso_habilitado', default=False)

    class Meta:
        managed = False
        db_table = 'pdg\".\"com_compra'

    def __str__(self):
        return f"Compra {self.id}: Usuario {self.usuario_id} -> Edicion {self.edicion_id} ({self.estado})"
