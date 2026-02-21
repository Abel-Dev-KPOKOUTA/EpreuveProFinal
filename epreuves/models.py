from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class SystemeScolaire(models.Model):
    """Système scolaire : Semestriel ou Trimestriel"""
    SYSTEME_CHOICES = [
        ('semestriel', 'Système Semestriel (Collège/Lycée)'),
        ('trimestriel', 'Système Trimestriel (Primaire)'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    type_systeme = models.CharField(max_length=15, choices=SYSTEME_CHOICES)
    nombre_periodes = models.PositiveSmallIntegerField(help_text="2 pour semestriel, 3 pour trimestriel")
    
    class Meta:
        verbose_name = "Système Scolaire"
    
    def __str__(self):
        return self.nom


class Niveau(models.Model):
    """Niveaux : Primaire, Collège, Lycée"""
    CYCLE_CHOICES = [
        ('primaire', 'Enseignement Primaire'),
        ('college', 'Premier Cycle (Collège)'),
        ('lycee', 'Second Cycle (Lycée)'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=50)
    cycle = models.CharField(max_length=10, choices=CYCLE_CHOICES)
    systeme = models.ForeignKey(SystemeScolaire, on_delete=models.CASCADE, related_name='niveaux')
    ordre = models.PositiveSmallIntegerField(default=0)
    
    # Configuration spécifique
    has_serie = models.BooleanField(default=False, help_text="A des séries (A, C, D...)")
    has_examen_final = models.BooleanField(default=False, help_text="A un examen final (CEP, BEPC, Bac)")
    nom_examen = models.CharField(max_length=50, blank=True, help_text="Ex: BEPC, Baccalauréat")
    
    class Meta:
        verbose_name = "Niveau"
        ordering = ['ordre']
    
    def __str__(self):
        return self.nom


class Classe(models.Model):
    """Classes : CP1, CE1... 6ème, 5ème... Terminale"""
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='classes')
    nom = models.CharField(max_length=30)  # CP1, 6ème, Terminale...
    code = models.CharField(max_length=15, unique=True)  # cp1, 6eme, terminale
    
    # Pour le système béninois
    numero_classe = models.PositiveSmallIntegerField(
        help_text="1 pour CP1/6ème, 2 pour CP2/5ème... 4 pour Terminale"
    )
    
    class Meta:
        verbose_name = "Classe"
        ordering = ['niveau__ordre', 'numero_classe']
    
    def __str__(self):
        return f"{self.nom} ({self.niveau.nom})"


class Serie(models.Model):
    """Séries du second cycle : A, C, D, E, TI, G2..."""
    code = models.CharField(max_length=5, unique=True)  # A, C, D, TI...
    nom_complet = models.CharField(max_length=100)  # Série A (Maths-Physique)
    description = models.TextField(blank=True)
    couleur = models.CharField(max_length=7, default="#6366f1")
    
    # Matières associées
    matieres_principales = models.ManyToManyField('Matiere', blank=True, related_name='series_principales')
    
    class Meta:
        verbose_name = "Série"
    
    def __str__(self):
        return f"Série {self.code}"


class Periode(models.Model):
    """Semestres ou Trimestres"""
    PERIODE_CHOICES = [
        ('s1', '1er Semestre'),
        ('s2', '2ème Semestre'),
        ('t1', '1er Trimestre'),
        ('t2', '2ème Trimestre'),
        ('t3', '3ème Trimestre'),
        ('exam', 'Examen Final'),
    ]
    
    code = models.CharField(max_length=5, choices=PERIODE_CHOICES, unique=True)
    nom = models.CharField(max_length=30)
    numero = models.PositiveSmallIntegerField(help_text="1, 2 ou 3")
    mois_debut = models.CharField(max_length=20, blank=True)  # Septembre, Février...
    mois_fin = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = "Période"
        ordering = ['code']
    
    def __str__(self):
        return self.nom


class Matiere(models.Model):
    """Matières enseignées"""
    nom = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    
    # Organisation
    niveaux = models.ManyToManyField(Niveau, blank=True, related_name='matieres')
    
    # Apparence
    couleur = models.CharField(max_length=7, default="#6366f1")
    icon = models.CharField(max_length=10, blank=True, default="📚")
    
    # Métadonnées
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Matière"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.nom)
        super().save(*args, **kwargs)


class Epreuve(models.Model):
    """Épreuves : Compositions, Évaluations, Examens"""
    
    # Types d'épreuves spécifiques au Bénin
    TYPE_EPREUVE_CHOICES = [
        # Contrôles continus
        ('composition_1', '1ère Composition'),
        ('composition_2', '2ème Composition'),
        ('evaluation_1', '1ère Évaluation'),
        ('evaluation_2', '2ème Évaluation'),
        ('evaluation_3', '3ème Évaluation'),  # Pour trimestriel
        
        # Examens officiels
        ('ceped', 'CEPED'),  # Certificat d'Études du Premier Degré
        ('cepd', 'CEPD'),    # Ancien nom
        ('bepc', 'BEPC'),
        ('bac_1', 'Baccalauréat 1er Tour'),
        ('bac_2', 'Baccalauréat 2ème Tour'),
        ('bac_blanc', 'Bac Blanc'),
        
        # Concours
        ('concours', 'Concours d\'entrée'),
        ('examen_entree', 'Examen d\'entrée'),
    ]
    
    # Session
    SESSION_CHOICES = [
        ('normale', 'Session Normale'),
        ('remplacement', 'Session de Remplacement'),
        ('rattrapage', 'Rattrapage'),
    ]
    
    titre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    
    # Hiérarchie scolaire
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='epreuves')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='epreuves')
    serie = models.ForeignKey(Serie, on_delete=models.SET_NULL, null=True, blank=True, related_name='epreuves')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='epreuves')
    
    # Période (crucial pour le Bénin)
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE, related_name='epreuves')
    annee_scolaire = models.CharField(
        max_length=9, 
        help_text="Format: 2023-2024",
        default="2023-2024"
    )
    
    # Détails de l'épreuve
    type_epreuve = models.CharField(max_length=20, choices=TYPE_EPREUVE_CHOICES)
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, default='normale', blank=True)
    
    # Spécificités
    duree = models.CharField(max_length=20, blank=True, help_text="Ex: 2h, 4h, 5h30")
    coefficient = models.PositiveSmallIntegerField(null=True, blank=True)
    bareme = models.PositiveSmallIntegerField(default=20, help_text="Barème sur 20 ou 400")
    
    # Fichiers
    fichier_sujet = models.FileField(upload_to='epreuves/sujets/%Y/%m/')
    fichier_corrige = models.FileField(
        upload_to='epreuves/corriges/%Y/%m/', 
        blank=True, null=True,
        verbose_name="Corrigé type"
    )
    fichier_rapport = models.FileField(
        upload_to='epreuves/rapports/%Y/%m/',
        blank=True, null=True,
        verbose_name="Rapport de l'épreuve (pour examens officiels)"
    )
    
    # Contenu
    enonce = models.TextField(blank=True, help_text="Texte de l'énoncé (optionnel)")
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text="Instructions spéciales")
    
    # Métadonnées
    nombre_pages = models.PositiveSmallIntegerField(null=True, blank=True)
    taille_fichier = models.PositiveIntegerField(null=True, blank=True, help_text="En Ko")
    
    # Gestion
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    nombre_telechargements = models.PositiveIntegerField(default=0)
    nombre_vues = models.PositiveIntegerField(default=0)
    
    # Dates
    date_epreuve = models.DateField(null=True, blank=True, help_text="Date réelle de l'épreuve")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Épreuve"
        verbose_name_plural = "Épreuves"
        ordering = ['-annee_scolaire', 'periode__code', 'matiere__nom']
        indexes = [
            models.Index(fields=['annee_scolaire', 'classe', 'periode']),
            models.Index(fields=['type_epreuve', 'matiere']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        serie_str = f" - Série {self.serie.code}" if self.serie else ""
        return f"{self.get_type_epreuve_display()} - {self.matiere}{serie_str} ({self.classe} - {self.periode.nom})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.type_epreuve}-{self.matiere}-{self.classe}-{self.annee_scolaire}"
            slug = slugify(base[:80])
            counter = 1
            while Epreuve.objects.filter(slug=slug).exists():
                slug = f"{slugify(base[:75])}-{counter}"
                counter += 1
            self.slug = slug
        
        # Calcul taille
        if self.fichier_sujet and not self.taille_fichier:
            self.taille_fichier = self.fichier_sujet.size // 1024
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('epreuves:detail', kwargs={'slug': self.slug})
    
    def get_type_display_with_icon(self):
        """Retourne le type avec icône appropriée"""
        icons = {
            'composition_1': '📝',
            'composition_2': '📝',
            'evaluation_1': '✍️',
            'evaluation_2': '✍️',
            'evaluation_3': '✍️',
            'ceped': '🎓',
            'cepd': '🎓',
            'bepc': '🎓',
            'bac_1': '🎓',
            'bac_2': '🎓',
            'bac_blanc': '📋',
            'concours': '🏆',
        }
        return f"{icons.get(self.type_epreuve, '📄')} {self.get_type_epreuve_display()}"
    
    def is_examen_officiel(self):
        """Vérifie si c'est un examen officiel"""
        return self.type_epreuve in ['ceped', 'cepd', 'bepc', 'bac_1', 'bac_2']
    
    def periode_complete(self):
        """Retourne la période avec l'année scolaire"""
        return f"{self.periode.nom} {self.annee_scolaire}"


class Telechargement(models.Model):
    """Téléchargements par les utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telechargements_epreuves')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='telechargements')
    
    date_telechargement = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Quelle partie a été téléchargée
    a_telecharge_sujet = models.BooleanField(default=True)
    a_telecharge_corrige = models.BooleanField(default=False)
    
    # Pour les utilisateurs gratuits
    utilise_credit_gratuit = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'epreuve']
        ordering = ['-date_telechargement']
    
    def __str__(self):
        return f"{self.user} - {self.epreuve}"


class Favori(models.Model):
    """Épreuves favorites"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris_epreuves')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='favoris')
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'epreuve']
    
    def __str__(self):
        return f"❤️ {self.user} - {self.epreuve}"