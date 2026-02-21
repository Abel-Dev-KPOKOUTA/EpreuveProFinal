from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta

# ✅ IMPORTER LE MANAGER
from .managers import UserManager


class User(AbstractUser):
    """
    Modèle Utilisateur personnalisé pour EpreuvesPro Bénin
    Étend le modèle Django par défaut avec des champs spécifiques
    """
    
    # ✅ AJOUTER LE MANAGER
    objects = UserManager()
    
    # Supprimer le champ username des champs obligatoires
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    # Informations de contact
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        error_messages={
            'unique': "Cet email est déjà utilisé par un autre compte."
        }
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Le numéro doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
            )
        ],
        verbose_name="Téléphone",
        help_text="Numéro WhatsApp pour les notifications"
    )
    
    # Type d'utilisateur
    is_student = models.BooleanField(
        default=True, 
        verbose_name="Élève",
        help_text="Cocher si l'utilisateur est un élève"
    )
    
    is_teacher = models.BooleanField(
        default=False, 
        verbose_name="Enseignant",
        help_text="Cocher si l'utilisateur est un enseignant"
    )
    
    # Informations scolaires
    school = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Établissement scolaire",
        help_text="Nom de l'école ou du collège/lycée"
    )
    
    class_level = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name="Classe",
        help_text="Ex: 6ème, 3ème, Terminale..."
    )
    
    # Avatar
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo de profil",
        help_text="Image de profil (max 2Mo)"
    )
    
    # Vérifications
    email_verified = models.BooleanField(
        default=False, 
        verbose_name="Email vérifié",
        help_text="L'email a été confirmé via le lien de vérification"
    )
    
    phone_verified = models.BooleanField(
        default=False, 
        verbose_name="Téléphone vérifié",
        help_text="Le numéro a été confirmé via SMS"
    )
    
    # Paiement FedaPay
    fedapay_customer_id = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="ID Client FedaPay",
        help_text="Identifiant unique chez FedaPay"
    )
    
    # Préférences
    newsletter_subscribed = models.BooleanField(
        default=True, 
        verbose_name="Inscrit à la newsletter",
        help_text="Recevoir les emails de conseils et offres"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    last_activity = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Dernière activité"
    )
    
    # ✅ CONFIGURATION CRUCIALE
    USERNAME_FIELD = 'email'           # Champ utilisé pour le login
    REQUIRED_FIELDS = []               # Champs obligatoires pour createsuperuser
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_student', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.email.split('@')[0]} ({self.email})"
    
    def get_display_name(self):
        """Retourne le prénom ou la partie locale de l'email"""
        if self.first_name:
            return self.first_name
        return self.email.split('@')[0]
    
    def get_initials(self):
        """Retourne les initiales pour l'avatar par défaut"""
        first = self.first_name[0].upper() if self.first_name else ''
        last = self.last_name[0].upper() if self.last_name else ''
        initials = f"{first}{last}"
        return initials or self.email[0].upper()
    
    def update_last_activity(self):
        """Met à jour la date de dernière activité"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def has_active_subscription(self):
        """Vérifie si l'utilisateur a un abonnement actif"""
        try:
            from apps.abonnements.models import Abonnement
            return Abonnement.objects.filter(
                user=self,
                is_active=True,
                date_fin__gte=timezone.now()
            ).exists()
        except ImportError:
            return False
    
    def get_subscription(self):
        """Retourne l'abonnement actif ou None"""
        try:
            from apps.abonnements.models import Abonnement
            return Abonnement.objects.filter(
                user=self,
                is_active=True,
                date_fin__gte=timezone.now()
            ).first()
        except ImportError:
            return None
    
    def can_download(self):
        """Vérifie si l'utilisateur peut télécharger (abonnement actif ou crédits)"""
        subscription = self.get_subscription()
        if subscription:
            return subscription.can_download()
        # Vérifier les achats à l'unité
        from apps.abonnements.models import AchatUnite
        return AchatUnite.objects.filter(
            user=self,
            is_used=False
        ).exists()
    
    def get_downloads_count_this_month(self):
        """Nombre de téléchargements ce mois-ci"""
        from apps.epreuves.models import Telechargement
        debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        return Telechargement.objects.filter(
            user=self,
            date_telechargement__gte=debut_mois
        ).count()
    
    def save(self, *args, **kwargs):
        """Surcharge pour créer automatiquement le username depuis l'email"""
        if not self.username:
            # Créer un username unique basé sur l'email
            base_username = self.email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base_username}{counter}"
                counter += 1
            self.username = username
        super().save(*args, **kwargs)


class UserActivity(models.Model):
    """
    Journal d'activité des utilisateurs (analytics)
    """
    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('register', 'Inscription'),
        ('download_epreuve', 'Téléchargement épreuve'),
        ('download_corrige', 'Téléchargement corrigé'),
        ('view_epreuve', 'Consultation épreuve'),
        ('search', 'Recherche'),
        ('purchase', 'Achat'),
        ('subscribe', 'Abonnement'),
        ('profile_update', 'Mise à jour profil'),
        ('password_change', 'Changement mot de passe'),
        ('password_reset', 'Réinitialisation mot de passe'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Utilisateur"
    )
    
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES, 
        verbose_name="Action"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    epreuve_id = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="ID Épreuve"
    )
    
    details = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Détails supplémentaires",
        help_text="Données JSON additionnelles"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name="Adresse IP"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="Navigateur/Appareil"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date/Heure"
    )
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateurs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class EmailVerification(models.Model):
    """
    Tokens de vérification d'email
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification'
    )
    
    token = models.CharField(
        max_length=64, 
        unique=True,
        verbose_name="Token de vérification"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name="Utilisé"
    )
    
    class Meta:
        verbose_name = "Vérification d'email"
        verbose_name_plural = "Vérifications d'email"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vérification pour {self.user.email}"
    
    def is_valid(self):
        """Vérifie si le token est encore valide (24h)"""
        if self.is_used:
            return False
        expiration = self.created_at + timedelta(hours=24)
        return timezone.now() < expiration
    
    def mark_as_used(self):
        """Marque le token comme utilisé"""
        self.is_used = True
        self.save(update_fields=['is_used'])
        # Marquer l'email comme vérifié sur l'utilisateur
        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])


class PasswordResetToken(models.Model):
    """
    Tokens de réinitialisation de mot de passe
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    
    token = models.CharField(
        max_length=64, 
        unique=True,
        verbose_name="Token"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token de réinitialisation"
        ordering = ['-created_at']
    
    def is_valid(self):
        """Valide pendant 1 heure"""
        if self.is_used:
            return False
        expiration = self.created_at + timedelta(hours=1)
        return timezone.now() < expiration


class UserPreference(models.Model):
    """
    Préférences utilisateur avancées
    """
    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]
    
    LANG_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name="Thème"
    )
    
    language = models.CharField(
        max_length=2,
        choices=LANG_CHOICES,
        default='fr',
        verbose_name="Langue"
    )
    
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email"
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name="Notifications SMS"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Préférence utilisateur"
    
    def __str__(self):
        return f"Préférences de {self.user}"