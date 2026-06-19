from django.db import models
from apps.accounts.models.usuario import Usuario

class Empresa(models.Model):
    id = models.BigAutoField(db_column='emp_id', primary_key=True)
    ruc = models.CharField(db_column='emp_ruc', max_length=11, unique=True)
    razon_social = models.CharField(db_column='emp_razon_social', max_length=200)
    nombre_comercial = models.CharField(db_column='emp_nombre_comercial', max_length=180)
    slug = models.CharField(db_column='emp_slug', max_length=180, unique=True)
    descripcion = models.TextField(db_column='emp_descripcion', null=True, blank=True)
    correo = models.CharField(db_column='emp_correo', max_length=150, null=True, blank=True)
    telefono = models.CharField(db_column='emp_telefono', max_length=20, null=True, blank=True)
    direccion = models.CharField(db_column='emp_direccion', max_length=250, null=True, blank=True)
    sitio_web = models.CharField(db_column='emp_sitio_web', max_length=250, null=True, blank=True)
    estado = models.CharField(db_column='emp_estado', max_length=20, default='PENDIENTE')
    fecha_activacion = models.DateTimeField(db_column='emp_fecha_activacion', null=True, blank=True)
    fecha_suspension = models.DateTimeField(db_column='emp_fecha_suspension', null=True, blank=True)
    motivo_suspension = models.CharField(db_column='emp_motivo_suspension', max_length=500, null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='emp_creado_por',
        related_name='empresas_creadas'
    )
    fecha_creacion = models.DateTimeField(db_column='emp_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='emp_fecha_actualizacion', null=True, blank=True)
    eliminado = models.BooleanField(db_column='emp_eliminado', default=False)
    fecha_eliminacion = models.DateTimeField(db_column='emp_fecha_eliminacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg"."emp_empresa'

    def __str__(self):
        # Safe string representation without exposing sensitive details
        return f"Empresa: {self.nombre_comercial} (RUC: {self.ruc})"
