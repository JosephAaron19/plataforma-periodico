from rest_framework import serializers
from apps.editions.models.edicion import Edicion

class LibraryEditionSerializer(serializers.ModelSerializer):
    empresa_id = serializers.IntegerField(source='empresa.id')
    empresa_nombre = serializers.CharField(source='empresa.nombre_comercial')
    empresa_slug = serializers.CharField(source='empresa.slug')

    class Meta:
        model = Edicion
        fields = [
            'id',
            'codigo',
            'titulo',
            'slug',
            'descripcion_corta',
            'descripcion_larga',
            'fecha_edicion',
            'fecha_publicacion',
            'modalidad',
            'precio',
            'moneda',
            'numero_paginas',
            'es_destacada',
            'permite_muestra',
            'paginas_muestra',
            'empresa_id',
            'empresa_nombre',
            'empresa_slug',
        ]
