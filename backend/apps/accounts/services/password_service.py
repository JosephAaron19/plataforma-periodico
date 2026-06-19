from django.contrib.auth.hashers import make_password, check_password as django_check_password, is_password_usable as django_is_password_usable

def hash_password(raw_password: str) -> str:
    """
    Hashes a raw password using Django's default secure hashers.
    """
    if not raw_password:
        raise ValueError("La contraseña no puede estar vacía")
    return make_password(raw_password)

def check_password(raw_password: str, hashed_password: str) -> bool:
    """
    Verifies a raw password against a hashed password.
    """
    if not raw_password or not hashed_password:
        return False
    return django_check_password(raw_password, hashed_password)

def is_password_usable(hashed_password: str) -> bool:
    """
    Checks if a hashed password value is usable for authentication.
    """
    if not hashed_password:
        return False
    return django_is_password_usable(hashed_password)
