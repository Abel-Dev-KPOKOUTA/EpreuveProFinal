# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('epreuves/', views.epreuves_list, name='epreuves'),
    path('downloads/', views.downloads_history, name='downloads'),
    path('abonnement/', views.abonnement_view, name='abonnement'),
    path('profil/', views.profile_view, name='profile'),
]