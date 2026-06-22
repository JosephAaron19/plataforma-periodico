from django.db import models
from apps.payments.models.pago import Pago
from apps.purchases.models.proveedor_pago import ProveedorPago


class PagoEvento(models.Model):
    """
    Unmanaged model mapping to pdg.pge_pago_evento.
    Records payment gateway events (webhooks). Reserved for real gateway integration.

    Physical states (pge_estado_procesamiento):
      RECIBIDO   — event received (default)
      PROCESADO  — event processed successfully
      FALLIDO    — processing failed
      IGNORADO   — event ignored (duplicate or irrelevant)
    """
    RECIBIDO = 'RECIBIDO'
    PROCESADO = 'PROCESADO'
    FALLIDO = 'FALLIDO'
    IGNORADO = 'IGNORADO'
    ESTADO_PROCESAMIENTO_CHOICES = [
        (RECIBIDO, 'Recibido'),
        (PROCESADO, 'Procesado'),
        (FALLIDO, 'Fallido'),
        (IGNORADO, 'Ignorado'),
    ]

    id = models.BigAutoField(db_column='pge_id', primary_key=True)
    pago = models.ForeignKey(
        Pago,
        on_delete=models.DO_NOTHING,
        db_column='pag_id',
        related_name='eventos',
        null=True,
        blank=True
    )
    proveedor = models.ForeignKey(
        ProveedorPago,
        on_delete=models.DO_NOTHING,
        db_column='ppr_id',
        related_name='eventos'
    )
    # External identifier from gateway — NEVER store full token/secret
    identificador_externo = models.CharField(
        db_column='pge_identificador_externo', max_length=200, unique=True
    )
    tipo_evento = models.CharField(db_column='pge_tipo_evento', max_length=100)
    # payload stored as JSONB — must be sanitized before storing (no CVV, no card tokens)
    payload = models.JSONField(db_column='pge_payload', null=True, blank=True)
    fecha_evento = models.DateTimeField(db_column='pge_fecha_evento', null=True, blank=True)
    fecha_recepcion = models.DateTimeField(db_column='pge_fecha_recepcion', auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(
        db_column='pge_fecha_procesamiento', null=True, blank=True
    )
    estado_procesamiento = models.CharField(
        db_column='pge_estado_procesamiento', max_length=30,
        choices=ESTADO_PROCESAMIENTO_CHOICES, default=RECIBIDO
    )
    intentos_procesamiento = models.IntegerField(
        db_column='pge_intentos_procesamiento', default=0
    )
    resultado = models.CharField(
        db_column='pge_resultado', max_length=200, null=True, blank=True
    )
    motivo_rechazo = models.CharField(
        db_column='pge_motivo_rechazo', max_length=500, null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'pdg\".\"pge_pago_evento'

    def __str__(self):
        return f"PagoEvento {self.id}: {self.tipo_evento} ({self.estado_procesamiento})"
