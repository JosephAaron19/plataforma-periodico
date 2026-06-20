from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import Http404
from apps.editions.selectors.public_edition_selectors import (
    get_public_editions, get_public_edition_by_slug
)
from apps.editions.serializers.edition_serializers import EditionPublicSerializer

class PublicEditionListView(generics.ListAPIView):
    """
    GET: Public list of published editions of active tenants.
    """
    permission_classes = [AllowAny]
    serializer_class = EditionPublicSerializer

    def get_queryset(self):
        qs = get_public_editions()
        
        # Public filtering options
        company_id = self.request.query_params.get('company_id')
        if company_id:
            qs = qs.filter(empresa_id=company_id)
            
        company_slug = self.request.query_params.get('company_slug')
        if company_slug:
            qs = qs.filter(empresa__slug=company_slug)
            
        titulo = self.request.query_params.get('titulo')
        if titulo:
            qs = qs.filter(titulo__icontains=titulo)

        # Always order public editions by publication datetime descending
        return qs.order_by('-fecha_publicacion')


class PublicEditionDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a published edition by slug.
    """
    permission_classes = [AllowAny]
    serializer_class = EditionPublicSerializer
    lookup_field = 'slug'

    def get_object(self):
        company_slug = self.kwargs.get('company_slug')
        slug = self.kwargs.get('slug')
        edition = get_public_edition_by_slug(company_slug, slug)
        if not edition:
            raise Http404("La edición especificada no existe, no está publicada o fue suspendida.")
        return edition
