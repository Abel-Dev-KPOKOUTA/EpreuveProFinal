from django.urls import path,include
from .import views

app_name = 'abonnements'

urlpatterns = [
    path('abonnements/' , views.abonnement , name='plans')
    
]
