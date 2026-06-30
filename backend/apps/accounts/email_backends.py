import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property

class UnverifiedEmailBackend(SMTPBackend):
    """
    Custom SMTP Email Backend that bypasses SSL certificate verification.
    WARNING: Only use this for local development or troubleshooting SSL issues.
    Do NOT use this backend in production environments.
    """
    @cached_property
    def ssl_context(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
