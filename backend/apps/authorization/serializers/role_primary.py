from rest_framework import serializers

class RoleFinalizeSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=500, required=True)

class RoleSetPrimarySerializer(serializers.Serializer):
    pass
