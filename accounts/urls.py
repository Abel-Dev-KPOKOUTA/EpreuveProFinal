from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='profile_update'),
    path('preferences/', views.preferences_view, name='preferences'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
]