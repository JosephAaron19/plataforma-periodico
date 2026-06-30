import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.files.models.archivo import Archivo

class Command(BaseCommand):
    help = "Seeds the database with Amazonia Diario company and its mock editions"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Amazonia Diario...")

        # 1. Get creator user
        user = Usuario.objects.using('periodico_db').filter(usr_correo='admin').first()
        if not user:
            user = Usuario.objects.using('periodico_db').first()
        if not user:
            self.stdout.write(self.style.ERROR("No user found in the database to associate as creator!"))
            return

        # 2. Get or create Empresa
        empresa, created = Empresa.objects.using('periodico_db').get_or_create(
            slug="amazonia-diario",
            defaults={
                "ruc": "20999999999",
                "razon_social": "Amazonia Diario S.A.C.",
                "nombre_comercial": "Amazonia Diario",
                "descripcion": "El periódico líder de la región amazónica peruana, con información veraz y oportuna.",
                "correo": "contacto@amazoniadiario.pe",
                "telefono": "+51 999 888 777",
                "direccion": "Av. Interoceánica 456, Puerto Maldonado, Madre de Dios",
                "sitio_web": "www.amazoniadiario.pe",
                "estado": "ACTIVA",
                "fecha_activacion": timezone.now(),
                "creado_por": user,
                "eliminado": False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Empresa created: {empresa}"))
        else:
            # Ensure it is active
            if empresa.estado != "ACTIVA":
                empresa.estado = "ACTIVA"
                empresa.save(using='periodico_db')
            self.stdout.write(f"Empresa already exists: {empresa}")

        # 3. Create mock editions
        ediciones_info = [
            {
                "codigo": "EDI-1254",
                "titulo": "Jóvenes lideran iniciativas ambientales",
                "fecha_edicion": datetime.date(2024, 5, 11),
                "precio": 0.50,
                "paginas": 16,
                "tamano": 10542310, # ~10 MB
                "slug": "jovenes-lideran-iniciativas-ambientales-1254",
                "cover_img": "mock_cover_1254.png"
            },
            {
                "codigo": "EDI-1255",
                "titulo": "Productores impulsan el cacao amazónico",
                "fecha_edicion": datetime.date(2024, 5, 12),
                "precio": 0.50,
                "paginas": 20,
                "tamano": 14210340, # ~13.5 MB
                "slug": "productores-impulsan-el-cacao-amazonico-1255",
                "cover_img": "mock_cover_1255.png"
            },
            {
                "codigo": "EDI-1256",
                "titulo": "Celebran el día de la madre en toda la región",
                "fecha_edicion": datetime.date(2024, 5, 13),
                "precio": 0.50,
                "paginas": 24,
                "tamano": 18230550, # ~17.4 MB
                "slug": "celebran-el-dia-de-la-madre-en-toda-la-region-1256",
                "cover_img": "mock_cover_1256.png"
            },
            {
                "codigo": "EDI-1257",
                "titulo": "Proyectos de infraestructura avanzan",
                "fecha_edicion": datetime.date(2024, 5, 14),
                "precio": 0.50,
                "paginas": 18,
                "tamano": 12560700, # ~12 MB
                "slug": "proyectos-de-infraestructura-avanzan-1257",
                "cover_img": "mock_cover_1257.png"
            },
            {
                "codigo": "EDI-1258",
                "titulo": "Impulsan desarrollo sostenible en la región amazónica",
                "fecha_edicion": datetime.date(2024, 5, 15),
                "precio": 0.50,
                "paginas": 24,
                "tamano": 19542000, # ~18.6 MB
                "slug": "impulsan-desarrollo-sostenible-en-la-region-amazonica-1258",
                "cover_img": "mock_cover_1258.png",
                "es_destacada": True
            }
        ]

        for info in ediciones_info:
            edicion, ed_created = Edicion.objects.using('periodico_db').get_or_create(
                codigo=info["codigo"],
                empresa=empresa,
                defaults={
                    "titulo": info["titulo"],
                    "slug": info["slug"],
                    "descripcion_corta": f"Edición diaria de Amazonia Diario del {info['fecha_edicion'].strftime('%d de %B, %Y')}.",
                    "descripcion_larga": f"Detalle completo de la Edición {info['codigo']}. Mantente informado de los acontecimientos locales y regionales.",
                    "fecha_edicion": info["fecha_edicion"],
                    "fecha_publicacion": timezone.make_aware(datetime.datetime.combine(info["fecha_edicion"], datetime.time(6, 0))),
                    "modalidad": "PAGO",
                    "precio": info["precio"],
                    "moneda": "PEN",
                    "numero_paginas": info["paginas"],
                    "es_destacada": info.get("es_destacada", False),
                    "permite_compra": True,
                    "permite_muestra": True,
                    "paginas_muestra": 2,
                    "estado": "PUBLICADA",
                    "creado_por": user,
                    "eliminado": False,
                }
            )

            if ed_created:
                self.stdout.write(self.style.SUCCESS(f"Edition created: {edicion.titulo} ({edicion.codigo})"))
            else:
                self.stdout.write(f"Edition already exists: {edicion.titulo} ({edicion.codigo})")

            # 4. Create mock files (PORTADA and PDF) if they don't exist
            # Cover Image
            cover_file, cover_file_created = Archivo.objects.using('periodico_db').get_or_create(
                nombre_interno=f"amazonia_{info['codigo']}_cover",
                defaults={
                    "empresa": empresa,
                    "creado_por": user,
                    "nombre_original": info["cover_img"],
                    "extension": "png",
                    "tipo_mime": "image/png",
                    "tamano_bytes": 124500,
                    "hash_sha256": "mockhash_cover_" + info["codigo"],
                    "ruta_storage": f"covers/amazonia_{info['codigo']}.png",
                    "proveedor_storage": "LOCAL",
                    "contenedor": "media",
                    "es_publico": True,
                    "estado": "DISPONIBLE",
                    "eliminado": False
                }
            )

            # Associate Cover to Edition
            EdicionArchivo.objects.using('periodico_db').get_or_create(
                edicion=edicion,
                archivo=cover_file,
                tipo_archivo="PORTADA",
                defaults={
                    "empresa": empresa,
                    "es_actual": True,
                    "estado": "ACTIVO",
                    "asignado_por": user
                }
            )

            # PDF File
            pdf_file, pdf_file_created = Archivo.objects.using('periodico_db').get_or_create(
                nombre_interno=f"amazonia_{info['codigo']}_pdf",
                defaults={
                    "empresa": empresa,
                    "creado_por": user,
                    "nombre_original": f"amazonia_{info['codigo']}.pdf",
                    "extension": "pdf",
                    "tipo_mime": "application/pdf",
                    "tamano_bytes": info["tamano"],
                    "hash_sha256": "mockhash_pdf_" + info["codigo"],
                    "ruta_storage": f"pdfs/amazonia_{info['codigo']}.pdf",
                    "proveedor_storage": "LOCAL",
                    "contenedor": "media",
                    "es_publico": False,
                    "estado": "DISPONIBLE",
                    "eliminado": False
                }
            )

            # Associate PDF to Edition
            EdicionArchivo.objects.using('periodico_db').get_or_create(
                edicion=edicion,
                archivo=pdf_file,
                tipo_archivo="PDF_ORIGINAL",
                defaults={
                    "empresa": empresa,
                    "es_actual": True,
                    "estado": "ACTIVO",
                    "asignado_por": user
                }
            )

        self.stdout.write(self.style.SUCCESS("Database seeding completed for Amazonia Diario!"))
