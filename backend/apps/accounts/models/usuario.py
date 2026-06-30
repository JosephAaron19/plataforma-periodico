from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from apps.accounts.managers.usuario_manager import UsuarioManager
from apps.accounts.constants import EstadoUsuario

class Usuario(AbstractBaseUser):
    # Primary Key mapped to usr_id
    id = models.BigAutoField(db_column='usr_id', primary_key=True)
    
    # Credentials & Core Auth Fields
    usr_correo = models.EmailField(db_column='usr_correo', unique=True, max_length=255)
    # AbstractBaseUser attributes mapped to DB columns
    password = models.CharField(db_column='usr_clave_hash', max_length=255)
    last_login = models.DateTimeField(db_column='usr_ultimo_acceso', null=True, blank=True)
    
    # Personal Info Columns
    nombres = models.CharField(db_column='usr_nombres', max_length=100)
    apellidos = models.CharField(db_column='usr_apellidos', max_length=100, null=True, blank=True)
    tipo_documento = models.CharField(db_column='usr_tipo_documento', max_length=20, null=True, blank=True)
    numero_documento = models.CharField(db_column='usr_numero_documento', max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(db_column='usr_telefono', max_length=20, null=True, blank=True)
    
    # Verification & Security Columns
    correo_verificado = models.BooleanField(db_column='usr_correo_verificado', default=False)
    fecha_verificacion = models.DateTimeField(db_column='usr_fecha_verificacion', null=True, blank=True)
    intentos_fallidos = models.IntegerField(db_column='usr_intentos_fallidos', default=0)
    bloqueado_hasta = models.DateTimeField(db_column='usr_bloqueado_hasta', null=True, blank=True)
    
    # Audit & Status Columns
    estado = models.CharField(db_column='usr_estado', max_length=20, default=EstadoUsuario.PENDIENTE)
    fecha_creacion = models.DateTimeField(db_column='usr_fecha_creacion', default=timezone.now)
    fecha_actualizacion = models.DateTimeField(db_column='usr_fecha_actualizacion', null=True, blank=True)
    eliminado = models.BooleanField(db_column='usr_eliminado', default=False)
    fecha_eliminacion = models.DateTimeField(db_column='usr_fecha_eliminacion', null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'usr_correo'
    EMAIL_FIELD = 'usr_correo'
    REQUIRED_FIELDS = ['nombres']

    class Meta:
        managed = False
        db_table = 'pdg"."usr_usuario'

    @property
    def is_active(self):
        """
        Dynamic active state based on user status, delete flag, and temporal locks.
        """
        if self.eliminado or self.estado != EstadoUsuario.ACTIVO:
            return False
        if self.bloqueado_hasta and self.bloqueado_hasta > timezone.now():
            return False
        return True

    @property
    def is_superuser(self):
        if self.usr_correo == 'admin':
            return True
        try:
            from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
            return UsuarioEmpresaRol.objects.using('periodico_db').filter(
                usuario_empresa__usuario=self,
                estado='ACTIVO',
                rol_id=1,  # Role ID 1 is SUPERADMIN
                fecha_inicio__lte=timezone.now()
            ).filter(
                models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=timezone.now())
            ).exists()
        except Exception:
            return False

    @property
    def is_staff(self):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        """
        Temporary permission check resolution.
        Returns is_superuser (False) since permission system is not yet mapped to the database.
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Temporary module permission check resolution.
        Returns is_superuser (False) since permission system is not yet mapped to the database.
        """
        return self.is_superuser

    def get_full_name(self):
        if self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        return self.nombres

    def get_short_name(self):
        return self.nombres

    def __str__(self):
        return self.usr_correo
