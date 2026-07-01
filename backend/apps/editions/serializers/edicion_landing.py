from rest_framework import serializers
from apps.editions.models.edicion_landing import EdicionLanding

class EdicionLandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdicionLanding
        fields = ['id', 'imagen', 'orden', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']
