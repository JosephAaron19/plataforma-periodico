from rest_framework import serializers
from apps.processing.models.procesamiento import Procesamiento
from apps.processing.models.procesamiento_error import ProcesamientoError

class ProcesamientoErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcesamientoError
        fields = [
            'id', 'pre_codigo', 'pre_categoria', 'pre_mensaje_usuario',
            'pre_numero_pagina', 'pre_severidad', 'pre_fecha'
        ]
        read_only_fields = fields


class ProcessingStatusSerializer(serializers.ModelSerializer):
    errores = serializers.SerializerMethodField()

    class Meta:
        model = Procesamiento
        fields = [
            'id', 'version', 'estado', 'total_paginas_esperadas',
            'total_paginas_generadas', 'porcentaje_avance',
            'fecha_solicitud', 'fecha_inicio', 'fecha_fin', 'errores'
        ]
        read_only_fields = fields

    def get_errores(self, obj):
        # Retrieve all errors associated with all attempts of this processing
        errors = ProcesamientoError.objects.using('periodico_db').filter(
            intento__procesamiento=obj
        ).order_by('pre_fecha')
        return ProcesamientoErrorSerializer(errors, many=True).data
