from django.db import models
from apps.accounts.models.usuario import Usuario

class Perfil(models.Model):
    id = models.BigAutoField(db_column='prf_id', primary_key=True)
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='perfil'
    )
    foto_url = models.CharField(db_column='prf_foto_url', max_length=255, null=True, blank=True)
    fecha_nacimiento = models.DateField(db_column='prf_fecha_nacimiento', null=True, blank=True)
    genero = models.CharField(db_column='prf_genero', max_length=20, null=True, blank=True)
    direccion = models.CharField(db_column='prf_direccion', max_length=255, null=True, blank=True)
    departamento = models.CharField(db_column='prf_departamento', max_length=100, null=True, blank=True)
    provincia = models.CharField(db_column='prf_provincia', max_length=100, null=True, blank=True)
    distrito = models.CharField(db_column='prf_distrito', max_length=100, null=True, blank=True)
    preferencia_tema = models.CharField(db_column='prf_preferencia_tema', max_length=20, null=True, blank=True)
    idioma = models.CharField(db_column='prf_idioma', max_length=10, default='es')
    fecha_creacion = models.DateTimeField(db_column='prf_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='prf_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."prf_perfil'

    def __str__(self):
        return f"Perfil de {self.usuario.usr_correo}"
