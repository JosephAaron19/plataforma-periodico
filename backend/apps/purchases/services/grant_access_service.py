"""
grant_access_service — concesión de acceso de lectura post-pago confirmado.

Crea un registro AccesoEdicion vinculado a la compra confirmada.
Protege contra duplicados activos para la misma (usuario, edicion).
"""
import logging
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ValidationError
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.access.models.acceso_tipo import AccesoTipo

logger = logging.getLogger(__name__)

# The access type code for purchases — must exist in pdg.atr_acceso_tipo
ACCESS_TYPE_COMPRA_CODE = 'COMPRA'


def get_acceso_tipo_compra(using: str = 'periodico_db') -> AccesoTipo:
    """
    Retrieves the AccesoTipo with code='COMPRA' from pdg.atr_acceso_tipo.
    Raises ValidationError if the catalogue record does not exist.
    """
    try:
        return AccesoTipo.objects.using(using).get(codigo=ACCESS_TYPE_COMPRA_CODE, estado='ACTIVO')
    except AccesoTipo.DoesNotExist:
        raise ValidationError(
            f"No existe un AccesoTipo activo con codigo='{ACCESS_TYPE_COMPRA_CODE}' "
            f"en pdg.atr_acceso_tipo. Verificar catálogo de tipos de acceso."
        )


def grant_purchase_access(
    *,
    usuario,
    edicion,
    compra,
    using: str = 'periodico_db'
) -> AccesoEdicion:
    """
    Creates or returns an active AccesoEdicion linked to a confirmed purchase.

    Idempotent: if an active access for (usuario, edicion) already exists
    and is linked to the same compra, returns it without creating a duplicate.

    Args:
        usuario: Usuario instance (authenticated, active).
        edicion: Edicion instance (published, processed).
        compra: Compra instance (estado='PAGADO').
        using: Database alias.

    Returns:
        AccesoEdicion — new or existing active access record.

    Raises:
        ValidationError — if AccesoTipo 'COMPRA' is not found.
    """
    now = timezone.now()

    # Guard: check for existing active access for this exact purchase
    existing = AccesoEdicion.objects.using(using).filter(
        usuario=usuario,
        edicion=edicion,
        compra_id=compra.id,
        estado='ACTIVO'
    ).first()

    if existing:
        logger.info(
            f"grant_purchase_access: acceso ya existe para "
            f"usr={usuario.id} edi={edicion.id} com={compra.id} (acc={existing.id}). "
            f"Retornando existente."
        )
        return existing

    # Also guard: any active access for (usuario, edicion) regardless of purchase
    # to avoid granting duplicate access when re-confirming
    any_active = AccesoEdicion.objects.using(using).filter(
        usuario=usuario,
        edicion=edicion,
        estado='ACTIVO',
        fecha_inicio__lte=now
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=now)
    ).first()

    if any_active:
        logger.info(
            f"grant_purchase_access: acceso activo genérico ya existe para "
            f"usr={usuario.id} edi={edicion.id} (acc={any_active.id}). Retornando existente."
        )
        return any_active

    tipo_acceso = get_acceso_tipo_compra(using=using)

    # Determine expiry date (fecha_fin) for subscriptions
    ref = (compra.referencia_interna or '').upper()
    fecha_fin = None
    origen_ref = 'COMPRA_INDIVIDUAL'
    motivo_txt = f"Acceso otorgado por compra confirmada com_id={compra.id}."

    import calendar
    from datetime import timedelta

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

    if "DIARIO" in ref:
        fecha_fin = now + timedelta(hours=24)
        origen_ref = 'PLAN_DIARIO'
        motivo_txt = f"Suscripción Plan Diario activa por 24 horas. com_id={compra.id}."
    elif "MENSUAL" in ref:
        fecha_fin = add_months(now, 1)
        origen_ref = 'PLAN_MENSUAL'
        motivo_txt = f"Suscripción Plan Mensual activa por 1 mes. com_id={compra.id}."
    elif "ANUAL" in ref:
        fecha_fin = add_years(now, 1)
        origen_ref = 'PLAN_ANUAL'
        motivo_txt = f"Suscripción Plan Anual activa por 1 año. com_id={compra.id}."

    try:
        acceso = AccesoEdicion.objects.using(using).create(
            usuario=usuario,
            edicion=edicion,
            compra_id=compra.id,
            tipo_acceso=tipo_acceso,
            fecha_inicio=now,
            fecha_fin=fecha_fin,
            estado='ACTIVO',
            origen_referencia=origen_ref,
            motivo=motivo_txt
        )
        logger.info(
            f"grant_purchase_access: acceso creado acc={acceso.id} "
            f"usr={usuario.id} edi={edicion.id} com={compra.id}."
        )
        return acceso
    except IntegrityError as e:
        # Race condition: another request granted access simultaneously
        logger.warning(
            f"grant_purchase_access: IntegrityError al crear acceso "
            f"usr={usuario.id} edi={edicion.id} com={compra.id}: {e}. "
            f"Buscando registro existente."
        )
        existing = AccesoEdicion.objects.using(using).filter(
            usuario=usuario,
            edicion=edicion,
            compra_id=compra.id,
            estado='ACTIVO'
        ).first()
        if existing:
            return existing
        raise
