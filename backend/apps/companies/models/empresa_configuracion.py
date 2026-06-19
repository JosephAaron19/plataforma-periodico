from django.db import models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class EmpresaConfiguracion(models.Model):
    id = models.BigAutoField(db_column='ecf_id', primary_key=True)
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.DO_NOTHING,
        db_column='emp_id',
        related_name='configuracion'
    )
    moneda = models.CharField(db_column='ecf_moneda', max_length=3, default='PEN')
    zona_horaria = models.CharField(db_column='ecf_zona_horaria', max_length=50, default='America/Lima')
    idioma = models.CharField(db_column='ecf_idioma', max_length=10, default='es')
    permite_ediciones_gratuitas = models.BooleanField(db_column='ecf_permite_ediciones_gratuitas', default=True)
    permite_programacion = models.BooleanField(db_column='ecf_permite_programacion', default=True)
    requiere_aprobacion_publicacion = models.BooleanField(db_column='ecf_requiere_aprobacion_publicacion', default=False)
    limite_pdf_mb = models.IntegerField(db_column='ecf_limite_pdf_mb', default=50)
    limite_paginas_pdf = models.IntegerField(db_column='ecf_limite_paginas_pdf', default=500)
    limite_usuarios_internos = models.IntegerField(db_column='ecf_limite_usuarios_internos', null=True, blank=True)
    limite_ediciones_mensuales = models.IntegerField(db_column='ecf_limite_ediciones_mensuales', null=True, blank=True)
    max_sesiones_lector = models.IntegerField(db_column='ecf_max_sesiones_lector', default=2)
    max_sesiones_empresarial = models.IntegerField(db_column='ecf_max_sesiones_empresarial', default=1)
    marca_agua_activa = models.BooleanField(db_column='ecf_marca_agua_activa', default=True)
    texto_marca_agua = models.CharField(db_column='ecf_texto_marca_agua', max_length=200, null=True, blank=True)
    mostrar_precio_publico = models.BooleanField(db_column='ecf_mostrar_precio_publico', default=True)
    notificaciones_internas = models.BooleanField(db_column='ecf_notificaciones_internas', default=True)
    estado = models.CharField(db_column='ecf_estado', max_length=20, default='ACTIVA')
    fecha_creacion = models.DateTimeField(db_column='ecf_fecha_creacion', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(db_column='ecf_fecha_actualizacion', null=True, blank=True)
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='ecf_actualizado_por',
        related_name='configuraciones_actualizadas',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'pdg"."ecf_empresa_configuracion'

    def __str__(self):
        return f"Configuración Empresa ID: {self.empresa_id}"
