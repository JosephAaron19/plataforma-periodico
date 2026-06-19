from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission, IsPlatformSuperadmin
from apps.plans.selectors.plan_selectors import get_active_plans, get_plan_by_code, get_company_active_plan
from apps.plans.services.plan_limit_service import get_company_usage, get_company_plan_limits
from apps.plans.serializers.plan import PlanSerializer
from apps.plans.serializers.company_plan import CompanyPlanSerializer
from apps.plans.serializers.plan_usage import PlanUsageSerializer
from apps.plans.serializers.plan_change import PlanChangeSerializer
from apps.plans.services.plan_change_service import change_company_plan
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

class PlanListView(generics.ListAPIView):
    """
    GET: List active and public plans.
    
    API Contract (Option A: Catálogo sin paginación):
    - This catalog is static and small (typically 3-5 tiers).
    - It always returns a flat JSON array directly, without page wrappers.
    - Paginating here is intentionally disabled to ease comparison grid rendering on frontend.
    """
    permission_classes = [AllowAny]
    serializer_class = PlanSerializer
    pagination_class = None

    def get_queryset(self):
        return get_active_plans()

class PlanDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PlanSerializer
    lookup_field = 'plan_code'

    def get_object(self):
        plan_code = self.kwargs.get('plan_code')
        return get_plan_by_code(plan_code)

class CompanyPlanDetailView(generics.GenericAPIView):
    permission_classes = [HasCompanyAccess]
    serializer_class = CompanyPlanSerializer

    def get(self, request, emp_id):
        active_plan_relation = get_company_active_plan(emp_id)
        if not active_plan_relation:
            return Response({"detail": "La empresa no tiene un plan activo asignado."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(active_plan_relation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyPlanUsageView(generics.GenericAPIView):
    permission_classes = [HasCompanyPermission]
    required_permission = 'EMPRESA_VER'
    serializer_class = PlanUsageSerializer

    def get(self, request, emp_id):
        active_plan_relation = get_company_active_plan(emp_id)
        if not active_plan_relation:
            return Response({"detail": "La empresa no tiene un plan activo asignado."}, status=status.HTTP_404_NOT_FOUND)

        plan = active_plan_relation.plan
        limits = get_company_plan_limits(emp_id)
        usage = get_company_usage(emp_id)

        users_limit = limits["users"]
        users_used = usage["users"]
        users_avail = (users_limit - users_used) if users_limit is not None else None

        editions_limit = limits["editions"]
        editions_used = usage["editions"]
        editions_avail = (editions_limit - editions_used) if editions_limit is not None else None

        storage_limit_bytes = limits["storage_bytes"]
        storage_used_bytes = usage["storage_bytes"]
        storage_avail_bytes = (storage_limit_bytes - storage_used_bytes) if storage_limit_bytes is not None else None

        data = {
            "plan": {
                "code": plan.codigo,
                "name": plan.nombre
            },
            "users": {
                "limit": users_limit,
                "used": users_used,
                "available": users_avail
            },
            "editions": {
                "limit": editions_limit,
                "used": editions_used,
                "available": editions_avail
            },
            "storage": {
                "limit_bytes": storage_limit_bytes,
                "used_bytes": storage_used_bytes,
                "available_bytes": storage_avail_bytes
            }
        }
        
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CompanyPlanChangeView(generics.GenericAPIView):
    permission_classes = [IsPlatformSuperadmin]
    serializer_class = PlanChangeSerializer

    def post(self, request, emp_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_code = serializer.validated_data['plan_code']
        reason = serializer.validated_data['reason']

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        try:
            new_relation = change_company_plan(
                empresa_id=emp_id,
                plan_code=plan_code,
                reason=reason,
                solicitante=request.user,
                ip_address=ip_address
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        # Retrieve usage and construct warning messages if there's overconsumption
        usage = get_company_usage(emp_id)
        new_plan = new_relation.plan
        warnings = []

        if new_plan.limite_usuarios is not None and usage["users"] > new_plan.limite_usuarios:
            warnings.append(f"El consumo actual de usuarios ({usage['users']}) excede el nuevo límite ({new_plan.limite_usuarios}).")

        if new_plan.limite_ediciones_mes is not None and usage["editions"] > new_plan.limite_ediciones_mes:
            warnings.append(f"El consumo actual de ediciones mensuales ({usage['editions']}) excede el nuevo límite ({new_plan.limite_ediciones_mes}).")

        new_plan_storage_bytes = (new_plan.limite_storage_mb * 1024 * 1024) if new_plan.limite_storage_mb is not None else None
        if new_plan_storage_bytes is not None and usage["storage_bytes"] > new_plan_storage_bytes:
            warnings.append(f"El consumo actual de almacenamiento ({usage['storage_bytes'] / (1024 * 1024):.2f} MB) excede el nuevo límite ({new_plan.limite_storage_mb} MB).")

        response_serializer = CompanyPlanSerializer(new_relation)
        res_data = response_serializer.data
        res_data["warnings"] = warnings
        
        return Response(res_data, status=status.HTTP_200_OK)
