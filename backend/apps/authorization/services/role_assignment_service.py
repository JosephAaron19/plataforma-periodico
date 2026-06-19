import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.constants import EstadoUsuarioEmpresa, EstadoUsuarioEmpresaRol, TipoRol, EstadoRol
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def assign_role_to_member(
    *,
    uep_id: int,
    emp_id: int,
    role_code: str,
    is_primary: bool = False,
    start_date = None,
    end_date = None,
    solicitante: Usuario,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresaRol:
    """
    Assigns a corporate role to a member of a company.
    If the assignment already exists and is active, raises ValidationError.
    If it exists but is finalized/suspended, it reactivates it.
    If is_primary=True, unmarks other active roles of the member as primary.
    Logs to RolHistorial and AuditService.
    """
    now = timezone.now()
    
    # 1. Resolve role
    try:
        rol = Rol.objects.using('periodico_db').get(codigo=role_code)
    except Rol.DoesNotExist:
        raise ValidationError({"role_code": "El rol especificado no existe."})

    if rol.estado != EstadoRol.ACTIVO:
        raise ValidationError({"role_code": "El rol especificado se encuentra inactivo."})
        
    if rol.tipo == TipoRol.PLATAFORMA or rol.codigo == 'SUPERADMIN':
        raise ValidationError({"role_code": "No se pueden asignar roles del ámbito de plataforma."})

    # Privilege escalation check
    from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
    from apps.authorization.models.rol_permiso import RolPermiso
    if not is_platform_superadmin(solicitante):
        role_perms = set(
            RolPermiso.objects.using('periodico_db').filter(
                rol=rol,
                estado=True,
                permiso__estado=EstadoRol.ACTIVO
            ).values_list('permiso__codigo', flat=True)
        )
        requester_perms = calculate_effective_permissions(solicitante.id, emp_id)
        missing_perms = role_perms - requester_perms
        if missing_perms:
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='ESCALAMIENTO_PRIVILEGIOS_DENEGADO',
                entidad='UsuarioEmpresaRol',
                entidad_id=None,
                valores_anteriores=None,
                valores_nuevos={"requested_role": rol.codigo},
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Intento de asignar rol {rol.codigo} que contiene permisos que el solicitante no posee.",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )
            raise ValidationError({"role_code": "No puedes asignar un rol que contenga permisos que tú mismo no posees."})

    # 2. Check dates validity
    if start_date and end_date and start_date > end_date:
        raise ValidationError({"end_date": "La fecha de finalización debe ser posterior a la fecha de inicio."})

    try:
        with transaction.atomic(using='periodico_db'):
            # 3. Retrieve target member relation and lock it
            try:
                uep = UsuarioEmpresa.objects.using('periodico_db').select_for_update().get(
                    id=uep_id,
                    empresa_id=emp_id
                )
            except UsuarioEmpresa.DoesNotExist:
                raise ValidationError("El miembro especificado no existe o no pertenece a la empresa.")

            if uep.estado != EstadoUsuarioEmpresa.ACTIVO:
                raise ValidationError(f"El miembro se encuentra en estado '{uep.estado}', no se le pueden asignar roles.")

            # 4. Check for existing record to avoid unique constraint violations
            existing_uer = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().filter(
                usuario_empresa=uep,
                rol=rol
            ).first()

            if existing_uer:
                # If it's active and not expired, it is duplicate
                is_active = (existing_uer.estado == EstadoUsuarioEmpresaRol.ACTIVO)
                if is_active:
                    raise ValidationError("El miembro ya posee este rol asignado y activo.")
                
                # Reactivate existing record
                uer = existing_uer
                uer.estado = EstadoUsuarioEmpresaRol.ACTIVO
                uer.fecha_inicio = start_date or now
                uer.fecha_fin = end_date
                uer.asignado_por = solicitante
            else:
                uer = UsuarioEmpresaRol(
                    usuario_empresa=uep,
                    rol=rol,
                    estado=EstadoUsuarioEmpresaRol.ACTIVO,
                    fecha_inicio=start_date or now,
                    fecha_fin=end_date,
                    asignado_por=solicitante,
                    es_principal=False
                )

            # 5. Handle primary role logic
            if is_primary:
                # Unmark previous primary roles of this user in this company
                other_primary_roles = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().filter(
                    usuario_empresa=uep,
                    es_principal=True
                )
                for other_uer in other_primary_roles:
                    if other_uer.id != uer.id:
                        other_uer.es_principal = False
                        other_uer.save(using='periodico_db')
                        
                uer.es_principal = True
            else:
                # Ensure es_principal remains unchanged or set to False
                uer.es_principal = False

            uer.save(using='periodico_db')

            # 6. Log history
            historial = RolHistorial(
                usuario_empresa=uep,
                rol=rol,
                tipo_evento='ASIGNACION_ROL',
                valor_anterior=None if not existing_uer else {"estado": existing_uer.estado},
                valor_nuevo={"estado": "ACTIVO", "es_principal": uer.es_principal},
                motivo="Asignación administrativa de rol",
                realizado_por=solicitante,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 7. Audit event
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='ROL_ASIGNADO',
                entidad='UsuarioEmpresaRol',
                entidad_id=str(uer.id),
                valores_anteriores=None if not existing_uer else {"estado": existing_uer.estado},
                valores_nuevos={"estado": "ACTIVO", "rol": rol.codigo, "es_principal": uer.es_principal},
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Rol {rol.codigo} asignado al miembro {uep_id}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uer

    except Exception as e:
        logger.error(f"Error assigning role {role_code} to member {uep_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo asignar el rol: {str(e)}")
