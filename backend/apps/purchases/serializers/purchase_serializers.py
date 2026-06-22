from rest_framework import serializers
from apps.purchases.models.compra import Compra
from apps.editions.models.edicion import Edicion


class PurchaseInitiateResponseSerializer(serializers.Serializer):
    """Response serializer for POST /api/v1/editions/{edi_id}/purchase/"""
    com_id = serializers.IntegerField()
    pag_id = serializers.IntegerField(allow_null=True)
    referencia_interna = serializers.CharField()
    estado = serializers.CharField()
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    moneda = serializers.CharField()
    proveedor = serializers.CharField()
    already_exists = serializers.BooleanField()


class MockConfirmRequestSerializer(serializers.Serializer):
    """Request serializer for POST /api/v1/payments/mock-confirm/"""
    com_id = serializers.IntegerField()
    force_failure = serializers.BooleanField(default=False, required=False)


class MockConfirmResponseSerializer(serializers.Serializer):
    """Response serializer for POST /api/v1/payments/mock-confirm/"""
    com_id = serializers.IntegerField()
    pag_id = serializers.IntegerField(allow_null=True)
    estado = serializers.CharField()
    acceso_id = serializers.IntegerField(allow_null=True)
    idempotente = serializers.BooleanField()


class CompraEdicionSerializer(serializers.Serializer):
    """Nested serializer for edition info in MyPurchasesView."""
    edi_id = serializers.IntegerField(source='id')
    titulo = serializers.CharField()
    slug = serializers.CharField()
    fecha_edicion = serializers.DateField()
    modalidad = serializers.CharField()
    precio = serializers.DecimalField(max_digits=12, decimal_places=2)
    moneda = serializers.CharField()


class CompraEmpresaSerializer(serializers.Serializer):
    """Nested serializer for company info in MyPurchasesView."""
    emp_id = serializers.IntegerField(source='id')
    nombre_comercial = serializers.CharField()
    slug = serializers.CharField()


class MyPurchaseItemSerializer(serializers.ModelSerializer):
    """
    Response serializer for GET /api/v1/my-purchases/
    Returns safe, non-sensitive purchase data.
    Excludes: internal tokens, raw gateway payloads, sensitive card data.
    """
    edicion = CompraEdicionSerializer(read_only=True)
    empresa = CompraEmpresaSerializer(read_only=True)
    acceso_id = serializers.SerializerMethodField()
    acceso_fecha_fin = serializers.SerializerMethodField()

    class Meta:
        model = Compra
        fields = [
            'id',
            'edicion',
            'empresa',
            'fecha_creacion',
            'fecha_confirmacion',
            'estado',
            'monto_total',
            'moneda',
            'acceso_id',
            'acceso_fecha_fin',
        ]

    def get_acceso_id(self, obj):
        """Returns the active AccesoEdicion id linked to this purchase, if any."""
        from apps.access.models.acceso_edicion import AccesoEdicion
        from django.utils import timezone
        from django.db import models as db_models
        now = timezone.now()
        acc = AccesoEdicion.objects.using('periodico_db').filter(
            compra_id=obj.id,
            estado='ACTIVO',
            fecha_inicio__lte=now
        ).filter(
            db_models.Q(fecha_fin__isnull=True) | db_models.Q(fecha_fin__gt=now)
        ).values_list('id', flat=True).first()
        return acc

    def get_acceso_fecha_fin(self, obj):
        """Returns the expiry date of the active access, if any."""
        from apps.access.models.acceso_edicion import AccesoEdicion
        from django.utils import timezone
        from django.db import models as db_models
        now = timezone.now()
        acc = AccesoEdicion.objects.using('periodico_db').filter(
            compra_id=obj.id,
            estado='ACTIVO',
            fecha_inicio__lte=now
        ).filter(
            db_models.Q(fecha_fin__isnull=True) | db_models.Q(fecha_fin__gt=now)
        ).values('fecha_fin').first()
        if acc:
            return acc['fecha_fin']
        return None
