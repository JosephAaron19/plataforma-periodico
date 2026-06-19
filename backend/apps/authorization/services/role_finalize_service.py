import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

from apps.accounts.models.usuario import Usuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol_historial import RolHistorial
from apps.authorization.constants import EstadoUsuarioEmpresaRol
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def finalize_member_role(
    *,
    uep_id: int,
    emp_id: int,
    uer_id: int,
    solicitante: Usuario,
    motivo: str,
    ip_address: str = None,
    user_agent: str = None
) -> UsuarioEmpresaRol:
    """
    Finalizes a company member's role assignment.
    Verifies that we are not finalizing the last active ADMIN_EMPRESA role of the company.
    Logs to RolHistorial and AuditService.
    """
    if not motivo:
        raise ValidationError({"motivo": "El motivo de la finalización es requerido."})

    now = timezone.now()

    try:
        with transaction.atomic(using='periodico_db'):
            # 1. Retrieve and lock the target assignment
            try:
                uer = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().get(
                    id=uer_id,
                    usuario_empresa_id=uep_id,
                    usuario_empresa__empresa_id=emp_id
                )
            except UsuarioEmpresaRol.DoesNotExist:
                raise ValidationError("La asignación de rol especificada no existe para este miembro.")

            if uer.estado == EstadoUsuarioEmpresaRol.FINALIZADO:
                raise ValidationError("La asignación de rol ya se encuentra finalizada.")

            # 2. Protection for the last active administrator
            if uer.rol.codigo == 'ADMIN_EMPRESA' and uer.estado == 'ACTIVO':
                # Check if there is any other active admin role in the company
                other_admins = UsuarioEmpresaRol.objects.using('periodico_db').select_for_update().filter(
                    usuario_empresa__empresa_id=emp_id,
                    rol__codigo='ADMIN_EMPRESA',
                    estado='ACTIVO',
                    fecha_inicio__lte=now,
                    usuario_empresa__estado='ACTIVO',
                    usuario_empresa__usuario__estado='ACTIVO',
                    usuario_empresa__usuario__eliminado=False
                ).filter(
                    Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now)
                ).exclude(id=uer.id)

                if not other_admins.exists():
                    # Audit failed termination attempt
                    AuditService.record_event(
                        usuario=solicitante,
                        emp_id=emp_id,
                        modulo=AuditoriaModulo.M04,
                        accion='ULTIMO_ADMINISTRADOR_PROTEGIDO',
                        entidad='UsuarioEmpresaRol',
                        entidad_id=str(uer.id),
                        valores_anteriores={"estado": uer.estado},
                        valores_nuevos=None,
                        resultado=AuditoriaResultado.RECHAZADO,
                        motivo="Intento de finalizar el último administrador activo bloqueado.",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        throw_on_error=False
                    )
                    raise ValidationError("No se puede finalizar el último rol administrador activo de la empresa.")

            # 3. Update the record
            estado_anterior = uer.estado
            es_principal_anterior = uer.es_principal
            
            uer.estado = EstadoUsuarioEmpresaRol.FINALIZADO
            uer.fecha_fin = now
            # When finalizing, it should no longer be primary
            uer.es_principal = False
            uer.save(using='periodico_db')

            # 4. Log to RolHistorial
            historial = RolHistorial(
                usuario_empresa_id=uep_id,
                rol=uer.rol,
                tipo_evento='FINALIZACION_ROL',
                valor_anterior={"estado": estado_anterior, "es_principal": es_principal_anterior},
                valor_nuevo={"estado": "FINALIZADO", "es_principal": False},
                motivo=motivo,
                realizado_por=solicitante,
                direccion_ip=ip_address
            )
            historial.save(using='periodico_db')

            # 5. Audit event
            AuditService.record_event(
                usuario=solicitante,
                emp_id=emp_id,
                modulo=AuditoriaModulo.M04,
                accion='ROL_FINALIZADO',
                entidad='UsuarioEmpresaRol',
                entidad_id=str(uer.id),
                valores_anteriores={"estado": estado_anterior, "es_principal": es_principal_anterior},
                valores_nuevos={"estado": "FINALIZADO", "es_principal": False},
                resultado=AuditoriaResultado.EXITOSO,
                motivo=f"Rol {uer.rol.codigo} finalizado para el miembro {uep_id}. Motivo: {motivo}",
                ip_address=ip_address,
                user_agent=user_agent,
                throw_on_error=False
            )

        return uer

    except Exception as e:
        logger.error(f"Error finalizing role assignment {uer_id}: {str(e)}")
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"No se pudo finalizar el rol: {str(e)}")
