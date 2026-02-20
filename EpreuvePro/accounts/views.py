# apps/accounts/views.py (OPTIMISÉ)

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserLoginForm


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vue de connexion"""
    # ✅ Redirection si déjà connecté
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    form = UserLoginForm()
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['username']  # ✅ C'est un email en fait !
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember', False)
            
            # ✅ Authentification avec email (USERNAME_FIELD = 'email')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                # ✅ Vérifier si le compte est actif
                if not user.is_active:
                    messages.error(request, 'Votre compte a été désactivé. Contactez le support.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                login(request, user)
                
                # ✅ Mettre à jour la dernière activité
                user.update_last_activity()
                
                # ✅ Gestion de la session
                if not remember:
                    request.session.set_expiry(0)  # Session navigateur
                else:
                    request.session.set_expiry(1209600)  # 2 semaines
                
                messages.success(request, f'Bonjour {user.get_display_name()} ! 👋')
                
                # ✅ Redirection sécurisée
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Email ou mot de passe incorrect')
                form.add_error(None, 'Identifiants invalides')
    
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Vue d'inscription"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    form = UserRegistrationForm()
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)  # ✅ Ajout request.FILES pour l'avatar
        
        if form.is_valid():
            user = form.save()
            
            # ✅ Créer les préférences par défaut
            from .models import UserPreference
            UserPreference.objects.create(user=user)
            
            # ✅ Logger l'activité
            from .models import UserActivity
            UserActivity.objects.create(
                user=user,
                action='register',
                description='Inscription réussie',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
            )
            
            login(request, user)
            messages.success(request, 'Bienvenue sur EpreuvesPro ! 🎉 Vérifie ton email pour activer ton compte.')
            return redirect('dashboard:home')
        else:
            # ✅ Messages d'erreur plus clairs
            for field, errors in form.errors.items():
                field_name = {
                    'username': 'Email',
                    'password1': 'Mot de passe',
                    'password2': 'Confirmation',
                }.get(field, field)
                for error in errors:
                    messages.error(request, f"{field_name}: {error}")
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    # ✅ Logger la déconnexion avant de déconnecter
    from .models import UserActivity
    UserActivity.objects.create(
        user=request.user,
        action='logout',
        ip_address=get_client_ip(request)
    )
    
    logout(request)
    messages.info(request, 'À bientôt ! 👋')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    user = request.user
    
    # ✅ Récupérer l'abonnement actif via la méthode du modèle
    subscription = user.get_subscription()
    
    # ✅ Stats pour le dashboard
    context = {
        'user': user,
        'subscription': subscription,
        'downloads_this_month': user.get_downloads_count_this_month(),
        'activities': user.activities.all()[:10],  # 10 dernières activités
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    """Mise à jour du profil (AJAX ou formulaire)"""
    user = request.user
    
    # ✅ Mettre à jour les champs autorisés
    allowed_fields = ['first_name', 'last_name', 'phone', 'school', 'class_level']
    for field in allowed_fields:
        if field in request.POST:
            setattr(user, field, request.POST[field])
    
    if 'avatar' in request.FILES:
        user.avatar = request.FILES['avatar']
    
    user.save()
    user.update_last_activity()
    
    messages.success(request, 'Profil mis à jour avec succès !')
    return redirect('accounts:profile')


# ==================== UTILITAIRES ====================

def get_client_ip(request):
    """Récupère l'IP réelle du client (derrière proxy si nécessaire)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==================== VUES DE VÉRIFICATION ====================

from django.shortcuts import get_object_or_404
from .models import EmailVerification

def verify_email_view(request, token):
    """Vérification d'email via token"""
    verification = get_object_or_404(EmailVerification, token=token)
    
    if verification.is_valid():
        verification.mark_as_used()
        messages.success(request, 'Votre email a été vérifié avec succès ! ✅')
    else:
        messages.error(request, 'Ce lien de vérification a expiré ou a déjà été utilisé.')
    
    return redirect('accounts:login')


@login_required
def resend_verification_email(request):
    """Renvoyer l'email de vérification"""
    if request.user.email_verified:
        messages.info(request, 'Votre email est déjà vérifié.')
        return redirect('accounts:profile')
    
    # ✅ Générer nouveau token
    import secrets
    from .models import EmailVerification
    
    # Supprimer l'ancien s'il existe
    EmailVerification.objects.filter(user=request.user).delete()
    
    # Créer nouveau
    verification = EmailVerification.objects.create(
        user=request.user,
        token=secrets.token_urlsafe(32)
    )
    
    # ✅ Envoyer l'email (à implémenter avec Celery)
    # send_verification_email.delay(request.user.email, verification.token)
    
    messages.success(request, 'Un nouvel email de vérification a été envoyé.')
    return redirect('accounts:profile')