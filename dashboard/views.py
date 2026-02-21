# dashboard/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Download, UserStats, Abonnement


from django.core.paginator import Paginator
from django.db.models import Q, Count



def get_or_create_abonnement(user):
    """Récupérer ou créer l'abonnement de l'utilisateur"""
    abonnement, created = Abonnement.objects.get_or_create(
        user=user,
        defaults={
            'plan': 'gratuit',
            'telechargements_inclus': 3
        }
    )
    return abonnement


def get_or_create_stats(user):
    """Récupérer ou créer les stats de l'utilisateur"""
    stats, created = UserStats.objects.get_or_create(
        user=user,
        defaults={
            'total_downloads': 0,
            'downloads_this_month': 0
        }
    )
    return stats


@login_required
def dashboard_home(request):
    """Page d'accueil du dashboard avec statistiques réelles"""
    user = request.user
    
    # Récupérer ou créer l'abonnement
    abonnement = get_or_create_abonnement(user)
    
    # Récupérer ou créer les stats
    stats = get_or_create_stats(user)
    
    # Calculer les stats réelles
    total_downloads = Download.objects.filter(user=user).count()
    
    # Téléchargements ce mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    downloads_this_month = Download.objects.filter(
        user=user,
        downloaded_at__gte=debut_mois
    ).count()
    
    # Téléchargements gratuits utilisés (tous les temps pour le plan gratuit)
    free_downloads_used = Download.objects.filter(
        user=user,
        is_free=True
    ).count()
    
    # Calculer les téléchargements restants
    if abonnement.plan == 'gratuit':
        downloads_remaining = max(0, 3 - free_downloads_used)
    else:
        downloads_remaining = abonnement.telechargements_restant()
    
    # Derniers téléchargements (5 derniers)
    recent_downloads = Download.objects.filter(user=user)[:5]
    
    # Matière favorite (la plus téléchargée)
    favorite_matiere = None
    if total_downloads > 0:
        matieres = Download.objects.filter(user=user).values('matiere').annotate(
            count=models.Count('matiere')
        ).order_by('-count').first()
        if matieres:
            favorite_matiere = matieres['matiere']
    
    # Mettre à jour les stats
    stats.total_downloads = total_downloads
    stats.downloads_this_month = downloads_this_month
    stats.favorite_matiere = favorite_matiere or ''
    stats.save()
    
    # Stats globales du site (à mettre en cache plus tard)
    from django.db.models import Count
    from accounts.models import User  # ou get_user_model()
    
    total_epreuves = 2500  # À remplacer par le vrai compte quand l'app epreuves existe
    total_corriges = 1800  # Idem
    
    context = {
        'user': user,
        
        # Stats personnelles (dynamiques)
        'downloads_count': total_downloads,
        'downloads_this_month': downloads_this_month,
        'downloads_remaining': downloads_remaining,
        'free_downloads_used': free_downloads_used,
        'free_downloads_total': 3,
        
        # Abonnement
        'abonnement': abonnement,
        'plan_name': abonnement.get_plan_display(),
        'plan_code': abonnement.plan,
        'is_premium': abonnement.plan in ['mensuel', 'annuel'],
        
        # Stats globales
        'epreuves_available': total_epreuves,
        'corriges_available': total_corriges,
        'total_users': User.objects.filter(is_active=True).count(),
        
        # Activité récente
        'recent_downloads': recent_downloads,
        'favorite_matiere': favorite_matiere,
        
        # Progression
        'usage_percentage': min(100, int((free_downloads_used / 3) * 100)) if abonnement.plan == 'gratuit' else 0,
    }
    
    return render(request, 'dashboard/home.html', context)


# @login_required
# def epreuves_list(request):
#     """Liste des épreuves disponibles"""
#     user = request.user
    
#     # Récupérer l'abonnement pour afficher les limites
#     abonnement = get_or_create_abonnement(user)
    
#     return render(request, 'dashboard/epreuves.html', {
#         'user': user,
#         'abonnement': abonnement,
#         'downloads_remaining': abonnement.telechargements_restant(),
#     })


# @login_required
# def downloads_history(request):
#     """Historique des téléchargements avec pagination"""
#     user = request.user
    
#     # Tous les téléchargements avec pagination
#     downloads_list = Download.objects.filter(user=user)
    
#     # Grouper par mois pour l'affichage
#     from django.db.models.functions import TruncMonth
#     from django.db.models import Count
    
#     downloads_by_month = Download.objects.filter(
#         user=user
#     ).annotate(
#         month=TruncMonth('downloaded_at')
#     ).values('month').annotate(
#         count=Count('id')
#     ).order_by('-month')
    
#     return render(request, 'dashboard/downloads.html', {
#         'user': user,
#         'downloads': downloads_list,
#         'downloads_by_month': downloads_by_month,
#         'total_downloads': downloads_list.count(),
#     })


