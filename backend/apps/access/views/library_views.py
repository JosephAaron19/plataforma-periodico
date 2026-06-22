from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import models
from apps.editions.models.edicion import Edicion
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.authorization.selectors.auth_selector import get_active_user_companies
from apps.authorization.services.permission_service import calculate_effective_permissions, is_platform_superadmin
from apps.access.serializers.library_serializers import LibraryEditionSerializer

class LibraryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/v1/library/
        Returns a list of all published editions that the authenticated user has access to.
        Access is determined by:
          - Edition has modality='GRATUITA'
          - User has an active AccesoEdicion record for the edition
          - User has company-level permissions (EDICION_VER) or is Platform Superadmin.
        """
        user = request.user
        now = timezone.now()

        # Check if the user is platform superadmin
        is_super = is_platform_superadmin(user)

        # Retrieve editions where user has active access
        active_access_edition_ids = AccesoEdicion.objects.using('periodico_db').filter(
            usuario=user,
            estado='ACTIVO',
            fecha_inicio__lte=now
        ).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
        ).values_list('edicion_id', flat=True)

        # Base conditions: free edition or active access record
        q_conditions = models.Q(modalidad='GRATUITA') | models.Q(id__in=active_access_edition_ids)

        if is_super:
            # Superadmin has access to editions of all active companies, no extra company filter needed
            pass
        else:
            # Check company context permissions
            company_ids_with_permission = []
            active_company_relations = get_active_user_companies(user)
            
            for rel in active_company_relations:
                company_id = rel.empresa_id
                perms = calculate_effective_permissions(user.id, company_id)
                if 'EDICION_VER' in perms:
                    company_ids_with_permission.append(company_id)
                    
            if company_ids_with_permission:
                q_conditions |= models.Q(empresa_id__in=company_ids_with_permission)

        # Retrieve published, non-deleted editions from active, non-deleted companies
        editions = Edicion.objects.using('periodico_db').select_related('empresa').filter(
            estado='PUBLICADA',
            eliminado=False,
            empresa__estado='ACTIVA',
            empresa__eliminado=False
        ).filter(q_conditions).distinct().order_by('-fecha_publicacion')

        serializer = LibraryEditionSerializer(editions, many=True)
        return Response(serializer.data)
