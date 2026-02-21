from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q, Avg
from django.core.paginator import Paginator

from .models import Livre, Categorie, AchatLivre, Lecture, Avis
from apps.dashboard.models import Abonnement


def bibliotheque(request):
    """Bibliothèque de livres"""
    livres = Livre.objects.filter(is_active=True).select_related('categorie')
    
    # Filtres
    categorie_slug = request.GET.get('categorie')
    search = request.GET.get('q')
    format_type = request.GET.get('format')
    
    if categorie_slug:
        livres = livres.filter(categorie__slug=categorie_slug)
    if search:
        livres = livres.filter(
            Q(titre__icontains=search) |
            Q(auteur__icontains=search) |
            Q(description__icontains=search)
        )
    if format_type:
        livres = livres.filter(format_disponible=format_type)
    
    # Pagination
    paginator = Paginator(livres, 9)
    page = request.GET.get('page')
    livres_page = paginator.get_page(page)
    
    context = {
        'livres': livres_page,
        'categories': Categorie.objects.filter(is_active=True),
        'total_livres': livres.count(),
    }
    
    # Si connecté, vérifier accès
    if request.user.is_authenticated:
        abonnement, _ = Abonnement.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'gratuit'}
        )
        context['abonnement'] = abonnement
        context['has_access'] = abonnement.plan in ['mensuel', 'annuel']
        
        # Livres achetés individuellement
        context['achats_ids'] = list(
            AchatLivre.objects.filter(user=request.user).values_list('livre_id', flat=True)
        )
    
    return render(request, 'livres/bibliotheque.html', context)


def detail_livre(request, slug):
    """Page détail d'un livre"""
    livre = get_object_or_404(Livre, slug=slug, is_active=True)
    
    # Livres similaires
    similaires = Livre.objects.filter(
        categorie=livre.categorie,
        is_active=True
    ).exclude(id=livre.id)[:3]
    
    # Avis
    avis = livre.avis.filter(is_approuve=True).select_related('user')[:5]
    
    context = {
        'livre': livre,
        'similaires': similaires,
        'avis': avis,
        'moyenne': livre.note_moyenne,
        'total_avis': livre.nombre_avis,
    }
    
    if request.user.is_authenticated:
        # Vérifier accès
        abonnement, _ = Abonnement.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'gratuit'}
        )
        
        has_access = (
            abonnement.plan in ['mensuel', 'annuel'] or
            AchatLivre.objects.filter(user=request.user, livre=livre).exists() or
            not livre.is_premium
        )
        
        context['has_access'] = has_access
        context['abonnement'] = abonnement
        
        # Progression de lecture
        try:
            lecture = Lecture.objects.get(user=request.user, livre=livre)
            context['progression'] = lecture
        except Lecture.DoesNotExist:
            context['progression'] = None
        
        # Avis de l'utilisateur
        try:
            context['mon_avis'] = Avis.objects.get(user=request.user, livre=livre)
        except Avis.DoesNotExist:
            context['mon_avis'] = None
    
    return render(request, 'livres/detail.html', context)


@login_required
def lecture_livre(request, slug):
    """Lecteur en ligne"""
    livre = get_object_or_404(Livre, slug=slug, is_active=True)
    
    # Vérifier les droits d'accès
    abonnement, _ = Abonnement.objects.get_or_create(
        user=request.user,
        defaults={'plan': 'gratuit'}
    )
    
    has_access = (
        abonnement.plan in ['mensuel', 'annuel'] or
        AchatLivre.objects.filter(user=request.user, livre=livre).exists() or
        not livre.is_premium
    )
    
    if not has_access:
        messages.error(request, "Ce livre nécessite un abonnement ou un achat.")
        return redirect('livres:detail', slug=slug)
    
    # Récupérer ou créer la progression
    lecture, created = Lecture.objects.get_or_create(
        user=request.user,
        livre=livre,
        defaults={'page_actuelle': 1}
    )
    
    # Incrémenter le compteur de lectures
    if created:
        livre.nombre_lectures += 1
        livre.save()
    
    context = {
        'livre': livre,
        'lecture': lecture,
    }
    
    return render(request, 'livres/lecture.html', context)


@login_required
def telecharger_livre(request, slug):
    """Téléchargement du livre"""
    livre = get_object_or_404(Livre, slug=slug, is_active=True)
    
    # Vérifier droits
    abonnement, _ = Abonnement.objects.get_or_create(
        user=request.user,
        defaults={'plan': 'gratuit'}
    )
    
    has_access = (
        abonnement.plan in ['mensuel', 'annuel'] or
        AchatLivre.objects.filter(user=request.user, livre=livre).exists() or
        not livre.is_premium
    )
    
    if not has_access:
        messages.error(request, "Accès refusé. Abonnez-vous ou achetez ce livre.")
        return redirect('livres:detail', slug=slug)
    
    # Choisir le fichier
    fichier = livre.fichier_pdf or livre.fichier_epub
    if not fichier:
        raise Http404("Fichier non disponible")
    
    # Incrémenter compteur
    livre.nombre_telechargements += 1
    livre.save()
    
    # Servir le fichier
    try:
        response = FileResponse(
            fichier.open(),
            content_type='application/pdf' if fichier.name.endswith('.pdf') else 'application/epub+zip',
            as_attachment=True,
            filename=f"{livre.titre}.{fichier.name.split('.')[-1]}"
        )
        return response
    except FileNotFoundError:
        raise Http404("Fichier non trouvé")


@login_required
def sauvegarder_progression(request, slug):
    """API pour sauvegarder la progression (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    livre = get_object_or_404(Livre, slug=slug)
    page = request.POST.get('page')
    pourcentage = request.POST.get('pourcentage')
    
    lecture, _ = Lecture.objects.get_or_create(
        user=request.user,
        livre=livre
    )
    
    lecture.page_actuelle = int(page)
    lecture.pourcentage = int(pourcentage)
    lecture.termine = (pourcentage >= 95)
    lecture.save()
    
    return JsonResponse({'success': True, 'termine': lecture.termine})


@login_required
def ajouter_avis(request, slug):
    """Ajouter un avis"""
    livre = get_object_or_404(Livre, slug=slug)
    
    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire')
        
        # Vérifier si déjà avis
        avis, created = Avis.objects.update_or_create(
            user=request.user,
            livre=livre,
            defaults={
                'note': note,
                'commentaire': commentaire
            }
        )
        
        # Recalculer la moyenne
        moyenne = livre.avis.aggregate(Avg('note'))['note__avg'] or 0
        livre.note_moyenne = round(moyenne, 2)
        livre.nombre_avis = livre.avis.count()
        livre.save()
        
        messages.success(request, "Merci pour votre avis !")
    
    return redirect('livres:detail', slug=slug)