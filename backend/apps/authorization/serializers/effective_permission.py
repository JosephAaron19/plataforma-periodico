from rest_framework import serializers

class EffectivePermissionSerializer(serializers.Serializer):
    permission_code = serializers.CharField()
    nombre = serializers.CharField(required=False)
    granted = serializers.BooleanField()
    origin = serializers.CharField()
