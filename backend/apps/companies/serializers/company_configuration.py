from rest_framework import serializers
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion

class CompanyConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaConfiguracion
        fields = [
            'moneda',
            'zona_horaria',
            'idioma',
            'permite_ediciones_gratuitas',
            'permite_programacion',
            'requiere_aprobacion_publicacion',
            'limite_pdf_mb',
            'limite_paginas_pdf',
            'limite_usuarios_internos',
            'limite_ediciones_mensuales',
            'max_sesiones_lector',
            'max_sesiones_empresarial',
            'marca_agua_activa',
            'texto_marca_agua',
            'mostrar_precio_publico',
            'notificaciones_internas',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = [
            'limite_pdf_mb',
            'limite_paginas_pdf',
            'limite_usuarios_internos',
            'limite_ediciones_mensuales',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion'
        ]

    def validate_moneda(self, value):
        allowed = {'PEN', 'USD', 'EUR'}
        if value not in allowed:
            raise serializers.ValidationError(f"Moneda '{value}' no soportada. Permitidas: {', '.join(allowed)}.")
        return value

    def validate_idioma(self, value):
        allowed = {'es', 'en'}
        if value not in allowed:
            raise serializers.ValidationError(f"Idioma '{value}' no soportado. Permitidos: {', '.join(allowed)}.")
        return value
