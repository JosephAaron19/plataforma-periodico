from typing import Optional
from django.db.models import QuerySet
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.perfil import Perfil
from apps.accounts.models.sesion import Sesion
from apps.accounts.models.recuperacion import RecuperacionCuenta
from apps.accounts.constants import EstadoSesion, EstadoRecuperacion

def get_user_by_email(email: str) -> Optional[Usuario]:
    """
    Search for a user by their normalized email address.
    """
    if not email:
        return None
    normalized_email = email.strip().lower()
    try:
        return Usuario.objects.get(usr_correo=normalized_email)
    except Usuario.DoesNotExist:
        return None

def get_user_by_id(user_id: int) -> Optional[Usuario]:
    """
    Search for a user by id.
    """
    try:
        return Usuario.objects.get(pk=user_id)
    except Usuario.DoesNotExist:
        return None

def get_user_profile(user: Usuario) -> Optional[Perfil]:
    """
    Get the profile associated with a user.
    """
    try:
        return user.perfil
    except Perfil.DoesNotExist:
        return None

def get_active_sessions(user: Usuario) -> QuerySet[Sesion]:
    """
    Query active sessions for a user.
    """
    return Sesion.objects.filter(
        usuario=user,
        estado=EstadoSesion.ACTIVA,
        fecha_expiracion__gt=timezone.now(),
        fecha_cierre__isnull=True
    )

def get_active_recoveries(user: Usuario) -> QuerySet[RecuperacionCuenta]:
    """
    Query active recovery requests for a user.
    """
    return RecuperacionCuenta.objects.filter(
        usuario=user,
        estado=EstadoRecuperacion.SOLICITADA,
        fecha_expiracion__gt=timezone.now(),
        fecha_uso__isnull=True
    )
