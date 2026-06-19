from rest_framework import serializers

class PlanChangeSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=50)
    reason = serializers.CharField(max_length=500)
