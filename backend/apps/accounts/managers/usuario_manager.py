from django.contrib.auth.models import BaseUserManager

class UsuarioManager(BaseUserManager):
    """
    Custom manager for the Usuario model.
    Handles user creation and centralizes email normalization.
    """
    def create_user(self, usr_correo, password=None, **extra_fields):
        if not usr_correo:
            raise ValueError('El correo electrónico es obligatorio')
        
        email = self.normalize_email(usr_correo)
        user = self.model(usr_correo=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, usr_correo, password=None, **extra_fields):
        # Superuser defaults for local/admin operations
        extra_fields.setdefault('usr_estado', 'ACTIVO')
        extra_fields.setdefault('usr_correo_verificado', True)
        return self.create_user(usr_correo, password, **extra_fields)

    def normalize_email(self, email):
        """
        Normalize the email address by striping and lowering the string.
        """
        if not email:
            return ''
        return email.strip().lower()
