from rest_framework import serializers
from apps.files.models.archivo import Archivo

class ArchivoMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = [
            'id', 'nombre_original', 'extension', 'tipo_mime',
            'tamano_bytes', 'hash_sha256', 'es_publico', 'estado',
            'fecha_creacion'
        ]
        read_only_fields = fields
