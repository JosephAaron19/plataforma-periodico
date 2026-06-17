def get_client_ip(request) -> str:
    """
    Extracts client IP address safely, taking X-Forwarded-For into account.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request) -> str:
    """
    Extracts User-Agent header from request.
    """
    if not request:
        return None
    return request.META.get('HTTP_USER_AGENT')
