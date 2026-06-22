from django.core.management.base import BaseCommand, CommandError
from django.db import connections

class Command(BaseCommand):
    help = 'Validates connection to the external PostgreSQL database and checks the schema pdg integrity (exactly 54 tables and 6 accounts tables).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== INICIANDO VALIDACION MANUAL DEL ESQUEMA EXTERNO ==="))
        
        db_alias = 'periodico_db'
        if db_alias not in connections:
            raise CommandError(f"El alias de base de datos '{db_alias}' no está configurado.")
            
        conn = connections[db_alias]
        
        try:
            # Force read-only transaction state on the connection/cursor
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY;")
                
                # 1. Validate total table count in schema 'pdg'
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'pdg' 
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                )
                tables = [row[0] for row in cursor.fetchall()]
                table_count = len(tables)
                
                self.stdout.write(f"Total de tablas encontradas en esquema 'pdg': {table_count}")
                
                if table_count != 54:
                    raise CommandError(
                        f"Inconsistencia de esquema: Se encontraron {table_count} tablas en vez de las 54 esperadas."
                    )
                
                # 2. Check existence of the 6 accounts tables
                expected_tables = {
                    'usr_usuario',
                    'prf_perfil',
                    'ses_sesion',
                    'rec_recuperacion_cuenta',
                    'ina_intento_acceso',
                    'ver_verificacion_correo'
                }
                
                found_expected = set(tables).intersection(expected_tables)
                missing_tables = expected_tables - found_expected
                
                if missing_tables:
                    raise CommandError(
                        f"Tablas del módulo 'accounts' faltantes en el esquema 'pdg': {', '.join(missing_tables)}"
                    )
                
                self.stdout.write(self.style.SUCCESS("[OK] Las 6 tablas del modulo 'accounts' estan presentes."))
                self.stdout.write(self.style.SUCCESS("[OK] Se encontraron exactamente las 54 tablas del esquema."))
                self.stdout.write(self.style.SUCCESS("=== VALIDACION DE ESQUEMA EXTERNO EXITOSA ==="))
                
        except Exception as e:
            raise CommandError(f"Error durante la validación del esquema: {str(e)}")
