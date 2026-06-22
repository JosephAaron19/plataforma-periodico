from django.db import models
from apps.purchases.models.compra import Compra
from apps.purchases.models.proveedor_pago import ProveedorPago


class Pago(models.Model):
    """
    Unmanaged model mapping to pdg.pag_pago.
    Represents a payment attempt for a purchase.

    Physical states (pag_estado):
      CREADO     — payment attempt registered (default)
      CONFIRMADO — payment confirmed by provider
      RECHAZADO  — payment rejected by provider
      ERROR      — processing error

    Unique constraints:
      - (com_id, pag_numero_intento) — prevents duplicate attempts
      - pag_identificador_externo    — external idempotency (real gateway)
    """
    CREADO = 'CREADO'
    CONFIRMADO = 'CONFIRMADO'
    RECHAZADO = 'RECHAZADO'
    ERROR = 'ERROR'
    ESTADO_CHOICES = [
        (CREADO, 'Creado'),
        (CONFIRMADO, 'Confirmado'),
        (RECHAZADO, 'Rechazado'),
        (ERROR, 'Error'),
    ]

    id = models.BigAutoField(db_column='pag_id', primary_key=True)
    compra = models.ForeignKey(
        Compra,
        on_delete=models.DO_NOTHING,
        db_column='com_id',
        related_name='pagos'
    )
    proveedor = models.ForeignKey(
        ProveedorPago,
        on_delete=models.DO_NOTHING,
        db_column='ppr_id',
        related_name='pagos'
    )
    numero_intento = models.IntegerField(db_column='pag_numero_intento')
    identificador_externo = models.CharField(
        db_column='pag_identificador_externo', max_length=200, null=True, blank=True, unique=True
    )
    monto = models.DecimalField(db_column='pag_monto', max_digits=12, decimal_places=2)
    moneda = models.CharField(db_column='pag_moneda', max_length=3, default='PEN')
    estado = models.CharField(
        db_column='pag_estado', max_length=20, choices=ESTADO_CHOICES, default=CREADO
    )
    estado_externo = models.CharField(
        db_column='pag_estado_externo', max_length=100, null=True, blank=True
    )
    medio_pago = models.CharField(
        db_column='pag_medio_pago', max_length=50, null=True, blank=True
    )
    marca_tarjeta = models.CharField(
        db_column='pag_marca_tarjeta', max_length=30, null=True, blank=True
    )
    # Only last 4 digits — never full card number
    ultimos_cuatro = models.CharField(
        db_column='pag_ultimos_cuatro', max_length=4, null=True, blank=True
    )
    codigo_respuesta = models.CharField(
        db_column='pag_codigo_respuesta', max_length=50, null=True, blank=True
    )
    mensaje_respuesta = models.CharField(
        db_column='pag_mensaje_respuesta', max_length=300, null=True, blank=True
    )
    fecha_inicio = models.DateTimeField(db_column='pag_fecha_inicio', auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(
        db_column='pag_fecha_confirmacion', null=True, blank=True
    )
    fecha_actualizacion = models.DateTimeField(
        db_column='pag_fecha_actualizacion', null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'pdg\".\"pag_pago'

    def __str__(self):
        return f"Pago {self.id}: Compra {self.compra_id} intento #{self.numero_intento} ({self.estado})"
