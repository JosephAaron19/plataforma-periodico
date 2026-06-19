from apps.files.models.archivo import Archivo

def validate_company_file_reference(arc_id, emp_id):
    """
    Validates that a file reference (arc_id) exists, belongs specifically to the
    given company (emp_id), is in state 'DISPONIBLE', and is not marked as deleted.
    
    Returns True if valid, False otherwise.
    """
    if not arc_id:
        return True
        
    try:
        archivo = Archivo.objects.get(id=arc_id)
        
        # Check that it belongs to this company specifically
        if archivo.empresa_id != emp_id:
            return False
            
        # Check active status and not deleted
        if archivo.estado != 'DISPONIBLE' or archivo.eliminado:
            return False
            
        return True
    except Archivo.DoesNotExist:
        return False
