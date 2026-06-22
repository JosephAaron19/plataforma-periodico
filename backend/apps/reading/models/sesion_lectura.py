import uuid
from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.access.models.acceso_edicion import AccesoEdicion

class SesionLectura(models.Model):
    id = models.UUIDField(db_column='sle_id', primary_key=True, default=uuid.uuid4)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usr_id',
        related_name='sesiones_lectura'
    )
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.DO_NOTHING,
        db_column='edi_id',
        related_name='sesiones_lectura'
    )
    acceso = models.ForeignKey(
        AccesoEdicion,
        on_delete=models.DO_NOTHING,
        db_column='acc_id',
        related_name='sesiones_lectura'
    )
    sesion_jwt_id = models.UUIDField(db_column='ses_id', null=True, blank=True)
    fecha_inicio = models.DateTimeField(db_column='sle_fecha_inicio')
    fecha_fin = models.DateTimeField(db_column='sle_fecha_fin', null=True, blank=True)
    pagina_inicio = models.IntegerField(db_column='sle_pagina_inicio', default=1)
    pagina_fin = models.IntegerField(db_column='sle_pagina_fin', null=True, blank=True)
    dispositivo = models.CharField(db_column='sle_dispositivo', max_length=150, null=True, blank=True)
    direccion_ip = models.GenericIPAddressField(db_column='sle_direccion_ip', null=True, blank=True)
    estado = models.CharField(db_column='sle_estado', max_length=20, default='ACTIVA')

    class Meta:
        managed = False
        db_table = 'pdg\".\"sle_sesion_lectura'

    def __str__(self):
        return f"SesionLectura {self.id} - Usuario {self.usuario_id} - Edicion {self.edicion_id} ({self.estado})"