@login_required
def abonnement_view(request):
    """Gestion de l'abonnement avec comparaison des plans"""
    user = request.user
    abonnement = get_or_create_abonnement(user)
    
    # Calculer l'économie annuelle
    plans_comparison = [
        {
            'code': 'gratuit',
            'name': 'Gratuit',
            'price': 0,
            'downloads': 3,
            'features': ['3 épreuves gratuites', 'Accès limité', 'Support email'],
            'popular': False,
            'current': abonnement.plan == 'gratuit',
        },
        {
            'code': 'mensuel',
            'name': 'Mensuel',
            'price': 2500,
            'downloads': 100,
            'features': ['100 téléchargements/mois', 'Tous les corrigés', 'Support prioritaire', 'Annulable'],
            'popular': True,
            'current': abonnement.plan == 'mensuel',
        },
        {
            'code': 'annuel',
            'name': 'Annuel',
            'price': 20000,
            'downloads': float('inf'),  # Illimité
            'features': ['Téléchargements illimités', 'Tous les corrigés', 'Support 24/7', 'Livres numériques', '-33% de réduction'],
            'popular': False,
            'current': abonnement.plan == 'annuel',
            'savings': 10000,  # Économie vs mensuel
        },
    ]
    
    return render(request, 'dashboard/abonnement.html', {
        'user': user,
        'abonnement': abonnement,
        'current_plan': abonnement.get_plan_display(),
        'plans': plans_comparison,
        'next_billing': abonnement.date_fin,
    })


@login_required
def profile_view(request):
    """Profil utilisateur avec stats personnelles"""
    user = request.user
    stats = get_or_create_stats(user)
    abonnement = get_or_create_abonnement(user)
    
    # Calculer l'ancienneté
    member_since = user.date_joined
    days_as_member = (timezone.now() - member_since).days
    
    return render(request, 'dashboard/profile.html', {
        'user': user,
        'stats': stats,
        'abonnement': abonnement,
        'member_since': member_since,
        'days_as_member': days_as_member,
        'completion_percentage': calculate_profile_completion(user),
    })


def calculate_profile_completion(user):
    """Calculer le pourcentage de complétion du profil"""
    fields = [
        user.first_name,
        user.last_name,
        user.email,
        user.phone,
        user.school,
        user.class_level,
    ]
    filled = sum(1 for f in fields if f)
    return int((filled / len(fields)) * 100)

























# dashboard/views.py (ajouter ces imports et fonctions)


@login_required
def epreuves_list(request):
    """Liste des épreuves avec filtres et recherche"""
    user = request.user
    abonnement = get_or_create_abonnement(user)
    
    # Listes pour les filtres (à remplacer par des requêtes réelles)
    classes_list = ['6ème', '5ème', '4ème', '3ème', '2nde', '1ère', 'Terminale']
    matieres_list = ['Mathématiques', 'Physique-Chimie', 'SVT', 'Français', 'Anglais', 'Histoire-Géographie', 'Philosophie']
    annees_list = list(range(2024, 2014, -1))
    
    # Filtres depuis l'URL
    selected_classe = request.GET.get('classe', user.class_level or '')
    selected_matiere = request.GET.get('matiere', '')
    selected_annee = request.GET.get('annee', '')
    selected_type = request.GET.get('type', '')
    search_query = request.GET.get('q', '')
    
    # Simulation d'épreuves (à remplacer par requête réelle)
    # Epreuve.objects.filter(...)
    epreuves = []  # Remplacer par tes vraies épreuves
    
    # Pagination
    paginator = Paginator(epreuves, 12)
    page = request.GET.get('page')
    epreuves = paginator.get_page(page)
    
    context = {
        'user': user,
        'abonnement': abonnement,
        'is_premium': abonnement.plan in ['mensuel', 'annuel'],
        'can_download': abonnement.telechargements_restant() > 0 or abonnement.plan != 'gratuit',
        'downloads_remaining': abonnement.telechargements_restant(),
        
        # Filtres
        'classes_list': classes_list,
        'matieres_list': matieres_list,
        'annees_list': annees_list,
        'selected_classe': selected_classe,
        'selected_matiere': selected_matiere,
        'selected_annee': selected_annee,
        'selected_type': selected_type,
        'search_query': search_query,
        
        # Résultats
        'epreuves': epreuves,
        'epreuves_count': len(epreuves),
    }
    
    return render(request, 'dashboard/epreuves.html', context)


@login_required
def downloads_history(request):
    """Historique des téléchargements"""
    user = request.user
    
    # Récupérer les vrais téléchargements
    downloads_list = Download.objects.filter(user=user).order_by('-downloaded_at')
    
    # Stats
    total_downloads = downloads_list.count()
    
    # Ce mois
    from django.utils import timezone
    from datetime import timedelta
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    downloads_this_month = downloads_list.filter(downloaded_at__gte=debut_mois).count()
    
    # Listes pour filtres
    matieres_list = downloads_list.values_list('matiere', flat=True).distinct()
    annees_list = downloads_list.values_list('annee', flat=True).distinct().order_by('-annee')
    
    # Grouper par mois pour l'affichage
    downloads_by_month = {}
    for download in downloads_list:
        month_key = download.downloaded_at.strftime('%B %Y')
        if month_key not in downloads_by_month:
            downloads_by_month[month_key] = []
        downloads_by_month[month_key].append(download)
    
    # Abonnement
    abonnement = get_or_create_abonnement(user)
    is_premium = abonnement.plan in ['mensuel', 'annuel']
    downloads_remaining = abonnement.telechargements_restant() if not is_premium else float('inf')
    
    context = {
        'user': user,
        'downloads': downloads_list,
        'total_downloads': total_downloads,
        'downloads_this_month': downloads_this_month,
        'downloads_by_month': downloads_by_month.items(),
        'matieres_list': matieres_list,
        'annees_list': annees_list,
        'is_premium': is_premium,
        'downloads_remaining': downloads_remaining if downloads_remaining != float('inf') else 'Illimité',
    }
    
    return render(request, 'dashboard/downloads.html', context)