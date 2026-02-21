# apps/epreuves/urls.py

from django.urls import path
from . import views

app_name = 'epreuves'

urlpatterns = [
    # Liste des épreuves avec filtres
    path('liste/', views.liste_epreuves, name='liste'),
    
    # Détail d'une épreuve
    path('<slug:slug>/', views.detail_epreuve, name='detail'),
    
    # Téléchargement du sujet
    path('<slug:slug>/telecharger/', views.telecharger_epreuve, name='telecharger'),
    
    # Téléchargement du corrigé (nouveau)
    path('<slug:slug>/telecharger-corrige/', views.telecharger_corrige, name='telecharger_corrige'),
    
    # Toggle favori (AJAX)
    path('<slug:slug>/favori/', views.toggle_favori, name='favori'),
    
    # Mes épreuves téléchargées (optionnel)
    # path('mes-epreuves/', views.mes_epreuves, name='mes_epreuves'),
]