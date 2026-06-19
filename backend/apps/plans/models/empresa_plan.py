from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.plans.models.plan import Plan

class EmpresaPlan(models.Model):
    id = models.BigAutoField(db_column='epl_id', primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='planes_empresa'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.DO_NOTHING,
        db_column='pla_id',
        related_name='empresas_plan'
    )
    fecha_inicio = models.DateTimeField(db_column='epl_fecha_inicio')
    fecha_fin = models.DateTimeField(db_column='epl_fecha_fin', null=True, blank=True)
    precio_contratado = models.DecimalField(db_column='epl_precio_contratado', max_digits=12, decimal_places=2, null=True, blank=True)
    moneda = models.CharField(db_column='epl_moneda', max_length=3, default='PEN')
    periodicidad = models.CharField(db_column='epl_periodicidad', max_length=20)
    renovacion_automatica = models.BooleanField(db_column='epl_renovacion_automatica', default=False)
    estado = models.CharField(db_column='epl_estado', max_length=20, default='PENDIENTE')
    motivo_cambio = models.CharField(db_column='epl_motivo_cambio', max_length=500, null=True, blank=True)
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='epl_asignado_por',
        related_name='planes_asignados'
    )
    fecha_creacion = models.DateTimeField(db_column='epl_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='epl_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."epl_empresa_plan'

    def __str__(self):
        return f"EmpresaPlan {self.id} - Empresa: {self.empresa_id} - Plan: {self.plan_id} ({self.estado})"
