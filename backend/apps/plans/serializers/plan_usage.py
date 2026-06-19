from rest_framework import serializers

class PlanSummarySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()

class ResourceUsageSerializer(serializers.Serializer):
    limit = serializers.IntegerField(allow_null=True)
    used = serializers.IntegerField()
    available = serializers.IntegerField(allow_null=True)

class StorageUsageSerializer(serializers.Serializer):
    limit_bytes = serializers.IntegerField(allow_null=True)
    used_bytes = serializers.IntegerField()
    available_bytes = serializers.IntegerField(allow_null=True)

class PlanUsageSerializer(serializers.Serializer):
    plan = PlanSummarySerializer()
    users = ResourceUsageSerializer()
    editions = ResourceUsageSerializer()
    storage = StorageUsageSerializer()
