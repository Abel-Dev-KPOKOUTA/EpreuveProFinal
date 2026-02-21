# apps/livres/urls.py

from django.urls import path
from . import views

app_name = 'livres'

urlpatterns = [
    path('', views.bibliotheque, name='bibliotheque'),
    path('<slug:slug>/', views.detail_livre, name='detail'),
    path('<slug:slug>/lire/', views.lecture_livre, name='lecture'),
    path('<slug:slug>/telecharger/', views.telecharger_livre, name='telecharger'),
    path('<slug:slug>/progression/', views.sauvegarder_progression, name='progression'),
    path('<slug:slug>/avis/', views.ajouter_avis, name='avis'),
]