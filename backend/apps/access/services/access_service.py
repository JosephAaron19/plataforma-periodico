from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.access.models.acceso_tipo import AccesoTipo
from apps.authorization.services.permission_service import calculate_effective_permissions

def can_user_read_edition(user, edition) -> bool:
    """
    Determines if a user has full reading access to an edition.
    Validates:
      - Authenticated and active user.
      - Published and non-deleted edition.
      - Active and non-deleted company.
      - At least one processed page (edp_es_actual=True, edp_estado='GENERADA') is available.
      - Access rights (free modality, active AccesoEdicion record, or company permission EDICION_VER).
    """
    if not user or not user.is_authenticated or not user.is_active:
        return False
        
    if edition.eliminado or edition.estado != 'PUBLICADA':
        return False
        
    if edition.empresa.eliminado or edition.empresa.estado != 'ACTIVA':
        return False
        
    # Check if there is at least one processed page available
    if not edition.paginas.filter(edp_es_actual=True, edp_estado='GENERADA').exists():
        return False

    # 1. Modality is free
    if edition.modalidad == 'GRATUITA':
        return True

    # 2. Existing active AccesoEdicion record
    now = timezone.now()
    active_access = AccesoEdicion.objects.using('periodico_db').filter(
        usuario=user,
        edicion=edition,
        estado='ACTIVO',
        fecha_inicio__lte=now
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
    ).exists()
    
    if active_access:
        return True

    # 3. Company permission (EDICION_VER)
    effective_perms = calculate_effective_permissions(user.id, edition.empresa_id)
    if 'EDICION_VER' in effective_perms:
        return True

    return False


def get_or_create_reading_access(user, edition) -> AccesoEdicion:
    """
    Retrieves an active reading access for the user, or creates one if the user
    is authorized via free edition status or company permissions.
    """
    now = timezone.now()
    
    # 1. Search for existing active AccesoEdicion
    access = AccesoEdicion.objects.using('periodico_db').filter(
        usuario=user,
        edicion=edition,
        estado='ACTIVO',
        fecha_inicio__lte=now
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
    ).first()
    
    if access:
        return access

    # 2. Free edition: auto-create GRATUITO access
    if edition.modalidad == 'GRATUITA':
        try:
            tipo_gratuito = AccesoTipo.objects.using('periodico_db').get(id=2)
        except AccesoTipo.DoesNotExist:
            # Fallback or create in memory if test environment doesn't have it
            tipo_gratuito = AccesoTipo.objects.using('periodico_db').create(
                id=2, codigo='GRATUITO', nombre='Gratuito', estado='ACTIVO'
            )
            
        access, created = AccesoEdicion.objects.using('periodico_db').get_or_create(
            usuario=user,
            edicion=edition,
            tipo_acceso=tipo_gratuito,
            defaults={
                'fecha_inicio': now,
                'estado': 'ACTIVO',
                'origen_referencia': 'LECTURA_GRATUITA',
                'motivo': 'Acceso automático para edición gratuita.'
            }
        )
        return access

    # 3. Permissions-based: auto-create ADMIN_TEMPORAL access
    effective_perms = calculate_effective_permissions(user.id, edition.empresa_id)
    if 'EDICION_VER' in effective_perms:
        try:
            tipo_admin = AccesoTipo.objects.using('periodico_db').get(id=5)
        except AccesoTipo.DoesNotExist:
            tipo_admin = AccesoTipo.objects.using('periodico_db').create(
                id=5, codigo='ADMIN_TEMPORAL', nombre='Acceso administrativo temporal', estado='ACTIVO'
            )
            
        access, created = AccesoEdicion.objects.using('periodico_db').get_or_create(
            usuario=user,
            edicion=edition,
            tipo_acceso=tipo_admin,
            defaults={
                'fecha_inicio': now,
                'estado': 'ACTIVO',
                'origen_referencia': 'PERMISO_VER',
                'motivo': 'Acceso automático para usuario con permisos de visualización.'
            }
        )
        return access

    raise ValidationError("El usuario no tiene acceso a esta edición.")
