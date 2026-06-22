from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion

class ProgresoLectura(models.Model):
    id = models.BigAutoField(db_column='prl_id', primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='progresos_lectura'
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='progresos_lectura'
    )
    ultima_pagina = models.IntegerField(db_column='prl_ultima_pagina', default=1)
    porcentaje = models.DecimalField(db_column='prl_porcentaje', max_digits=5, decimal_places=2, default=0.00)
    fecha_ultima_lectura = models.DateTimeField(db_column='prl_fecha_ultima_lectura')
    fecha_creacion = models.DateTimeField(db_column='prl_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='prl_fecha_actualizacion', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pdg\".\"prl_progreso_lectura'
        unique_together = (('usuario', 'edicion'),)

    def __str__(self):
        return f"ProgresoLectura {self.id}: Usuario {self.usuario_id} -> Edicion {self.edicion_id} (Pag: {self.ultima_pagina}, {self.porcentaje}%)"
