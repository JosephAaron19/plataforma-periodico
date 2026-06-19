def mask_email(email: str) -> str:
    """
    Masks an email address for safe logging.
    e.g. testregister@example.com -> te***@example.com
    """
    if not email or '@' not in email:
        return email
    try:
        parts = email.split('@')
        name = parts[0]
        domain = parts[1]
        if len(name) <= 2:
            masked_name = name + '***'
        else:
            masked_name = name[:2] + '***'
        return f"{masked_name}@{domain}"
    except Exception:
        return email
