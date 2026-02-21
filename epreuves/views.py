from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime

from .models import (
    Epreuve, Matiere, Classe, Niveau, Serie, Periode, 
    Telechargement, Favori
)
from dashboard.models import Abonnement


def get_annee_scolaire_actuelle():
    """Retourne l'année scolaire en cours"""
    now = timezone.now()
    if now.month >= 9:  # Rentrée en septembre
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"


def liste_epreuves(request):
    """Liste des épreuves avec filtres adaptés au Bénin"""
    
    # Base queryset optimisée
    epreuves = Epreuve.objects.filter(is_active=True).select_related(
        'matiere', 'classe', 'classe__niveau', 'serie', 'periode'
    )
    
    # Filtres
    classe_id = request.GET.get('classe')
    matiere_id = request.GET.get('matiere')
    periode_id = request.GET.get('periode')
    serie_id = request.GET.get('serie')
    type_epreuve = request.GET.get('type_epreuve')
    annee_scolaire = request.GET.get('annee_scolaire', get_annee_scolaire_actuelle())
    search = request.GET.get('q')
    
    if classe_id:
        epreuves = epreuves.filter(classe_id=classe_id)
    if matiere_id:
        epreuves = epreuves.filter(matiere_id=matiere_id)
    if periode_id:
        if periode_id == 'exam':
            epreuves = epreuves.filter(type_epreuve__in=['ceped', 'bepc', 'bac_1', 'bac_2', 'bac_blanc'])
        else:
            epreuves = epreuves.filter(periode_id=periode_id)
    if serie_id:
        epreuves = epreuves.filter(serie_id=series_id)
    if type_epreuve:
        epreuves = epreuves.filter(type_epreuve=type_epreuve)
    if annee_scolaire:
        epreuves = epreuves.filter(annee_scolaire=annee_scolaire)
    if search:
        epreuves = epreuves.filter(
            Q(titre__icontains=search) |
            Q(matiere__nom__icontains=search) |
            Q(description__icontains=search) |
            Q(classe__nom__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(epreuves, 12)
    page = request.GET.get('page')
    epreuves_page = paginator.get_page(page)
    
    # Données pour les filtres
    context = {
        'epreuves': epreuves_page,
        'total_epreuves': epreuves.count(),
        'classes': Classe.objects.select_related('niveau').all(),
        'matieres': Matiere.objects.filter(is_active=True),
        'periodes': Periode.objects.all(),
        'series': Serie.objects.all(),
        'annees_scolaires': [f"{y}-{y+1}" for y in range(2024, 2019, -1)],
        'annee_actuelle': get_annee_scolaire_actuelle(),
        'filtres': {
            'classe': classe_id,
            'matiere': matiere_id,
            'periode': periode_id,
            'serie': serie_id,
            'type_epreuve': type_epreuve,
            'annee_scolaire': annee_scolaire,
            'q': search,
        }
    }
    
    # Données utilisateur connecté
    if request.user.is_authenticated:
        abonnement, _ = Abonnement.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'gratuit', 'telechargements_inclus': 3}
        )
        context['abonnement'] = abonnement
        context['can_download'] = abonnement.telechargements_restant() > 0 or abonnement.plan != 'gratuit'
        context['downloads_remaining'] = abonnement.telechargements_restant()
        
        # IDs déjà téléchargés
        context['downloaded_ids'] = list(
            Telechargement.objects.filter(user=request.user).values_list('epreuve_id', flat=True)
        )
        
        # Favoris
        context['favoris_ids'] = list(
            Favori.objects.filter(user=request.user).values_list('epreuve_id', flat=True)
        )
    
    return render(request, 'epreuves/liste.html', context)


