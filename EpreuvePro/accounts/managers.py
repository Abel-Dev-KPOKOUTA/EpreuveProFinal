# apps/accounts/managers.py

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User
    Gère la création d'utilisateurs avec email comme identifiant
    """
    
    use_in_migrations = True
    
    def _create_user(self, email, password, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email donné
        """
        if not email:
            raise ValueError('L\'email doit être renseigné')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée un utilisateur standard (élève)
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_student', True)
        
        # Générer un username à partir de l'email (requis par Django)
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée un superutilisateur (admin)
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_student', False)
        
        # Générer un username à partir de l'email
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)