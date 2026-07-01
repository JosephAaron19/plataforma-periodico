import logging
import calendar
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.core.exceptions import ValidationError

from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.plans.models.plan import Plan
from apps.purchases.models.compra import Compra
from apps.purchases.models.proveedor_pago import ProveedorPago
from apps.payments.models.pago import Pago
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.access.models.acceso_tipo import AccesoTipo
from apps.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)

AUDIT_MODULE = 'M11'  # Purchases/Payments

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return sourcedate.replace(year=year, month=month, day=day)

def add_years(sourcedate, years):
    try:
        return sourcedate.replace(year=sourcedate.year + years)
    except ValueError:
        return sourcedate.replace(year=sourcedate.year + years, day=28)

def get_plan_duration(plan_code: str, start_date):
    """
    Returns the end date based on plan periodicity/code.
    """
    code_upper = plan_code.upper()
    if "DIARIO" in code_upper:
        return start_date + timedelta(hours=24)
    elif "ANUAL" in code_upper:
        return add_years(start_date, 1)
    elif "MENSUAL" in code_upper:
        return add_months(start_date, 1)
    else:
        # Default fallback to 1 month
        return add_months(start_date, 1)

def check_user_has_active_plan(usuario_id: int, using: str = 'periodico_db') -> AccesoEdicion:
    """
    Checks if a user currently has a running, active plan subscription.
    """
    now = timezone.now()
    return AccesoEdicion.objects.using(using).filter(
        usuario_id=usuario_id,
        estado='ACTIVO',
        origen_referencia__in=['PLAN_DIARIO', 'PLAN_MENSUAL', 'PLAN_ANUAL'],
        fecha_inicio__lte=now
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=now)
    ).order_by('-fecha_inicio').first()

def get_acceso_tipo_compra(using: str = 'periodico_db') -> AccesoTipo:
    try:
        return AccesoTipo.objects.using(using).get(codigo='COMPRA', estado='ACTIVO')
    except AccesoTipo.DoesNotExist:
        raise ValidationError(
            "No existe un AccesoTipo activo con codigo='COMPRA' en pdg.atr_acceso_tipo."
        )

def create_user_plan_purchase(
    *,
    usuario,
    plan,
    payment_method: str,
    reference_number: str,
    using: str = 'periodico_db'
) -> Compra:
    """
    Creates a new plan purchase. 
    If user already has an active plan, registers it but leaves it pending activation.
    """
    if not usuario.is_active:
        raise ValidationError("El usuario no está activo.")

    if plan.estado != 'ACTIVO':
        raise ValidationError("El plan seleccionado no está activo.")

    ref_key = f"REF-{reference_number}-{plan.codigo.upper()}"

    # Idempotency check
    existing = Compra.objects.using(using).filter(referencia_interna=ref_key, usuario=usuario).first()
    if existing:
        return existing

    # Find a placeholder edition since com_compra.edi_id is NOT NULL
    edition = Edicion.objects.using(using).filter(estado='PUBLICADA').first()
    if not edition:
        edition = Edicion.objects.using(using).first()

    if not edition:
        raise ValidationError("No hay ediciones en el sistema para asociar la compra.")

    # Get mock payment provider
    try:
        proveedor = ProveedorPago.objects.using(using).get(codigo='MOCK', estado='ACTIVO')
    except ProveedorPago.DoesNotExist:
        proveedor = ProveedorPago.objects.using(using).first()

    if not proveedor:
        raise ValidationError("Proveedor de pago MOCK no configurado.")

    has_active = check_user_has_active_plan(usuario.id, using=using)

    try:
        with transaction.atomic(using=using):
            compra = Compra.objects.using(using).create(
                usuario=usuario,
                empresa_id=edition.empresa_id,
                edicion=edition,
                referencia_interna=ref_key,
                precio_unitario=plan.precio,
                monto_total=plan.precio,
                moneda=plan.moneda or 'PEN',
                estado=Compra.PENDIENTE,
                origen=Compra.ORIGEN_WEB,
                acceso_habilitado=False,
            )

            pago = Pago.objects.using(using).create(
                compra=compra,
                proveedor=proveedor,
                numero_intento=1,
                identificador_externo=reference_number,
                monto=plan.precio,
                moneda=plan.moneda or 'PEN',
                estado=Pago.CREADO,
                medio_pago=payment_method.upper(),
                mensaje_respuesta=f"Registro manual de compra de plan {plan.codigo}"
            )

        # Audit events
        AuditService.record_event(
            usuario=usuario,
            emp_id=edition.empresa_id,
            modulo=AUDIT_MODULE,
            accion='COMPRA_REALIZADA',
            entidad='com_compra',
            entidad_id=str(compra.id),
            valores_nuevos={
                'com_id': compra.id,
                'plan_codigo': plan.codigo,
                'precio': str(plan.precio),
                'estado': compra.estado
            },
            resultado='EXITOSO',
            motivo='Compra de plan iniciada exitosamente.'
        )

        if has_active:
            AuditService.record_event(
                usuario=usuario,
                emp_id=edition.empresa_id,
                modulo=AUDIT_MODULE,
                accion='COMPRA_PENDIENTE',
                entidad='com_compra',
                entidad_id=str(compra.id),
                valores_nuevos={'com_id': compra.id},
                resultado='EXITOSO',
                motivo='Compra marcada como pendiente de activación porque ya existe un plan activo.'
            )

        return compra

    except IntegrityError as e:
        logger.error(f"create_user_plan_purchase: IntegrityError al crear compra de plan: {e}")
        raise ValidationError("Error al procesar la compra de plan. Posible referencia duplicada.")

