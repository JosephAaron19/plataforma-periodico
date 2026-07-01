import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db import connections
with connections['periodico_db'].cursor() as cursor:
    cursor.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_pla_periodicidad'")
    print(cursor.fetchone())
