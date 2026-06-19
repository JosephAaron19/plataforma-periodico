from rest_framework import serializers
from apps.plans.models.plan import Plan

class PlanSerializer(serializers.ModelSerializer):
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
            'limite_paginas_pdf'
        ]