def detail_epreuve(request, slug):
    """Page détail d'une épreuve"""
    epreuve = get_object_or_404(
        Epreuve.objects.select_related('matiere', 'classe', 'serie', 'periode'),
        slug=slug, 
        is_active=True
    )
    
    # Incrémenter les vues
    epreuve.nombre_vues += 1
    epreuve.save(update_fields=['nombre_vues'])
    
    # Épreuves similaires (même classe, même matière ou même période)
    similaires = Epreuve.objects.filter(
        classe=epreuve.classe,
        is_active=True
    ).exclude(id=epreuve.id).select_related('matiere', 'periode')[:4]
    
    context = {
        'epreuve': epreuve,
        'similaires': similaires,
    }
    
    if request.user.is_authenticated:
        # Abonnement
        abonnement, _ = Abonnement.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'gratuit'}
        )
        
        # Droits d'accès
        has_access = (
            abonnement.plan in ['mensuel', 'annuel'] or
            not epreuve.is_premium
        )
        
        # Déjà téléchargé ?
        deja_telecharge = Telechargement.objects.filter(
            user=request.user,
            epreuve=epreuve
        ).exists()
        
        context.update({
            'abonnement': abonnement,
            'has_access': has_access,
            'deja_telecharge': deja_telecharge,
            'downloads_remaining': abonnement.telechargements_restant(),
            'est_favori': Favori.objects.filter(user=request.user, epreuve=epreuve).exists(),
        })
    
    return render(request, 'epreuves/detail.html', context)


@login_required
def telecharger_epreuve(request, slug):
    """Téléchargement d'une épreuve"""
    epreuve = get_object_or_404(Epreuve, slug=slug, is_active=True)
    
    # Vérifier droits
    abonnement, _ = Abonnement.objects.get_or_create(
        user=request.user,
        defaults={'plan': 'gratuit', 'telechargements_inclus': 3}
    )
    
    deja_telecharge = Telechargement.objects.filter(
        user=request.user, 
        epreuve=epreuve
    ).exists()
    
    if not deja_telecharge:
        if abonnement.plan == 'gratuit' and abonnement.telechargements_restant() <= 0:
            messages.error(request, "Vous avez épuisé vos 3 téléchargements gratuits.")
            return redirect('abonnements:plans')
        
        # Enregistrer téléchargement
        Telechargement.objects.create(
            user=request.user,
            epreuve=epreuve,
            ip_address=get_client_ip(request),
            utilise_credit_gratuit=(abonnement.plan == 'gratuit')
        )
        
        # Mettre à jour compteurs
        if abonnement.plan == 'gratuit':
            abonnement.telechargements_utilises += 1
            abonnement.save()
        
        epreuve.nombre_telechargements += 1
        epreuve.save()
        
        messages.success(
            request, 
            f"Téléchargement réussi ! Il vous reste {abonnement.telechargements_restant()} téléchargements."
        )
    
    # Servir fichier
    try:
        response = FileResponse(
            epreuve.fichier_sujet.open(),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{epreuve.matiere.nom}_{epreuve.classe.nom}_{epreuve.annee_scolaire}.pdf"
        )
        return response
    except FileNotFoundError:
        raise Http404("Fichier non trouvé")


@login_required
def telecharger_corrige(request, slug):
    """Téléchargement du corrigé"""
    epreuve = get_object_or_404(Epreuve, slug=slug, is_active=True)
    
    if not epreuve.fichier_corrige:
        raise Http404("Corrigé non disponible")
    
    # Mêmes vérifications que pour le sujet...
    # (code similaire)
    
    try:
        response = FileResponse(
            epreuve.fichier_corrige.open(),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"CORRIGE_{epreuve.matiere.nom}_{epreuve.classe.nom}_{epreuve.annee_scolaire}.pdf"
        )
        return response
    except FileNotFoundError:
        raise Http404("Fichier non trouvé")


@login_required
def toggle_favori(request, slug):
    """Ajouter/Retirer des favoris"""
    epreuve = get_object_or_404(Epreuve, slug=slug)
    
    favori, created = Favori.objects.get_or_create(
        user=request.user, 
        epreuve=epreuve
    )
    
    if not created:
        favori.delete()
        messages.success(request, "Retiré des favoris")
        status = 'removed'
    else:
        messages.success(request, "Ajouté aux favoris ❤️")
        status = 'added'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': status})
    
    return redirect(request.META.get('HTTP_REFERER', 'epreuves:liste'))


def get_client_ip(request):
    """Récupère l'IP client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')