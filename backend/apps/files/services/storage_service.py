import os
import uuid
from pathlib import Path
from django.conf import settings

class StorageService:
    """
    Abstracción de almacenamiento para guardar archivos de forma segura.
    Soporta almacenamiento privado local fuera del directorio público y almacenamiento público en MEDIA_ROOT.
    """
    
    @staticmethod
    def get_private_storage_path() -> Path:
        # Directorio privado fuera de la carpeta pública de medios
        path = (settings.BASE_DIR / 'storage' / 'private').resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def save_private_file(uploaded_file, tenant_id: int, original_filename: str) -> str:
        """
        Guarda un archivo de forma privada. Genera un nombre interno aleatorio.
        Retorna la ruta relativa (clave) del archivo guardado.
        """
        private_path = StorageService.get_private_storage_path()
        tenant_dir = (private_path / f"tenant_{tenant_id}").resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext and hasattr(uploaded_file, 'name'):
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            
        random_name = f"{uuid.uuid4()}{ext}"
        target_path = (tenant_dir / random_name).resolve()
        
        # Security check: verify that target path remains inside tenant_dir
        if tenant_dir not in target_path.parents:
            raise ValueError("Intento de path traversal detectado en save_private_file.")

        while target_path.exists():
            random_name = f"{uuid.uuid4()}{ext}"
            target_path = (tenant_dir / random_name).resolve()

        with open(target_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                
        return f"tenant_{tenant_id}/{random_name}"

    @staticmethod
    def get_private_absolute_path(relative_path: str) -> Path:
        if not relative_path or '..' in relative_path or '\\' in relative_path or ':' in relative_path or relative_path.startswith('/') or relative_path.startswith('\\'):
            raise ValueError("Ruta relativa inválida o intento de path traversal.")
        private_root = StorageService.get_private_storage_path()
        abs_path = (private_root / relative_path).resolve()
        if private_root not in abs_path.parents and private_root != abs_path:
            raise ValueError("Acceso fuera del directorio privado autorizado.")
        return abs_path

    @staticmethod
    def delete_private_file(relative_path: str) -> bool:
        if not relative_path:
            return False
        try:
            abs_path = StorageService.get_private_absolute_path(relative_path)
            if abs_path.exists() and abs_path.is_file():
                os.remove(abs_path)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def save_public_file(uploaded_file, tenant_id: int, original_filename: str) -> str:
        """
        Guarda un archivo de forma pública en el directorio MEDIA_ROOT.
        Retorna la ruta relativa (clave) del archivo.
        """
        public_path = Path(settings.MEDIA_ROOT).resolve()
        tenant_dir = (public_path / f"tenant_{tenant_id}").resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext and hasattr(uploaded_file, 'name'):
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            
        random_name = f"{uuid.uuid4()}{ext}"
        target_path = (tenant_dir / random_name).resolve()
        
        # Security check: verify that target path remains inside tenant_dir
        if tenant_dir not in target_path.parents:
            raise ValueError("Intento de path traversal detectado en save_public_file.")

        while target_path.exists():
            random_name = f"{uuid.uuid4()}{ext}"
            target_path = (tenant_dir / random_name).resolve()
            
        with open(target_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                
        return f"tenant_{tenant_id}/{random_name}"

    @staticmethod
    def get_public_absolute_path(relative_path: str) -> Path:
        if not relative_path or '..' in relative_path or '\\' in relative_path or ':' in relative_path or relative_path.startswith('/') or relative_path.startswith('\\'):
            raise ValueError("Ruta relativa inválida o intento de path traversal.")
        public_root = Path(settings.MEDIA_ROOT).resolve()
        abs_path = (public_root / relative_path).resolve()
        if public_root not in abs_path.parents and public_root != abs_path:
            raise ValueError("Acceso fuera del directorio público autorizado.")
        return abs_path

    @staticmethod
    def delete_public_file(relative_path: str) -> bool:
        if not relative_path:
            return False
        try:
            abs_path = StorageService.get_public_absolute_path(relative_path)
            if abs_path.exists() and abs_path.is_file():
                os.remove(abs_path)
                return True
        except Exception:
            pass
        return False
