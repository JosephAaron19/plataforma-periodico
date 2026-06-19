from django.db import models

class ParametroSistema(models.Model):
    id = models.BigAutoField(db_column='par_id', primary_key=True)
    clave = models.CharField(db_column='par_clave', max_length=120, unique=True)
    tipo = models.CharField(db_column='par_tipo', max_length=30)
    valor_texto = models.TextField(db_column='par_valor_texto', null=True, blank=True)
    valor_numero = models.DecimalField(db_column='par_valor_numero', max_digits=18, decimal_places=4, null=True, blank=True)
    valor_booleano = models.BooleanField(db_column='par_valor_booleano', null=True, blank=True)
    descripcion = models.CharField(db_column='par_descripcion', max_length=500, null=True, blank=True)
    es_sensible = models.BooleanField(db_column='par_es_sensible', default=False)
    estado = models.CharField(db_column='par_estado', max_length=20, default='ACTIVO')
    actualizado_por = models.BigIntegerField(db_column='par_actualizado_por', null=True, blank=True)
    fecha_creacion = models.DateTimeField(db_column='par_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='par_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."par_parametro_sistema'

    def __str__(self):
        return self.clave
