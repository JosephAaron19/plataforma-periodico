from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class EmpresaHistorial(models.Model):
    id = models.BigAutoField(db_column='ehi_id', primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='historiales'
    )
    tipo_evento = models.CharField(db_column='ehi_tipo_evento', max_length=50)
    estado_anterior = models.CharField(db_column='ehi_estado_anterior', max_length=20, null=True, blank=True)
    estado_nuevo = models.CharField(db_column='ehi_estado_nuevo', max_length=20, null=True, blank=True)
    motivo = models.CharField(db_column='ehi_motivo', max_length=500)
    detalle_anterior = models.JSONField(db_column='ehi_detalle_anterior', null=True, blank=True)
    detalle_nuevo = models.JSONField(db_column='ehi_detalle_nuevo', null=True, blank=True)
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='ehi_realizado_por',
        related_name='historiales_empresa'
    )
    fecha = models.DateTimeField(db_column='ehi_fecha', auto_now_add=True)
    direccion_ip = models.GenericIPAddressField(db_column='ehi_direccion_ip', null=True, blank=True)
    resultado = models.CharField(db_column='ehi_resultado', max_length=20, default='EXITOSO')

    class Meta:
        managed = False
        db_table = 'pdg"."ehi_empresa_historial'

    def __str__(self):
        return f"Historial {self.id} - {self.tipo_evento} ({self.resultado})"
