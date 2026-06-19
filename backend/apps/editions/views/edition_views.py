from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.authorization.permissions.drf_permissions import (
    IsAuthenticatedAndActive, HasCompanyPermission, HasAnyCompanyPermission
)
from apps.plans.permissions.has_plan_feature import HasPlanFeature
from apps.plans.permissions.within_plan_limit import WithinPlanLimit
from apps.editions.selectors.edition_selectors import (
    get_company_editions, get_company_edition_by_id
)
from apps.editions.serializers.edition_serializers import (
    EditionListSerializer, EditionDetailSerializer,
    EditionCreateSerializer, EditionUpdateSerializer,
    EditionScheduleSerializer
)
from apps.editions.services.edition_create_service import create_edition
from apps.editions.services.edition_update_service import update_edition
from apps.editions.services.edition_schedule_service import schedule_publication
from apps.editions.services.edition_publish_service import publish_edition
from apps.editions.services.edition_suspend_service import suspend_edition
from apps.editions.services.edition_reactivate_service import reactivate_edition

class CompanyEditionListCreateView(generics.GenericAPIView):
    """
    GET: List editions for a company with filters, searches and pagination.
    POST: Create a draft edition inside plan limits.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            # Create requires RBAC permission + Plan Feature + Plan Limits
            return [IsAuthenticatedAndActive(), HasCompanyPermission(), HasPlanFeature(), WithinPlanLimit()]
        return [IsAuthenticatedAndActive(), HasCompanyPermission()]

    required_permission = 'EDICION_VER'  # Base for GET
    # POST required permissions/limits
    required_plan_feature = 'EDICION_CREAR'
    required_plan_limit = 'editions'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EditionCreateSerializer
        return EditionListSerializer

    def get_queryset(self):
        company_id = self.kwargs.get('emp_id')
        qs = get_company_editions(company_id)

        # 1. State Filter
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        # 2. Search by Title
        titulo = self.request.query_params.get('titulo')
        if titulo:
            qs = qs.filter(titulo__icontains=titulo)

        # 3. Date range filter
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        if fecha_inicio:
            qs = qs.filter(fecha_edicion__gte=fecha_inicio)
        
        fecha_fin = self.request.query_params.get('fecha_fin')
        if fecha_fin:
            qs = qs.filter(fecha_edicion__lte=fecha_fin)

        # 4. Ordering
        allowed_ordering = {
            'fecha_edicion', '-fecha_edicion',
            'titulo', '-titulo',
            'fecha_publicacion', '-fecha_publicacion',
            'fecha_creacion', '-fecha_creacion'
        }
        ordering = self.request.query_params.get('ordering', '-fecha_edicion')
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-fecha_edicion')

        return qs

    def get(self, request, emp_id):
        # Override get for list view with permissions
        # Make sure that POST permission attributes don't taint GET
        self.required_permission = 'EDICION_VER'
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, emp_id):
        # Override required_permission dynamically for POST checking
        self.required_permission = 'EDICION_CREAR'
        self.check_permissions(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get client IP address
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = create_edition(
                empresa_id=int(emp_id),
                creador=request.user,
                data=serializer.validated_data,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class CompanyEditionDetailUpdateView(generics.GenericAPIView):
    """
    GET: Retrieve details of an active edition of a company.
    PATCH: Update allowed fields of the edition.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'EDICION_VER'

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return EditionUpdateSerializer
        return EditionDetailSerializer

    def get_object(self):
        company_id = self.kwargs.get('emp_id')
        edition_id = self.kwargs.get('edi_id')
        edition = get_company_edition_by_id(company_id, edition_id)
        if not edition:
            raise Http404("La edición no existe.")
        return edition

    def get(self, request, emp_id, edi_id):
        self.required_permission = 'EDICION_VER'
        self.check_permissions(request)
        edition = self.get_object()
        serializer = self.get_serializer(edition)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, emp_id, edi_id):
        self.required_permission = 'EDICION_EDITAR'
        self.check_permissions(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = update_edition(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                data=serializer.validated_data,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class CompanyEditionScheduleView(generics.GenericAPIView):
    """
    POST: Schedule publication of an edition.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission, HasPlanFeature]
    required_permission = 'EDICION_PUBLICAR'
    required_plan_feature = 'EDICION_PUBLICAR'
    serializer_class = EditionScheduleSerializer

    def post(self, request, emp_id, edi_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = schedule_publication(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                scheduled_at=serializer.validated_data['scheduled_at'],
                timezone_name=serializer.validated_data['timezone'],
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class CompanyEditionPublishView(generics.GenericAPIView):
    """
    POST: Immediately publish an edition.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission, HasPlanFeature]
    required_permission = 'EDICION_PUBLICAR'
    required_plan_feature = 'EDICION_PUBLICAR'

    def post(self, request, emp_id, edi_id):
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = publish_edition(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class CompanyEditionSuspendView(generics.GenericAPIView):
    """
    POST: Suspend a published edition.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'EDICION_SUSPENDER'

    def post(self, request, emp_id, edi_id):
        reason = request.data.get('reason')
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = suspend_edition(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                reason=reason,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class CompanyEditionReactivateView(generics.GenericAPIView):
    """
    POST: Reactivate a suspended edition (returns it to PUBLICADA or BORRADOR).
    """
    permission_classes = [IsAuthenticatedAndActive, HasAnyCompanyPermission]
    required_permissions = ['EDICION_PUBLICAR', 'EDICION_SUSPENDER']

    def post(self, request, emp_id, edi_id):
        target_state = request.data.get('target_state', 'PUBLICADA')
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            edition = reactivate_edition(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                target_state=target_state,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except DjangoValidationError as de:
            raise ValidationError({"detail": de.message})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
