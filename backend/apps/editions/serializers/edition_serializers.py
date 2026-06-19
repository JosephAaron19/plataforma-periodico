from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.editions.services.edition_create_service import validate_edition_data

class UsuarioResumidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'usr_correo', 'nombres', 'apellidos']
        read_only_fields = fields


class EmpresaResumidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'ruc', 'razon_social', 'slug', 'nombre_comercial']
        read_only_fields = fields


class EditionCreateSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50)
    titulo = serializers.CharField(max_length=250)
    slug = serializers.CharField(max_length=250, required=False, allow_blank=True)
    descripcion_corta = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    descripcion_larga = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fecha_edicion = serializers.DateField()
    modalidad = serializers.ChoiceField(choices=['GRATUITA', 'PAGO'], default='PAGO')
    precio = serializers.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    moneda = serializers.CharField(max_length=3, default='PEN')
    numero_paginas = serializers.IntegerField(required=False, allow_null=True)
    es_destacada = serializers.BooleanField(default=False)
    permite_compra = serializers.BooleanField(default=True)
    permite_muestra = serializers.BooleanField(default=False)
    paginas_muestra = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        # Delegate validation to physical constraint checker
        try:
            validate_edition_data(attrs)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message)
        return attrs


class EditionUpdateSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50, required=False)
    titulo = serializers.CharField(max_length=250, required=False)
    slug = serializers.CharField(max_length=250, required=False, allow_blank=True)
    descripcion_corta = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    descripcion_larga = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fecha_edicion = serializers.DateField(required=False)
    modalidad = serializers.ChoiceField(choices=['GRATUITA', 'PAGO'], required=False)
    precio = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    moneda = serializers.CharField(max_length=3, required=False)
    numero_paginas = serializers.IntegerField(required=False, allow_null=True)
    es_destacada = serializers.BooleanField(required=False)
    permite_compra = serializers.BooleanField(required=False)
    permite_muestra = serializers.BooleanField(required=False)
    paginas_muestra = serializers.IntegerField(required=False, allow_null=True)


class EditionListSerializer(serializers.ModelSerializer):
    creador = UsuarioResumidoSerializer(source='creado_por', read_only=True)
    portada_url = serializers.SerializerMethodField()

    class Meta:
        model = Edicion
        fields = [
            'id', 'codigo', 'titulo', 'slug', 'estado', 'fecha_edicion', 
            'fecha_publicacion', 'precio', 'moneda', 'es_destacada', 
            'creador', 'fecha_creacion', 'fecha_actualizacion', 'portada_url'
        ]
        read_only_fields = fields

    def get_portada_url(self, obj) -> str:
        # Retrieve the current cover page file relation if one exists
        portada_rel = obj.archivos_asociados.filter(
            tipo_archivo='PORTADA',
            es_actual=True,
            estado='ACTIVO'
        ).select_related('archivo').first()
        
        if portada_rel and portada_rel.archivo:
            return portada_rel.archivo.ruta_storage
        return None


class EditionDetailSerializer(serializers.ModelSerializer):
    creador = UsuarioResumidoSerializer(source='creado_por', read_only=True)
    actualizado_por = UsuarioResumidoSerializer(read_only=True)
    empresa = EmpresaResumidoSerializer(read_only=True)
    portada_url = serializers.SerializerMethodField()

    class Meta:
        model = Edicion
        fields = [
            'id', 'empresa', 'codigo', 'titulo', 'slug', 'descripcion_corta',
            'descripcion_larga', 'fecha_edicion', 'fecha_publicacion',
            'modalidad', 'precio', 'moneda', 'numero_paginas', 'es_destacada',
            'permite_compra', 'permite_muestra', 'paginas_muestra', 'estado',
            'creador', 'actualizado_por', 'fecha_creacion', 'fecha_actualizacion',
            'portada_url'
        ]
        read_only_fields = fields

    def get_portada_url(self, obj) -> str:
        portada_rel = obj.archivos_asociados.filter(
            tipo_archivo='PORTADA',
            es_actual=True,
            estado='ACTIVO'
        ).select_related('archivo').first()
        
        if portada_rel and portada_rel.archivo:
            return portada_rel.archivo.ruta_storage
        return None


class EditionScheduleSerializer(serializers.Serializer):
    scheduled_at = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=50, default='America/Lima')


class EditionPublicSerializer(serializers.ModelSerializer):
    empresa = EmpresaResumidoSerializer(read_only=True)
    portada_url = serializers.SerializerMethodField()

    class Meta:
        model = Edicion
        fields = [
            'id', 'empresa', 'titulo', 'slug', 'descripcion_corta', 'descripcion_larga',
            'fecha_edicion', 'fecha_publicacion', 'modalidad', 'precio', 'moneda',
            'numero_paginas', 'es_destacada', 'portada_url'
        ]
        read_only_fields = fields

    def get_portada_url(self, obj) -> str:
        # For public views, only show cover if it is public and active
        portada_rel = obj.archivos_asociados.filter(
            tipo_archivo='PORTADA',
            es_actual=True,
            estado='ACTIVO',
            archivo__es_publico=True,
            archivo__eliminado=False
        ).select_related('archivo').first()
        
        if portada_rel and portada_rel.archivo:
            return portada_rel.archivo.ruta_storage
        return None
