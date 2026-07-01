from django.db import models

class NoticiaLanding(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    titulo = models.CharField(db_column='titulo', max_length=250)
    descripcion = models.CharField(db_column='descripcion', max_length=500)
    imagen = models.CharField(db_column='imagen', max_length=500)
    fecha_creacion = models.DateTimeField(db_column='fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='fecha_actualizacion', auto_now=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"content_noticia_landing'
        ordering = ['-fecha_actualizacion', '-fecha_creacion']

    def __str__(self):
        return f"Noticia Landing {self.id}: {self.titulo}"
