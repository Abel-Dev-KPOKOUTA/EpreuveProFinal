# apps/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

# ✅ IMPORTER LE MANAGER
from .managers import UserManager


class User(AbstractUser):
    """
    Modèle Utilisateur personnalisé pour EpreuvesPro Bénin
    """
    
    # ✅ AJOUTER LE MANAGER
    objects = UserManager()
    
    # Informations de contact
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Le numéro doit être au format: '+999999999'"
            )
        ],
        verbose_name="Téléphone"
    )
    
    email = models.EmailField(
        unique=True,  # Email unique obligatoire
        verbose_name="Email"
    )
    
    # Type d'utilisateur
    is_student = models.BooleanField(default=True, verbose_name="Élève")
    is_teacher = models.BooleanField(default=False, verbose_name="Enseignant")
    
    # Informations scolaires
    school = models.CharField(max_length=100, blank=True, verbose_name="Établissement")
    class_level = models.CharField(max_length=20, blank=True, verbose_name="Classe")
    
    # Avatar
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    
    # Vérifications
    email_verified = models.BooleanField(default=False, verbose_name="Email vérifié")
    phone_verified = models.BooleanField(default=False, verbose_name="Téléphone vérifié")
    
    # FedaPay
    fedapay_customer_id = models.CharField(max_length=100, blank=True, verbose_name="ID FedaPay")
    
    # Préférences
    newsletter_subscribed = models.BooleanField(default=True, verbose_name="Newsletter")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name="Dernière activité")

    # ✅ CONFIGURATION CRUCIALE
    USERNAME_FIELD = 'email'           # Champ utilisé pour le login
    REQUIRED_FIELDS = []               # Champs obligatoires pour createsuperuser (sauf email et password)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = 'accounts_user'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.email})"
    
    def get_display_name(self):
        if self.first_name:
            return self.first_name
        return self.email.split('@')[0]


class UserActivity(models.Model):
    """Historique des activités"""
    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('download_epreuve', 'Téléchargement épreuve'),
        ('download_corrige', 'Téléchargement corrigé'),
        ('view_epreuve', 'Consultation'),
        ('purchase', 'Achat'),
        ('subscribe', 'Abonnement'),
        ('search', 'Recherche'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Utilisateur"
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    epreuve_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID Épreuve")
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activité"
        ordering = ['-timestamp']


class EmailVerification(models.Model):
    """Tokens de vérification d'email"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification'
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        
        if self.is_used:
            return False
        expiration = self.created_at + timedelta(hours=24)
        return timezone.now() < expiration