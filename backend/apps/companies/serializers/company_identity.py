from rest_framework import serializers
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.selectors.company_file_selectors import validate_company_file_reference

class CompanyIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaIdentidad
        fields = [
            'nombre_publico',
            'descripcion_corta',
            'descripcion_larga',
            'logo_archivo_id',
            'logo_reducido_archivo_id',
            'favicon_archivo_id',
            'portada_archivo_id',
            'color_primario',
            'color_secundario',
            'color_acento',
            'tipografia',
            'sitio_web',
            'facebook',
            'instagram',
            'tiktok',
            'youtube',
            'whatsapp',
            'correo_publico',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['estado', 'fecha_creacion', 'fecha_actualizacion']

    def validate(self, attrs):
        # Retrieve the company ID from the instance or the URL context
        empresa_id = None
        if self.instance and self.instance.empresa_id:
            empresa_id = self.instance.empresa_id
        else:
            view = self.context.get('view')
            if view and hasattr(view, 'kwargs'):
                empresa_id = view.kwargs.get('pk')

        if empresa_id:
            file_fields = [
                'logo_archivo_id', 
                'logo_reducido_archivo_id', 
                'favicon_archivo_id', 
                'portada_archivo_id'
            ]
            for field in file_fields:
                if field in attrs and attrs[field] is not None:
                    if not validate_company_file_reference(attrs[field], empresa_id):
                        raise serializers.ValidationError({
                            field: "El archivo seleccionado no existe, no pertenece a esta empresa o no está disponible."
                        })
        return attrs
