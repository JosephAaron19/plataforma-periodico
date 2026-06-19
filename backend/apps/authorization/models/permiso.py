from django.db import models

class Permiso(models.Model):
    id = models.BigAutoField(db_column='per_id', primary_key=True)
    codigo = models.CharField(db_column='per_codigo', max_length=100, unique=True)
    nombre = models.CharField(db_column='per_nombre', max_length=150)
    descripcion = models.CharField(db_column='per_descripcion', max_length=500, null=True, blank=True)
    modulo = models.CharField(db_column='per_modulo', max_length=10)
    accion = models.CharField(db_column='per_accion', max_length=50)
    es_critico = models.BooleanField(db_column='per_es_critico', default=False)
    estado = models.CharField(db_column='per_estado', max_length=20, default='ACTIVO')
    fecha_creacion = models.DateTimeField(db_column='per_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='per_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."per_permiso'

    def __str__(self):
        return f"Permiso: {self.nombre} ({self.codigo})"
