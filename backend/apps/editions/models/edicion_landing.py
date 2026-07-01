from django.db import models

class EdicionLanding(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    imagen = models.CharField(db_column='imagen', max_length=500)
    orden = models.IntegerField(db_column='orden', default=0)
    fecha_creacion = models.DateTimeField(db_column='fecha_creacion', auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"edi_edicion_landing'
        ordering = ['orden', '-fecha_creacion']

    def __str__(self):
        return f"Edicion Landing {self.id}"
