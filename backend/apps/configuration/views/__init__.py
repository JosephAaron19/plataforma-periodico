from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.authorization.permissions.drf_permissions import IsPlatformSuperadmin
from apps.configuration.models.parametro_sistema import ParametroSistema
from rest_framework import status
from django.utils import timezone

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class LandingConfigView(APIView):
    """
    API View to retrieve and manage Hero/Landing page settings dynamically.
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsPlatformSuperadmin()]

    def get(self, request):
        # Retrieve parameters or seed defaults if they don't exist in the database
        title_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(
            clave='HERO_TITLE',
            defaults={
                'tipo': 'TEXTO',
                'valor_texto': 'La información que conecta nuestra región',
                'descripcion': 'Título principal de la sección Hero en la Landing Page'
            }
        )
        
        subtitle_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(
            clave='HERO_SUBTITLE',
            defaults={
                'tipo': 'TEXTO',
                'valor_texto': 'Noticias locales, nacionales e internacionales con el enfoque que importa a nuestra comunidad.',
                'descripcion': 'Subtítulo o bajada de la sección Hero en la Landing Page'
            }
        )
        
        bg_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(
            clave='HERO_BACKGROUND_URL',
            defaults={
                'tipo': 'TEXTO',
                'valor_texto': 'https://images.unsplash.com/photo-1599582964755-971498d2b4a0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWF6b24lMjByYWluZm9yZXN0JTIwc3Vuc2V0JTIwcml2ZXJ8ZW58MXx8fHwxNzgyNDkxNzM0fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
                'descripcion': 'URL de la imagen de fondo para la sección Hero en la Landing Page'
            }
        )

        pos_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(
            clave='HERO_BACKGROUND_POSITION',
            defaults={
                'tipo': 'TEXTO',
                'valor_texto': 'center',
                'descripcion': 'Alineación vertical de la imagen de fondo de portada (top, center, bottom)'
            }
        )

        return Response({
            'hero_title': title_param.valor_texto,
            'hero_subtitle': subtitle_param.valor_texto,
            'hero_background_url': bg_param.valor_texto,
            'hero_background_position': pos_param.valor_texto
        }, status=status.HTTP_200_OK)

    def put(self, request):
        hero_title = request.data.get('hero_title')
        hero_subtitle = request.data.get('hero_subtitle')
        hero_background_position = request.data.get('hero_background_position', 'center')
        
        # Check if file was uploaded
        bg_file = request.FILES.get('hero_background_file')
        if bg_file:
            import uuid
            from django.core.files.storage import default_storage
            from django.conf import settings
            
            sanitized_filename = f"landing/{uuid.uuid4().hex}_{bg_file.name}"
            saved_path = default_storage.save(sanitized_filename, bg_file)
            
            media_url = settings.MEDIA_URL
            if not media_url.endswith('/'):
                media_url += '/'
            hero_background_url = f"{media_url}{saved_path}"
        else:
            hero_background_url = request.data.get('hero_background_url')

        if not hero_title or not hero_subtitle or not hero_background_url:
            return Response(
                {'detail': 'Los campos hero_title, hero_subtitle y hero_background_url son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update values
        title_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(clave='HERO_TITLE')
        title_param.valor_texto = hero_title
        title_param.fecha_actualizacion = timezone.now()
        title_param.save(using='periodico_db')

        subtitle_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(clave='HERO_SUBTITLE')
        subtitle_param.valor_texto = hero_subtitle
        subtitle_param.fecha_actualizacion = timezone.now()
        subtitle_param.save(using='periodico_db')

        bg_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(clave='HERO_BACKGROUND_URL')
        bg_param.valor_texto = hero_background_url
        bg_param.fecha_actualizacion = timezone.now()
        bg_param.save(using='periodico_db')

        pos_param, _ = ParametroSistema.objects.using('periodico_db').get_or_create(clave='HERO_BACKGROUND_POSITION')
        pos_param.valor_texto = hero_background_position
        pos_param.fecha_actualizacion = timezone.now()
        pos_param.save(using='periodico_db')

        return Response({
            'hero_title': hero_title,
            'hero_subtitle': hero_subtitle,
            'hero_background_url': hero_background_url,
            'hero_background_position': hero_background_position
        }, status=status.HTTP_200_OK)
