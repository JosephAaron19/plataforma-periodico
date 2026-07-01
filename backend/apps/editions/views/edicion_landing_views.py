import logging
import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings
from apps.editions.models.edicion_landing import EdicionLanding
from apps.editions.serializers.edicion_landing import EdicionLandingSerializer

logger = logging.getLogger(__name__)

class EdicionLandingListCreateView(APIView):
    """
    API View to retrieve and create Landing Editions (only images).
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        editions = EdicionLanding.objects.using('periodico_db').all().order_by('orden', '-fecha_creacion')
        serializer = EdicionLandingSerializer(editions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        # Auth check for platform admin/publisher
        if not (user.is_superuser or user.email == 'admin' or getattr(user, 'companies', None)):
            return Response(
                {'detail': 'No tienes permisos para realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        image_file = request.FILES.get('image')
        image_url = request.data.get('image_url')
        orden = request.data.get('orden', 0)

        if image_file:
            sanitized_filename = f"landing_editions/{uuid.uuid4().hex}_{image_file.name}"
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
            edicion_landing = EdicionLanding.objects.using('periodico_db').create(
                imagen=image_path,
                orden=int(orden)
            )
            serializer = EdicionLandingSerializer(edicion_landing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating EdicionLanding: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al guardar la edición de landing.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EdicionLandingDetailView(APIView):
    """
    API View to delete a Landing Edition.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        user = request.user
        if not (user.is_superuser or user.email == 'admin' or getattr(user, 'companies', None)):
            return Response(
                {'detail': 'No tienes permisos para realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            ed = EdicionLanding.objects.using('periodico_db').get(id=pk)
            ed.delete(using='periodico_db')
            return Response(status=status.HTTP_204_NO_CONTENT)
        except EdicionLanding.DoesNotExist:
            return Response(
                {'detail': 'Edición de landing no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
