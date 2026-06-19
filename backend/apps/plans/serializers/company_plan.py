from rest_framework import serializers
from apps.plans.models.empresa_plan import EmpresaPlan
from apps.plans.serializers.plan import PlanSerializer

class CompanyPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()
    
    class Meta:
        model = EmpresaPlan
        fields = [
            'id',
            'plan',
            'fecha_inicio',
            'fecha_fin',
            'precio_contratado',
            'moneda',
            'periodicidad',
            'renovacion_automatica',
            'estado'
        ]
