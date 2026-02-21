from django.shortcuts import render, redirect

def accueil(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'core/base.html')