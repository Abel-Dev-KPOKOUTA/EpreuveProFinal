# accounts/views.py (CORRIGÉ)

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import UserRegistrationForm, UserLoginForm


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    # ✅ CRÉER LE FORMULAIRE (c'était manquant !)
    form = UserLoginForm()
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)  # ✅ Récupérer les données POST
        
        if form.is_valid():  # ✅ Valider le formulaire
            username = form.cleaned_data['username']  # ✅ Utiliser cleaned_data
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember', False)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                if not remember:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                
                messages.success(request, f'Bonjour {user.first_name} !')

                
                next_url = request.GET.get('next', 'dashboard:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Email ou mot de passe incorrect')
                form.add_error(None, 'Email ou mot de passe incorrect')  # ✅ Ajouter erreur au formulaire
    
    # ✅ PASSER LE FORMULAIRE AU TEMPLATE (c'était manquant !)
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Vue d'inscription"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    form = UserRegistrationForm()
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Bienvenue sur EpreuvesPro ! 🎉')
            return redirect('dashboard:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('accounts:login')  # ✅ Rediriger vers login, pas render


# Bonus : Vue profil
@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'abonnement': getattr(request.user, 'abonnement', None)
    })