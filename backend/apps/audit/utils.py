import ipaddress

def get_client_ip(request) -> str:
    """
    Extracts client IP address safely behind Nginx.
    Prefer X-Real-IP set by Nginx ($remote_addr) which maps to HTTP_X_REAL_IP.
    Falls back to REMOTE_ADDR.
    Validates formatting using ipaddress.ip_address. Returns None if invalid.
    """
    if not request:
        return None
        
    ip_str = request.META.get('HTTP_X_REAL_IP')
    if not ip_str:
        ip_str = request.META.get('REMOTE_ADDR')
        
    if not ip_str:
        return None
        
    ip_str = ip_str.strip()
    
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return str(ip_obj)
    except ValueError:
        return None


def get_user_agent(request) -> str:
    """
    Extracts User-Agent header from request.
    """
    if not request:
        return None
    return request.META.get('HTTP_USER_AGENT')
