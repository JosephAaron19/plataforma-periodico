from django.core.exceptions import ValidationError
from apps.plans.services.plan_limit_service import check_edition_limit, check_storage_limit

def assert_can_create_edition(company):
    """
    Asserts that the company has not exceeded its monthly edition creation limit.
    Raises a ValidationError with the corresponding code if the limit is reached.
    """
    res = check_edition_limit(company)
    if not res["allowed"]:
        err = ValidationError(res["message"])
        err.code = res.get("code", "PLAN_EDITION_LIMIT_REACHED")
        raise err

def assert_can_store_file(company, file_size: int):
    """
    Asserts that the company has enough storage capacity to save a file of file_size.
    Raises a ValidationError with the corresponding code if storage capacity is exceeded.
    """
    res = check_storage_limit(company, additional_bytes=file_size)
    if not res["allowed"]:
        err = ValidationError(res["message"])
        err.code = res.get("code", "PLAN_STORAGE_LIMIT_REACHED")
        raise err
