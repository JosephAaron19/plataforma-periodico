from django.db import models

class Rol(models.Model):
    id = models.BigAutoField(db_column='rol_id', primary_key=True)
    codigo = models.CharField(db_column='rol_codigo', max_length=50, unique=True)
    nombre = models.CharField(db_column='rol_nombre', max_length=100, unique=True)
    descripcion = models.CharField(db_column='rol_descripcion', max_length=500, null=True, blank=True)
    tipo = models.CharField(db_column='rol_tipo', max_length=20)
    es_sistema = models.BooleanField(db_column='rol_es_sistema', default=False)
    estado = models.CharField(db_column='rol_estado', max_length=20, default='ACTIVO')
    fecha_creacion = models.DateTimeField(db_column='rol_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='rol_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."rol_rol'

    def __str__(self):
        return f"Rol: {self.nombre} [{self.codigo}]"
