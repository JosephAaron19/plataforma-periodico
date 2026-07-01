import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.plans.models.plan import Plan
from apps.plans.models.plan_funcionalidad import PlanFuncionalidad

def seed_plans():
    print("Iniciando la inserción de planes reales de la Landing Page...")
    
    # 1. Plan Diario
    plan_diario, created = Plan.objects.using('periodico_db').get_or_create(
        codigo='PLAN_DIARIO',
        defaults={
            'nombre': 'Plan Diario',
            'descripcion': 'Ideal para informarte cada día',
            'precio': 0.50,
            'moneda': 'PEN',
            'periodicidad': 'PERSONALIZADO',
            'limite_usuarios': 1,
            'limite_ediciones_mes': 30,
            'limite_storage_mb': 100,
            'limite_pdf_mb': 20,
            'limite_paginas_pdf': 50,
            'es_publico': True,
            'orden': 1,
            'estado': 'ACTIVO'
        }
    )
    if not created:
        plan_diario.nombre = 'Plan Diario'
        plan_diario.descripcion = 'Ideal para informarte cada día'
        plan_diario.precio = 0.50
        plan_diario.periodicidad = 'PERSONALIZADO'
        plan_diario.es_publico = True
        plan_diario.orden = 1
        plan_diario.estado = 'ACTIVO'
        plan_diario.save(using='periodico_db')
        print("Plan Diario actualizado.")
    else:
        print("Plan Diario creado.")

    # Seed funcionalidades para Plan Diario
    PlanFuncionalidad.objects.using('periodico_db').filter(plan=plan_diario).delete()
    features_diario = [
        ("FEAT_ACCESO_DIA", "Acceso a la edición del día", "Permite leer la edición digital publicada hoy"),
        ("FEAT_LECTURA_LINEA", "Lectura en línea", "Permite leer en el visor digital sin descargar"),
        ("FEAT_MULTIDISPOSITIVO", "Desde cualquier dispositivo", "Acceso optimizado para PC, tablets y móviles")
    ]
    for code, name, desc in features_diario:
        PlanFuncionalidad.objects.using('periodico_db').create(
            plan=plan_diario,
            codigo_funcionalidad=code,
            nombre=name,
            descripcion=desc,
            habilitada=True
        )
    print("Funcionalidades para Plan Diario registradas.")

    # 2. Plan Mensual
    plan_mensual, created = Plan.objects.using('periodico_db').get_or_create(
        codigo='PLAN_MENSUAL',
        defaults={
            'nombre': 'Plan Mensual',
            'descripcion': 'Para lectores frecuentes',
            'precio': 14.50,
            'moneda': 'PEN',
            'periodicidad': 'MENSUAL',
            'limite_usuarios': 5,
            'limite_ediciones_mes': 150,
            'limite_storage_mb': 1024,
            'limite_pdf_mb': 50,
            'limite_paginas_pdf': 100,
            'es_publico': True,
            'orden': 2,
            'estado': 'ACTIVO'
        }
    )
    if not created:
        plan_mensual.nombre = 'Plan Mensual'
        plan_mensual.descripcion = 'Para lectores frecuentes'
        plan_mensual.precio = 14.50
        plan_mensual.periodicidad = 'MENSUAL'
        plan_mensual.es_publico = True
        plan_mensual.orden = 2
        plan_mensual.estado = 'ACTIVO'
        plan_mensual.save(using='periodico_db')
        print("Plan Mensual actualizado.")
    else:
        print("Plan Mensual creado.")

    # Seed funcionalidades para Plan Mensual
    PlanFuncionalidad.objects.using('periodico_db').filter(plan=plan_mensual).delete()
    features_mensual = [
        ("FEAT_ACCESO_COMPLETO", "Acceso completo a todas las ediciones", "Acceso irrestricto a publicaciones"),
        ("FEAT_HISTORIAL", "Historial de ediciones", "Acceso al catálogo histórico completo"),
        ("FEAT_LECTURA_ILIMITADA", "Lectura sin límites", "Sin límites de visualización de páginas"),
        ("FEAT_MULTIDISPOSITIVO", "Desde cualquier dispositivo", "Acceso optimizado para PC, tablets y móviles"),
        ("FEAT_SOPORTE_PRIO", "Soporte prioritario", "Atención preferente en consultas de soporte técnico")
    ]
    for code, name, desc in features_mensual:
        PlanFuncionalidad.objects.using('periodico_db').create(
            plan=plan_mensual,
            codigo_funcionalidad=code,
            nombre=name,
            descripcion=desc,
            habilitada=True
        )
    print("Funcionalidades para Plan Mensual registradas.")

    # 3. Plan Anual
    plan_anual, created = Plan.objects.using('periodico_db').get_or_create(
        codigo='PLAN_ANUAL',
        defaults={
            'nombre': 'Plan Anual',
            'descripcion': 'La mejor opción para ti',
            'precio': 129.00,
            'moneda': 'PEN',
            'periodicidad': 'ANUAL',
            'limite_usuarios': 10,
            'limite_ediciones_mes': 1000,
            'limite_storage_mb': 10240,
            'limite_pdf_mb': 100,
            'limite_paginas_pdf': 200,
            'es_publico': True,
            'orden': 3,
            'estado': 'ACTIVO'
        }
    )
    if not created:
        plan_anual.nombre = 'Plan Anual'
        plan_anual.descripcion = 'La mejor opción para ti'
        plan_anual.precio = 129.00
        plan_anual.periodicidad = 'ANUAL'
        plan_anual.es_publico = True
        plan_anual.orden = 3
        plan_anual.estado = 'ACTIVO'
        plan_anual.save(using='periodico_db')
        print("Plan Anual actualizado.")
    else:
        print("Plan Anual creado.")

    # Seed funcionalidades para Plan Anual
    PlanFuncionalidad.objects.using('periodico_db').filter(plan=plan_anual).delete()
    features_anual = [
        ("FEAT_ACCESO_COMPLETO", "Acceso completo a todas las ediciones", "Acceso irrestricto a publicaciones"),
        ("FEAT_HISTORIAL", "Historial de ediciones", "Acceso al catálogo histórico completo"),
        ("FEAT_LECTURA_ILIMITADA", "Lectura sin límites", "Sin límites de visualización de páginas"),
        ("FEAT_MULTIDISPOSITIVO", "Desde cualquier dispositivo", "Acceso optimizado para PC, tablets y móviles"),
        ("FEAT_SOPORTE_PRIO", "Soporte prioritario", "Atención preferente en consultas de soporte técnico"),
        ("FEAT_PROMO_GRATIS", "2 meses gratis", "Ahorro equivalente a dos mensualidades completas")
    ]
    for code, name, desc in features_anual:
        PlanFuncionalidad.objects.using('periodico_db').create(
            plan=plan_anual,
            codigo_funcionalidad=code,
            nombre=name,
            descripcion=desc,
            habilitada=True
        )
    print("Funcionalidades para Plan Anual registradas.")

    print("Semillero completado con éxito.")

if __name__ == '__main__':
    seed_plans()
