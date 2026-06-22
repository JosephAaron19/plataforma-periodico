from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_pagina import EdicionPagina
from apps.files.services.storage_service import StorageService

class PublicSamplePageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, company_slug, edition_slug, page_number):
        """
        GET /api/v1/public/editions/{company_slug}/{edition_slug}/sample/pages/{page_number}/
        Allows anyone (including guest users) to retrieve preview/sample pages of a published edition.
        Limits access strictly to 1 <= page_number <= paginas_muestra.
        """
        # 1. Look up published edition matching company & edition slugs
        try:
            edition = Edicion.objects.using('periodico_db').select_related('empresa').get(
                slug=edition_slug,
                empresa__slug=company_slug,
                eliminado=False,
                estado='PUBLICADA',
                empresa__estado='ACTIVA',
                empresa__eliminado=False
            )
        except Edicion.DoesNotExist:
            return Response(
                {"error": "La edición especificada no existe, no está publicada o su empresa editora no se encuentra activa."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Check if sample pages are enabled
        if not edition.permite_muestra or not edition.paginas_muestra:
            return Response(
                {"error": "Esta edición no permite visualización de páginas de muestra."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Check requested page number against the configured limits (Anti-IDOR / Anti-bypass)
        if page_number <= 0 or page_number > edition.paginas_muestra:
            return Response(
                {"error": "La página solicitada se encuentra fuera del rango de muestra autorizado para esta edición."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Find page record
        try:
            page = EdicionPagina.objects.using('periodico_db').select_related('archivo').get(
                edicion=edition,
                edp_numero_pagina=page_number,
                edp_es_actual=True,
                edp_estado='GENERADA'
            )
        except EdicionPagina.DoesNotExist:
            return Response(
                {"error": f"La página {page_number} no se encuentra disponible para visualización."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 5. Serve the private page image directly via FileResponse
        try:
            file_path = StorageService.get_private_absolute_path(page.archivo.ruta_storage)
            if not file_path.exists() or not file_path.is_file():
                return Response(
                    {"error": "El archivo físico de la página no está disponible en almacenamiento."},
                    status=status.HTTP_404_NOT_FOUND
                )

            return FileResponse(open(file_path, 'rb'), content_type='image/jpeg')
        except Exception as e:
            return Response(
                {"error": f"Error al servir la página de muestra: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
