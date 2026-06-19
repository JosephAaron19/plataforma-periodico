import hashlib
from apps.authorization.models.invitacion_usuario import InvitacionUsuario

def get_company_invitations_queryset(emp_id):
    """
    Returns a queryset of invitations for a given company.
    """
    return InvitacionUsuario.objects.using('periodico_db').filter(
        empresa_id=emp_id
    ).select_related('empresa', 'rol', 'invitado_por', 'usuario')

def get_invitation_by_token(plain_token: str):
    """
    Hashes the plain token and resolves it against the stored token_hash.
    Returns the InvitacionUsuario object if found, or None.
    """
    if not plain_token:
        return None
        
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()
    try:
        return InvitacionUsuario.objects.using('periodico_db').select_related(
            'empresa', 'rol', 'invitado_por', 'usuario'
        ).get(token_hash=token_hash)
    except InvitacionUsuario.DoesNotExist:
        return None
