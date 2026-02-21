from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

User = get_user_model()


class Categorie(models.Model):
    """Catégories de livres"""
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    couleur = models.CharField(max_length=7, default="#6366f1")
    ordre = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Catégorie"
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return self.nom


class Livre(models.Model):
    """Livres numériques"""
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('both', 'PDF + EPUB'),
    ]
    
    titre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sous_titre = models.CharField(max_length=200, blank=True)
    
    # Auteurs
    auteur = models.CharField(max_length=200)
    editeur = models.CharField(max_length=100, blank=True)
    
    # Relations
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='livres')
    
    # Contenu
    description = models.TextField()
    extrait = models.TextField(blank=True, help_text="Premières pages pour preview")
    
    # Métadonnées
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")
    nombre_pages = models.PositiveIntegerField(null=True, blank=True)
    annee_publication = models.PositiveSmallIntegerField(null=True, blank=True)
    langue = models.CharField(max_length=20, default='Français')
    
    # Fichiers
    fichier_pdf = models.FileField(upload_to='livres/pdf/%Y/', blank=True, null=True)
    fichier_epub = models.FileField(upload_to='livres/epub/%Y/', blank=True, null=True)
    format_disponible = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Couverture
    couverture = models.ImageField(upload_to='livres/covers/%Y/', blank=True, null=True)
    
    # Prix et accès
    prix = models.PositiveIntegerField(default=0, help_text="Prix en FCFA, 0 = gratuit avec abonnement")
    is_premium = models.BooleanField(default=True, help_text="Nécessite un abonnement actif")
    is_active = models.BooleanField(default=True)
    
    # Stats
    nombre_lectures = models.PositiveIntegerField(default=0)
    nombre_telechargements = models.PositiveIntegerField(default=0)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    nombre_avis = models.PositiveIntegerField(default=0)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Livre"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['categorie', 'is_premium']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.auteur}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titre[:50])
            slug = base_slug
            counter = 1
            while Livre.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('livres:detail', kwargs={'slug': self.slug})
    
    def get_lecture_url(self):
        return reverse('livres:lecture', kwargs={'slug': self.slug})
    
    def prix_formate(self):
        if self.prix == 0:
            return "Gratuit"
        return f"{self.prix:,} FCFA"


class AchatLivre(models.Model):
    """Achats individuels de livres (hors abonnement)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achats_livres')
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='achats')
    
    montant_paye = models.PositiveIntegerField()
    date_achat = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['user', 'livre']
        verbose_name = "Achat de livre"
    
    def __str__(self):
        return f"{self.user} - {self.livre}"


class Lecture(models.Model):
    """Progression de lecture"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lectures')
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='lectures_users')
    
    page_actuelle = models.PositiveIntegerField(default=1)
    pourcentage = models.PositiveSmallIntegerField(default=0)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    termine = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'livre']
        verbose_name = "Progression de lecture"
    
    def __str__(self):
        return f"{self.user} - {self.livre} ({self.pourcentage}%)"


class Avis(models.Model):
    """Avis et notes des utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_livres')
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='avis')
    
    note = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    is_approuve = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        unique_together = ['user', 'livre']
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.user} - {self.livre} ({self.note}/5)"