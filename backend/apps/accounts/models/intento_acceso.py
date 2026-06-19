from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import ResultadoIntentoAcceso

class IntentoAcceso(models.Model):
    id = models.BigAutoField(db_column='ina_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='intentos_acceso',
        null=True,
        blank=True
    )
    correo_ingresado = models.CharField(db_column='ina_correo_ingresado', max_length=255, null=True, blank=True)
    direccion_ip = models.GenericIPAddressField(db_column='ina_direccion_ip', null=True, blank=True)
    agente_usuario = models.TextField(db_column='ina_agente_usuario', null=True, blank=True)
    fecha = models.DateTimeField(db_column='ina_fecha', auto_now_add=True)
    resultado = models.CharField(
        db_column='ina_resultado',
        max_length=50,
        choices=ResultadoIntentoAcceso.CHOICES
    )
    motivo = models.CharField(db_column='ina_motivo', max_length=255, null=True, blank=True)
    bloqueo_generado = models.BooleanField(db_column='ina_bloqueo_generado', default=False)

    class Meta:
        managed = False
        db_table = 'pdg"."ina_intento_acceso'

    def __str__(self):
        return f"Intento Acceso {self.id} - {self.correo_ingresado or self.usuario.usr_correo} ({self.resultado})"