def activate_user_pending_subscriptions(usuario_id: int, using: str = 'periodico_db') -> int:
    """
    Checks if user is eligible (no active plan) and activates the first queued purchase.
    Returns 1 if a plan was activated, 0 otherwise.
    """
    now = timezone.now()

    # Verify if user already has an active plan
    has_active = check_user_has_active_plan(usuario_id, using=using)
    if has_active:
        logger.info(f"activate_user_pending_subscriptions: Usuario {usuario_id} ya tiene un plan activo (acc={has_active.id}). No se activa ninguno.")
        return 0

    # Find the first queued plan purchase
    queued = Compra.objects.using(using).filter(
        usuario_id=usuario_id,
        estado=Compra.PAGADO,
        acceso_habilitado=False
    ).filter(
        Q(referencia_interna__icontains='DIARIO') |
        Q(referencia_interna__icontains='MENSUAL') |
        Q(referencia_interna__icontains='ANUAL')
    ).order_by('fecha_creacion').first()

    if not queued:
        logger.info(f"activate_user_pending_subscriptions: Usuario {usuario_id} no tiene compras pagadas en cola.")
        return 0

    # Determine start date based on previous expired plans to maintain alignment, if recent
    previous_plan = AccesoEdicion.objects.using(using).filter(
        usuario_id=usuario_id,
        origen_referencia__in=['PLAN_DIARIO', 'PLAN_MENSUAL', 'PLAN_ANUAL']
    ).order_by('-fecha_fin').first()

    fecha_inicio = now
    if previous_plan and previous_plan.fecha_fin:
        # If it expired within the last 7 days, align exactly with expiration date to ensure continuous timeline.
        # Otherwise, start from now.
        if previous_plan.fecha_fin > now - timedelta(days=7):
            fecha_inicio = previous_plan.fecha_fin

    # Parse plan code
    ref_upper = queued.referencia_interna.upper()
    plan_code = 'PLAN_MENSUAL'
    if 'DIARIO' in ref_upper:
        plan_code = 'PLAN_DIARIO'
    elif 'ANUAL' in ref_upper:
        plan_code = 'PLAN_ANUAL'

    fecha_fin = get_plan_duration(plan_code, fecha_inicio)

    try:
        usuario = Usuario.objects.using(using).get(id=usuario_id)
        tipo_acceso = get_acceso_tipo_compra(using=using)

        with transaction.atomic(using=using):
            # Create access
            acceso = AccesoEdicion.objects.using(using).create(
                usuario=usuario,
                edicion=queued.edicion,
                compra_id=queued.id,
                tipo_acceso=tipo_acceso,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado='ACTIVO',
                origen_referencia=plan_code,
                motivo=f"Suscripción pendiente activada automáticamente por vencimiento. com_id={queued.id}."
            )

            # Set access enabled on purchase
            queued.acceso_habilitado = True
            queued.save(using=using)

        # Audit activation
        AuditService.record_event(
            usuario=usuario,
            emp_id=queued.empresa_id,
            modulo=AUDIT_MODULE,
            accion='COMPRA_ACTIVADA_AUTOMATICAMENTE',
            entidad='com_compra',
            entidad_id=str(queued.id),
            valores_nuevos={
                'com_id': queued.id,
                'acc_id': acceso.id,
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat()
            },
            resultado='EXITOSO',
            motivo='Suscripción pendiente activada exitosamente.'
        )

        # Send email notification asynchronously
        try:
            from apps.purchases.tasks.receipt_email_tasks import send_subscription_email_task
            send_subscription_email_task.delay(queued.id, 'ACTIVATED_AUTOMATICALLY')
        except Exception as email_err:
            logger.error(f"activate_user_pending_subscriptions: Error al encolar notificación de activación para compra={queued.id}: {email_err}")

        logger.info(f"activate_user_pending_subscriptions: Activada compra={queued.id} para usuario={usuario_id} (acc={acceso.id}).")
        return 1

    except Exception as e:
        logger.error(f"activate_user_pending_subscriptions: Error inesperado al activar suscripción: {e}", exc_info=True)
        return 0
