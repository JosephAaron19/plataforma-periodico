from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound

from apps.authorization.selectors.member_selectors import get_company_members_queryset
from apps.authorization.services.member_suspend_service import suspend_company_member
from apps.authorization.services.member_reactivate_service import reactivate_company_member

from apps.authorization.serializers.member import CompanyMemberSerializer, MemberSuspendSerializer, CompanyMemberCreateSerializer
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission

class CompanyMemberListView(generics.ListAPIView):
    """
    GET: List all active/suspended members of a given company.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_VER'
    serializer_class = CompanyMemberSerializer

    def get_queryset(self):
        emp_id = self.kwargs.get('emp_id')
        return get_company_members_queryset(emp_id).order_by('usuario__nombres')


class CompanyMemberDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific member in the company.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_VER'
    serializer_class = CompanyMemberSerializer

    def get_object(self):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        try:
            return get_company_members_queryset(emp_id).get(id=uep_id)
        except UsuarioEmpresa.DoesNotExist:
            raise NotFound("El miembro especificado no existe.")


class CompanyMemberSuspendView(generics.GenericAPIView):
    """
    POST: Suspends a company member relationship.
    Prevents leaving the company without an active administrator.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = MemberSuspendSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            member_relation = suspend_company_member(
                uep_id=uep_id,
                empresa_id=emp_id,
                solicitante=request.user,
                motivo=serializer.validated_data['motivo'],
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyMemberSerializer(member_relation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CompanyMemberReactivateView(generics.GenericAPIView):
    """
    POST: Reactivates a suspended company member relationship.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = CompanyMemberSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            member_relation = reactivate_company_member(
                uep_id=uep_id,
                empresa_id=emp_id,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyMemberSerializer(member_relation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CompanyMemberCreateDirectView(generics.GenericAPIView):
    """
    POST: Create a user and link it directly to the company with a role (no verification email needed).
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = CompanyMemberCreateSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        role_code = serializer.validated_data['role_code']
        nombres = serializer.validated_data.get('nombres')
        apellidos = serializer.validated_data.get('apellidos')
        
        email_clean = email.strip().lower()
        
        from django.db import transaction
        from apps.accounts.models.usuario import Usuario
        from apps.accounts.services.password_service import hash_password
        from apps.accounts.models.perfil import Perfil
        from apps.companies.models.empresa import Empresa
        from apps.authorization.models.rol import Rol
        from apps.authorization.models.usuario_empresa import UsuarioEmpresa
        from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
        from apps.authorization.models.rol_historial import RolHistorial

        # Check if user already exists
        user = Usuario.objects.using('periodico_db').filter(usr_correo=email_clean, eliminado=False).first()
        if user:
            raise DRFValidationError({"email": ["El correo electrónico ya está registrado en el sistema."]})
            
        try:
            with transaction.atomic(using='periodico_db'):
                # 1. Create the base User
                user = Usuario(
                    usr_correo=email_clean,
                    nombres=nombres or email_clean.split('@')[0].capitalize(),
                    apellidos=apellidos,
                    password=hash_password(password),
                    estado='ACTIVO',
                    correo_verificado=True
                )
                user.save(using='periodico_db')
                
                # 2. Create profile
                perfil = Perfil(usuario=user, idioma='es')
                perfil.save(using='periodico_db')
                
                # Get company and role records
                empresa = get_object_or_404(Empresa.objects.using('periodico_db'), id=emp_id)
                rol = get_object_or_404(Rol.objects.using('periodico_db'), codigo=role_code)
                
                # 3. Create company relation
                uep = UsuarioEmpresa(
                    usuario=user,
                    empresa=empresa,
                    es_principal=True,
                    estado='ACTIVO',
                    asignado_por=request.user,
                    motivo='Creado directamente desde la gestión de usuarios'
                )
                uep.save(using='periodico_db')
                
                # 4. Assign role
                uer = UsuarioEmpresaRol(
                    usuario_empresa=uep,
                    rol=rol,
                    es_principal=True,
                    asignado_por=request.user,
                    estado='ACTIVO'
                )
                uer.save(using='periodico_db')
                
                # 5. Log role history
                historial = RolHistorial(
                    usuario_empresa=uep,
                    rol=rol,
                    tipo_evento='ASIGNACION_ROL',
                    motivo='Asignación de rol inicial por creación directa de usuario',
                    realizado_por=request.user,
                    direccion_ip=request.META.get('REMOTE_ADDR')
                )
                historial.save(using='periodico_db')
                
            response_serializer = CompanyMemberSerializer(uep)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            raise DRFValidationError({"detail": f"No se pudo crear el miembro: {str(e)}"})

