# dashboard/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Download(models.Model):
    """Historique des téléchargements d'épreuves"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='downloads'
    )
    epreuve_id = models.PositiveIntegerField()
    epreuve_title = models.CharField(max_length=200)
    matiere = models.CharField(max_length=50)
    classe = models.CharField(max_length=20)
    annee = models.PositiveSmallIntegerField()
    downloaded_at = models.DateTimeField(auto_now_add=True)
    is_free = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-downloaded_at']
        verbose_name = 'Téléchargement'
        verbose_name_plural = 'Téléchargements'


class UserStats(models.Model):
    """Statistiques agrégées par utilisateur (pour performance)"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='stats'
    )
    total_downloads = models.PositiveIntegerField(default=0)
    downloads_this_month = models.PositiveIntegerField(default=0)
    last_download_date = models.DateTimeField(null=True, blank=True)
    favorite_matiere = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Statistiques utilisateur'
        verbose_name_plural = 'Statistiques utilisateurs'


class Abonnement(models.Model):
    """Gestion des abonnements"""
    PLAN_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('mensuel', 'Mensuel'),
        ('annuel', 'Annuel'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='abonnement'
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='gratuit'
    )
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    telechargements_inclus = models.PositiveIntegerField(default=3)  # Gratuit = 3
    telechargements_utilises = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Abonnement'
    
    def telechargements_restant(self):
        """Calculer les téléchargements restants"""
        restant = self.telechargements_inclus - self.telechargements_utilises
        return max(0, restant)
    
    def is_valid(self):
        """Vérifier si l'abonnement est valide"""
        if not self.is_active:
            return False
        if self.plan == 'gratuit':
            return True
        if self.date_fin and self.date_fin > timezone.now():
            return True
        return False