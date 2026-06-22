from django.db import models

class AccesoTipo(models.Model):
    id = models.BigIntegerField(db_column='atr_id', primary_key=True)
    codigo = models.CharField(db_column='atr_codigo', max_length=50)
    nombre = models.CharField(db_column='atr_nombre', max_length=100)
    descripcion = models.CharField(db_column='atr_descripcion', max_length=500, null=True, blank=True)
    estado = models.CharField(db_column='atr_estado', max_length=20, default='ACTIVO')

    class Meta:
        managed = False
        db_table = 'pdg\".\"atr_acceso_tipo'

    def __str__(self):
        return f"AccesoTipo {self.id}: {self.nombre} ({self.codigo})"
