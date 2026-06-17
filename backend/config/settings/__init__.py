import os

# Default to development settings
django_env = os.getenv('DJANGO_ENV', 'development').lower()

if django_env == 'production':
    from .production import *
else:
    from .development import *
