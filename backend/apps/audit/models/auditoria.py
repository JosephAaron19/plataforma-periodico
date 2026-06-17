from django.db import models

class Auditoria(models.Model):
    id = models.BigAutoField(db_column='aud_id', primary_key=True)
    usuario = models.ForeignKey(
        'accounts.Usuario',
        db_column='usr_id',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias'
    )
    emp_id = models.BigIntegerField(db_column='emp_id', null=True, blank=True)
    modulo = models.CharField(db_column='aud_modulo', max_length=10)
    accion = models.CharField(db_column='aud_accion', max_length=100)
    entidad = models.CharField(db_column='aud_entidad', max_length=120)
    entidad_id = models.CharField(db_column='aud_entidad_id', max_length=100, null=True, blank=True)
    valores_anteriores = models.JSONField(db_column='aud_valores_anteriores', null=True, blank=True)
    valores_nuevos = models.JSONField(db_column='aud_valores_nuevos', null=True, blank=True)
    resultado = models.CharField(db_column='aud_resultado', max_length=20)
    motivo = models.CharField(db_column='aud_motivo', max_length=500, null=True, blank=True)
    direccion_ip = models.GenericIPAddressField(db_column='aud_direccion_ip', null=True, blank=True)
    agente_usuario = models.TextField(db_column='aud_agente_usuario', null=True, blank=True)
    proceso_origen = models.CharField(db_column='aud_proceso_origen', max_length=100, null=True, blank=True)
    fecha = models.DateTimeField(db_column='aud_fecha', auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'pdg"."aud_auditoria'

    def __str__(self):
        return f"Auditoria {self.id} - Modulo: {self.modulo} - Accion: {self.accion} - Resultado: {self.resultado}"
