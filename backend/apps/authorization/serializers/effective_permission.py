from rest_framework import serializers

class EffectivePermissionSerializer(serializers.Serializer):
    code = serializers.CharField()
    nombre = serializers.CharField()
    origen = serializers.CharField()
