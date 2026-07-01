import logging
import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings
from apps.content.models.noticia_landing import NoticiaLanding
from apps.content.serializers.noticia_landing import NoticiaLandingSerializer

logger = logging.getLogger(__name__)

class NoticiaLandingListCreateView(APIView):
    """
    API View to retrieve and create News for the Landing Page.
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = NoticiaLanding.objects.using('periodico_db').all()
        if not queryset.exists():
            default_items = [
                {
                    'titulo': 'Ganó el presidente en Perú',
                    'descripcion': 'Resultados oficiales confirman la victoria. No se reportan incidencias graves.',
                    'imagen': 'https://images.unsplash.com/photo-1580530719806-99398637c403?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJ1JTIwcHJlc2lkZW50JTIwZ292ZXJubWVudHxlbnwxfHx8fDE3ODI0OTE3MzZ8MA&ixlib=rb-4.1.0&q=80&w=400'
                },
                {
                    'titulo': 'Terremoto en Bolivia',
                    'descripcion': 'Sismo de magnitud 6.2 sacude varias zonas del país. No se reportan víctimas fatales.',
                    'imagen': 'https://images.unsplash.com/photo-1657069345471-c54f2432b79c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmbG9vZGVkJTIwc3RyZWV0JTIwd2F0ZXJ8ZW58MXx8fHwxNzgyNDkxNzM6fDA&ixlib=rb-4.1.0&q=80&w=400'
                },
                {
                    'titulo': 'Lluvias intensas afectan norte',
                    'descripcion': 'Varias zonas en alerta por desbordes de ríos. Miles en alerta preventiva.',
                    'imagen': 'https://images.unsplash.com/photo-1501854140801-50d01698950b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400'
                },
                {
                    'titulo': 'Precio del dólar sigue a la baja',
                    'descripcion': 'Moneda americana registra ligera caída en el mercado local.',
                    'imagen': 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400'
                },
                {
                    'titulo': 'Selección Peruana se prepara para la fecha',
                    'descripcion': 'Equipo nacional con miras al próximo desafío de eliminatorias.',
                    'imagen': 'https://images.unsplash.com/photo-1622659097509-4d56de14539e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400'
                }
            ]
            import time
            for item in default_items:
                try:
                    NoticiaLanding.objects.using('periodico_db').create(
                        titulo=item['titulo'],
                        descripcion=item['descripcion'],
                        imagen=item['imagen']
                    )
                    time.sleep(0.01)
                except Exception as e:
                    logger.error(f"Error seeding default news item: {e}")
            queryset = NoticiaLanding.objects.using('periodico_db').all()

        noticias = queryset.order_by('-fecha_creacion')
        serializer = NoticiaLandingSerializer(noticias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        # Auth check for platform admin/publisher
        if not (user.is_superuser or user.email == 'admin' or getattr(user, 'companies', None)):
            return Response(
                {'detail': 'No tienes permisos para realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        titulo = request.data.get('titulo')
        descripcion = request.data.get('descripcion')
        image_file = request.FILES.get('image')
        image_url = request.data.get('image_url')

        if not titulo or not descripcion:
            return Response(
                {'detail': 'El título y la descripción son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if image_file:
            sanitized_filename = f"landing_news/{uuid.uuid4().hex}_{image_file.name}"
            saved_path = default_storage.save(sanitized_filename, image_file)
            media_url = settings.MEDIA_URL
            if not media_url.endswith('/'):
                media_url += '/'
            image_path = f"{media_url}{saved_path}"
        elif image_url:
            image_path = image_url
        else:
            return Response(
                {'detail': 'El archivo de imagen o la URL de la imagen es obligatoria.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            noticia = NoticiaLanding.objects.using('periodico_db').create(
                titulo=titulo.strip(),
                descripcion=descripcion.strip(),
                imagen=image_path
            )
            serializer = NoticiaLandingSerializer(noticia)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating NoticiaLanding: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al guardar la noticia de landing.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NoticiaLandingDetailView(APIView):
    """
    API View to update or delete a Landing News item.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        if not (user.is_superuser or user.email == 'admin' or getattr(user, 'companies', None)):
            return Response(
                {'detail': 'No tienes permisos para realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            noticia = NoticiaLanding.objects.using('periodico_db').get(id=pk)
        except NoticiaLanding.DoesNotExist:
            return Response(
                {'detail': 'Noticia de landing no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        titulo = request.data.get('titulo')
        descripcion = request.data.get('descripcion')
        image_file = request.FILES.get('image')
        image_url = request.data.get('image_url')

        if not titulo or not descripcion:
            return Response(
                {'detail': 'El título y la descripción son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if image_file:
            sanitized_filename = f"landing_news/{uuid.uuid4().hex}_{image_file.name}"
            saved_path = default_storage.save(sanitized_filename, image_file)
            media_url = settings.MEDIA_URL
            if not media_url.endswith('/'):
                media_url += '/'
            image_path = f"{media_url}{saved_path}"
            noticia.imagen = image_path
        elif image_url:
            noticia.imagen = image_url

        try:
            from django.utils import timezone
            noticia.titulo = titulo.strip()
            noticia.descripcion = descripcion.strip()
            noticia.fecha_actualizacion = timezone.now()
            noticia.save(using='periodico_db')
            
            serializer = NoticiaLandingSerializer(noticia)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating NoticiaLanding: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al actualizar la noticia de landing.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        user = request.user
        if not (user.is_superuser or user.email == 'admin' or getattr(user, 'companies', None)):
            return Response(
                {'detail': 'No tienes permisos para realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            noticia = NoticiaLanding.objects.using('periodico_db').get(id=pk)
            noticia.delete(using='periodico_db')
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NoticiaLanding.DoesNotExist:
            return Response(
                {'detail': 'Noticia de landing no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
