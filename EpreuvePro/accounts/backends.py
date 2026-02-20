# apps/accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authentification avec email OU téléphone + mot de passe
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        username peut être un email ou un numéro de téléphone
        """
        if username is None or password is None:
            return None
        
        try:
            # Chercher par email OU par téléphone
            user = User.objects.get(
                Q(email__iexact=username) | 
                Q(phone=username)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Si plusieurs users ont le même téléphone (erreur de données)
            user = User.objects.filter(phone=username).first()
        
        # Vérifier le mot de passe
        if user.check_password(password):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None