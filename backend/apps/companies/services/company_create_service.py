import logging
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.plans.models.plan import Plan
from apps.plans.models.empresa_plan import EmpresaPlan
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def create_company(
    *,
    ruc: str,
    razon_social: str,
    nombre_comercial: str,
    slug: str,
    creado_por: Usuario,
    administrator_user_id: int,
    descripcion: str = None,
    correo: str = None,
    telefono: str = None,
    direccion: str = None,
    sitio_web: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> Empresa:
    """
    Creates a new company and all its initial associations in a single transaction.
    """
    # 1. Resolve and validate the administrator user
    try:
        admin_user = Usuario.objects.using('periodico_db').get(id=administrator_user_id)
    except Usuario.DoesNotExist:
        raise ValidationError({"administrator_user_id": "El usuario administrador seleccionado no existe."})

    if admin_user.eliminado or admin_user.estado != 'ACTIVO':
        raise ValidationError({"administrator_user_id": "El usuario administrador seleccionado no está activo."})
    if not admin_user.correo_verificado:
        raise ValidationError({"administrator_user_id": "El usuario administrador seleccionado no tiene el correo verificado."})
    if admin_user.bloqueado_hasta and admin_user.bloqueado_hasta > timezone.now():
        raise ValidationError({"administrator_user_id": "El usuario administrador seleccionado tiene un bloqueo vigente."})

    # 2. Resolve role and plan by codes (not hardcoded IDs)
    try:
        rol_admin = Rol.objects.using('periodico_db').get(codigo='ADMIN_EMPRESA', estado='ACTIVO')
    except Rol.DoesNotExist:
        raise ValidationError("El rol ADMIN_EMPRESA no existe o no está activo en el sistema.")

    try:
        plan_base = Plan.objects.using('periodico_db').get(codigo='PLAN_BASE', estado='ACTIVO')
    except Plan.DoesNotExist:
        raise ValidationError("El plan PLAN_BASE no existe o no está activo en el sistema.")

    # 3. Check for existence (avoid race conditions as much as possible before transaction)
    if Empresa.objects.using('periodico_db').filter(ruc=ruc).exists():
        raise ValidationError({"ruc": "Una empresa con este RUC ya está registrada."})
    if Empresa.objects.using('periodico_db').filter(slug=slug).exists():
        raise ValidationError({"slug": "Una empresa con este slug ya está registrada."})

    # 4. Perform atomic transaction
    try:
        with transaction.atomic(using='periodico_db'):
            # Create Empresa in 'PENDIENTE' state (PostgreSQL allowed value)
            # We document that 'PENDIENTE' is the standard initial state for a newly registered company
            # waiting for activation or validation procedures.
            empresa = Empresa(
                ruc=ruc,
                razon_social=razon_social,
                nombre_comercial=nombre_comercial,
                slug=slug,
                descripcion=descripcion,
                correo=correo,
                telefono=telefono,
                direccion=direccion,
                sitio_web=sitio_web,
                estado='PENDIENTE',
                creado_por=creado_por
            )
            empresa.save(using='periodico_db')

            # Create EmpresaIdentidad in 'BORRADOR' state
            identidad = EmpresaIdentidad(
                empresa=empresa,
                nombre_publico=nombre_comercial,
                estado='BORRADOR',
                actualizado_por=creado_por
            )
            identidad.save(using='periodico_db')

            # Create EmpresaConfiguracion in 'ACTIVA' state
            configuracion = EmpresaConfiguracion(
                empresa=empresa,
                estado='ACTIVA',
                actualizado_por=creado_por
            )
            configuracion.save(using='periodico_db')

            # Create UsuarioEmpresa active relationship
            usuario_empresa = UsuarioEmpresa(
                usuario=admin_user,
                empresa=empresa,
                es_principal=True,
                estado='ACTIVO',
                asignado_por=creado_por,
                motivo='Asignación inicial de administrador al crear la empresa'
            )
            usuario_empresa.save(using='periodico_db')

            # Create UsuarioEmpresaRol relationship with ADMIN_EMPRESA
            usuario_empresa_rol = UsuarioEmpresaRol(
                usuario_empresa=usuario_empresa,
                rol=rol_admin,
                es_principal=True,
                estado='ACTIVO',
                asignado_por=creado_por
            )
            usuario_empresa_rol.save(using='periodico_db')

            # Calculate plan end date if periodicidad is MENSUAL or ANUAL
            fecha_inicio = timezone.now()
            fecha_fin = None
            if plan_base.periodicidad == 'MENSUAL':
                fecha_fin = fecha_inicio + timedelta(days=30)
            elif plan_base.periodicidad == 'ANUAL':
                fecha_fin = fecha_inicio + timedelta(days=365)

            # Create EmpresaPlan
            empresa_plan = EmpresaPlan(
                empresa=empresa,
                plan=plan_base,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                precio_contratado=plan_base.precio,
                moneda=plan_base.moneda,
                periodicidad=plan_base.periodicidad,
                renovacion_automatica=True,
                estado='ACTIVO',
                motivo_cambio='Asignación de plan base inicial',
                asignado_por=creado_por
            )
            empresa_plan.save(using='periodico_db')

            # Prepare detail_nuevo for history
            detalle_nuevo = {
                "ruc": ruc,
                "razon_social": razon_social,
                "nombre_comercial": nombre_comercial,
                "slug": slug,
                "estado": "PENDIENTE",
                "administrador_id": admin_user.id,
                "plan_inicial": plan_base.codigo
            }

            # Create EmpresaHistorial
            historial = EmpresaHistorial(
                empresa=empresa,
                tipo_evento='CREACION',
                estado_anterior=None,
                estado_nuevo='PENDIENTE',
                motivo='Creación e inicialización de la empresa',
                detalle_anterior=None,
                detalle_nuevo=detalle_nuevo,
                realizado_por=creado_por,
                direccion_ip=ip_address,
                resultado='EXITOSO'
            )
            historial.save(using='periodico_db')

            # Record audit using AuditService under a savepoint
            # We pass throw_on_error=False to ensure audit failure doesn't break the main transaction
            AuditService.record_event(
                usuario=creado_por,
                emp_id=empresa.id,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.EMPRESA_CREADA,
                entidad='Empresa',
                entidad_id=str(empresa.id),
                valores_anteriores=None,
                valores_nuevos=detalle_nuevo,
                resultado=AuditoriaResultado.EXITOSO,
                motivo='Creación de empresa exitosa',
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

            return empresa

    except IntegrityError as ie:
        logger.error(f"IntegrityError creating company: {str(ie)}")
        # Raise control error, do not expose internal DB details
        raise ValidationError("No se pudo crear la empresa. El RUC o el slug ya se encuentra registrado.")
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        # Re-raise standard ValidationError if it already is one
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Error al crear la empresa: {str(e)}")
