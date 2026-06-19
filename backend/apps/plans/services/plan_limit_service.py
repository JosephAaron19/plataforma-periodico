from django.core.exceptions import ValidationError
from apps.plans.selectors.plan_selectors import get_company_active_plan
from apps.plans.selectors.usage_selectors import (
    get_active_company_members_count,
    get_current_month_editions_count,
    get_company_storage_bytes
)

def get_company_plan_limits(company) -> dict:
    """
    Returns a dictionary of limits for the active plan of the company.
    """
    company_id = company if isinstance(company, int) else company.id
    active_plan_relation = get_company_active_plan(company_id)
    if not active_plan_relation:
        return {
            "users": 0,
            "editions": 0,
            "storage_mb": 0,
            "storage_bytes": 0,
            "pdf_mb": 0,
            "paginas_pdf": 0
        }
    
    plan = active_plan_relation.plan
    storage_mb = plan.limite_storage_mb or 0
    return {
        "users": plan.limite_usuarios,
        "editions": plan.limite_ediciones_mes,
        "storage_mb": storage_mb,
        "storage_bytes": storage_mb * 1024 * 1024,
        "pdf_mb": plan.limite_pdf_mb,
        "paginas_pdf": plan.limite_paginas_pdf
    }

def get_company_usage(company) -> dict:
    """
    Returns the current usage/consumption for a company.
    """
    company_id = company if isinstance(company, int) else company.id
    return {
        "users": get_active_company_members_count(company_id),
        "editions": get_current_month_editions_count(company_id),
        "storage_bytes": get_company_storage_bytes(company_id)
    }

def check_user_limit(company) -> dict:
    """
    Checks if the company has available slots to add/reactivate a user.
    """
    company_id = company if isinstance(company, int) else company.id
    active_plan_relation = get_company_active_plan(company_id)
    if not active_plan_relation:
        return {
            "allowed": False,
            "code": "PLAN_NOT_FOUND",
            "message": "La empresa no tiene un plan activo asignado.",
            "limit": 0,
            "used": 0
        }
    
    plan = active_plan_relation.plan
    limit = plan.limite_usuarios
    used = get_active_company_members_count(company_id)
    
    # None means unlimited
    if limit is None:
        return {
            "allowed": True,
            "limit": None,
            "used": used
        }
        
    if used >= limit:
        return {
            "allowed": False,
            "code": "PLAN_USER_LIMIT_REACHED",
            "message": f"La empresa alcanzó el límite de usuarios de su plan ({limit} usuarios).",
            "limit": limit,
            "used": used
        }
        
    return {
        "allowed": True,
        "limit": limit,
        "used": used
    }

def check_edition_limit(company) -> dict:
    """
    Checks if the company can create a new edition in the current month.
    """
    company_id = company if isinstance(company, int) else company.id
    active_plan_relation = get_company_active_plan(company_id)
    if not active_plan_relation:
        return {
            "allowed": False,
            "code": "PLAN_NOT_FOUND",
            "message": "La empresa no tiene un plan activo asignado.",
            "limit": 0,
            "used": 0
        }
        
    plan = active_plan_relation.plan
    limit = plan.limite_ediciones_mes
    used = get_current_month_editions_count(company_id)
    
    # None means unlimited
    if limit is None:
        return {
            "allowed": True,
            "limit": None,
            "used": used
        }
        
    if used >= limit:
        return {
            "allowed": False,
            "code": "PLAN_EDITION_LIMIT_REACHED",
            "message": f"La empresa alcanzó el límite de ediciones mensuales de su plan ({limit} ediciones).",
            "limit": limit,
            "used": used
        }
        
    return {
        "allowed": True,
        "limit": limit,
        "used": used
    }

def check_storage_limit(company, additional_bytes: int = 0) -> dict:
    """
    Checks if adding additional_bytes will exceed the company's storage capacity.
    """
    company_id = company if isinstance(company, int) else company.id
    active_plan_relation = get_company_active_plan(company_id)
    if not active_plan_relation:
        return {
            "allowed": False,
            "code": "PLAN_NOT_FOUND",
            "message": "La empresa no tiene un plan activo asignado.",
            "limit_bytes": 0,
            "used_bytes": 0
        }
        
    plan = active_plan_relation.plan
    limit_mb = plan.limite_storage_mb
    
    used_bytes = get_company_storage_bytes(company_id)
    
    if limit_mb is None:
        return {
            "allowed": True,
            "limit_bytes": None,
            "used_bytes": used_bytes
        }
        
    limit_bytes = limit_mb * 1024 * 1024
    if (used_bytes + additional_bytes) > limit_bytes:
        return {
            "allowed": False,
            "code": "PLAN_STORAGE_LIMIT_REACHED",
            "message": f"La empresa alcanzó el límite de almacenamiento de su plan ({limit_mb} MB).",
            "limit_bytes": limit_bytes,
            "used_bytes": used_bytes
        }
        
    return {
        "allowed": True,
        "limit_bytes": limit_bytes,
        "used_bytes": used_bytes
    }
