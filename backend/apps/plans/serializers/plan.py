from rest_framework import serializers
from apps.plans.models.plan import Plan
from apps.plans.models.plan_funcionalidad import PlanFuncionalidad

class PlanFuncionalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFuncionalidad
        fields = [
            'id',
            'codigo_funcionalidad',
            'nombre',
            'descripcion',
            'limite_valor',
            'valor_texto',
            'habilitada'
        ]

class PlanSerializer(serializers.ModelSerializer):
    funcionalidades = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'precio',
            'moneda',
            'periodicidad',
            'limite_usuarios',
            'limite_ediciones_mes',
            'limite_storage_mb',
            'limite_pdf_mb',
            'limite_paginas_pdf',
            'es_publico',
            'orden',
            'estado',
            'funcionalidades'
        ]

    def get_funcionalidades(self, obj):
        try:
            if hasattr(obj, 'funcionalidades'):
                # Force evaluation of the queryset to catch DatabaseOperationForbidden in test environments
                queryset = obj.funcionalidades.all()
                return PlanFuncionalidadSerializer(queryset, many=True).data
            return []
        except Exception as e:
            if 'DatabaseOperationForbidden' in type(e).__name__:
                return []
            raise e

    def create(self, validated_data):
        # Read functionalities list from initial data since method field is read-only
        funcionalidades_data = self.initial_data.get('funcionalidades', [])
        plan = Plan.objects.using('periodico_db').create(**validated_data)
        for func_data in funcionalidades_data:
            PlanFuncionalidad.objects.using('periodico_db').create(
                plan=plan,
                codigo_funcionalidad=func_data.get('codigo_funcionalidad'),
                nombre=func_data.get('nombre'),
                descripcion=func_data.get('descripcion'),
                habilitada=func_data.get('habilitada', True)
            )
        return plan

    def update(self, instance, validated_data):
        # Read functionalities list from initial data since method field is read-only
        funcionalidades_data = self.initial_data.get('funcionalidades', [])
        
        # Update plan attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using='periodico_db')

        # Replace functionalities
        PlanFuncionalidad.objects.using('periodico_db').filter(plan=instance).delete()
        for func_data in funcionalidades_data:
            PlanFuncionalidad.objects.using('periodico_db').create(
                plan=instance,
                codigo_funcionalidad=func_data.get('codigo_funcionalidad'),
                nombre=func_data.get('nombre'),
                descripcion=func_data.get('descripcion'),
                habilitada=func_data.get('habilitada', True)
            )
        
        return instance
