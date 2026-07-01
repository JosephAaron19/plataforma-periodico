from rest_framework import serializers
from apps.content.models.noticia_landing import NoticiaLanding

class NoticiaLandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticiaLanding
        fields = ['id', 'titulo', 'descripcion', 'imagen', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
