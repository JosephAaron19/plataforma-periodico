from django.db import models
from apps.plans.models.plan import Plan
from apps.authorization.models.permiso import Permiso

class PlanFuncionalidad(models.Model):
    id = models.BigAutoField(db_column='plf_id', primary_key=True)
    plan = models.ForeignKey(
        Plan,
        on_delete=models.DO_NOTHING,
        db_column='pla_id',
        related_name='funcionalidades'
    )
    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.DO_NOTHING,
        db_column='per_id',
        related_name='plan_funcionalidades',
        null=True,
        blank=True
    )
    codigo_funcionalidad = models.CharField(db_column='plf_codigo_funcionalidad', max_length=100)
    nombre = models.CharField(db_column='plf_nombre', max_length=150)
    descripcion = models.CharField(db_column='plf_descripcion', max_length=500, null=True, blank=True)
    limite_valor = models.DecimalField(db_column='plf_limite_valor', max_digits=12, decimal_places=2, null=True, blank=True)
    valor_texto = models.CharField(db_column='plf_valor_texto', max_length=250, null=True, blank=True)
    habilitada = models.BooleanField(db_column='plf_habilitada', default=True)
    fecha_creacion = models.DateTimeField(db_column='plf_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='plf_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."plf_plan_funcionalidad'
        unique_together = (('plan', 'codigo_funcionalidad'),)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_funcionalidad}) - Plan: {self.plan.nombre}"
