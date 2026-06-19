import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def suspend_company_member(
    *,
    uep_id: int,
    empresa_id: int,
    solicitante: Usuario,
    motivo: str,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresa:
    """
    Suspends a company member relationship.
    Prevents leaving the company without an active administrator.
    """
    if not motivo:
        raise ValidationError({"motivo": "El motivo de la suspensión es requerido."})

    # 1. Check permissions of requester
    if not is_platform_superadmin(solicitante):
        perms = calculate_effective_permissions(solicitante.id, empresa_id)
        if 'USUARIO_GESTIONAR' not in perms:
            raise ValidationError("No tienes permisos (USUARIO_GESTIONAR) para gestionar miembros.")

    try:
        with transaction.atomic(using='periodico_db'):
            # 2. Retrieve relationship with select_for_update inside the transaction
            try:
                uep = UsuarioEmpresa.objects.using('periodico_db').select_for_update().get(
                    id=uep_id,
                    empresa_id=empresa_id
                )
            except UsuarioEmpresa.DoesNotExist:
                raise ValidationError("La relación miembro-empresa especificada no existe.")

            if uep.estado != 'ACTIVO':
                raise ValidationError(f"La relación se encuentra en estado '{uep.estado}', no se puede suspender.")

            # 3. Prevent suspending the last active administrator
            from django.db.models import Q
            now = timezone.now()
            
            is_admin = uep.roles_asignados.filter(
                rol__codigo='ADMIN_EMPRESA', 
                estado='ACTIVO',
                fecha_inicio__lte=now
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)
            ).exists()
            
            if is_admin:
                # Lock and count other active administrators in this company to prevent race conditions
                other_admins = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().filter(
                    usuario_empresa__empresa_id=empresa_id,
                    usuario_empresa__empresa__estado='ACTIVA',
                    usuario_empresa__empresa__eliminado=False,
                    rol__codigo='ADMIN_EMPRESA',
                    estado='ACTIVO',
                    fecha_inicio__lte=now,
                    usuario_empresa__estado='ACTIVO',
                    usuario_empresa__usuario__estado='ACTIVO',
                    usuario_empresa__usuario__eliminado=False
                ).filter(
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)
                ).exclude(usuario_empresa_id=uep.id)
                
                if not other_admins.exists():
                    raise ValidationError("No se puede suspender al único administrador activo de la empresa.")

            # Save previous state for logging
            estado_anterior = uep.estado
            
            # Update uep state
            uep.estado = 'SUSPENDIDO'
            uep.motivo = motivo
            uep.fecha_actualizacion = now
            uep.save(using='periodico_db')

            # Suspend active roles of this relation
            active_roles = UsuarioEmpresaRol.objects.using('periodico_db').filter(
                usuario_empresa=uep,
                estado='ACTIVO'
            )
            
            for uer in active_roles:
                uer.estado = 'SUSPENDIDO'
                uer.save(using='periodico_db')

                # Log role suspension to RolHistorial
                historial = RolHistorial(
                    usuario_empresa=uep,
                    rol=uer.rol,
                    tipo_evento='FINALIZACION_ROL',
                    motivo=f"Relación suspendida: {motivo}",
                    realizado_por=solicitante,
                    direccion_ip=ip_address
                )
                historial.save(using='periodico_db')

            # Log audit record
            AuditService.record_event(
                usuario=solicitante,
                emp_id=empresa_id,
                modulo=AuditoriaModulo.M04,
                accion='MIEMBRO_SUSPENDIDO',
                entidad='UsuarioEmpresa',
                entidad_id=str(uep.id),
                valores_anteriores={
                    "estado": estado_anterior
                },
                valores_nuevos={
                    "estado": "SUSPENDIDO",
                    "motivo": motivo
                },
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Miembro suspendido: {motivo}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uep

    except Exception as e:
        logger.error(f"Error suspending member relationship {uep_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo suspender al miembro: {str(e)}")
