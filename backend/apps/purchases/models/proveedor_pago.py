from django.db import models


class ProveedorPago(models.Model):
    """
    Unmanaged model mapping to pdg.ppr_proveedor_pago.
    Catalogue of payment providers (real and mock).
    """
    id = models.BigAutoField(db_column='ppr_id', primary_key=True)
    codigo = models.CharField(db_column='ppr_codigo', max_length=50, unique=True)
    nombre = models.CharField(db_column='ppr_nombre', max_length=150, unique=True)
    descripcion = models.CharField(db_column='ppr_descripcion', max_length=500, null=True, blank=True)
    estado = models.CharField(db_column='ppr_estado', max_length=20, default='ACTIVO')
    es_predeterminado = models.BooleanField(db_column='ppr_es_predeterminado', default=False)
    fecha_creacion = models.DateTimeField(db_column='ppr_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='ppr_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"ppr_proveedor_pago'

    def __str__(self):
        return f"ProveedorPago {self.id}: {self.codigo} ({self.estado})"
