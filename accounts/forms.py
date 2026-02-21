# apps/accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User


class UserRegistrationForm(UserCreationForm):
    """
    Formulaire d'inscription
    """
    
    fullname = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Jean Dupont',
            'class': 'form-input'
        }),
        label='Nom complet'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'jean@exemple.com',
            'class': 'form-input'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '+229 01 23 45 67',
            'class': 'form-input'
        }),
        label='Téléphone'
    )
    
    # ✅ UTILISE CHARFIELD AU LIEU DE FOREIGNKEY
    niveau = forms.ChoiceField(
        choices=[
            ('', 'Sélectionne ton niveau'),
            ('college', 'Collège'),
            ('lycee', 'Lycée'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    classe = forms.ChoiceField(
        choices=[
            ('', 'Choisis ta classe'),
            ('6eme', '6ème'),
            ('5eme', '5ème'),
            ('4eme', '4ème'),
            ('3eme', '3ème'),
            ('2nde', '2nde'),
            ('1ere', '1ère'),
            ('terminale', 'Terminale'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    etablissement = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom de ton école',
            'class': 'form-input'
        }),
        label='Établissement'
    )
    
    newsletter = forms.BooleanField(required=False, initial=True)
    
    terms = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Vous devez accepter les conditions d\'utilisation.'
        }
    )
    
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'form-input'
        })
    )
    
    password2 = forms.CharField(
        label='Confirmer',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = User
        fields = ('fullname', 'email', 'phone', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Ce numéro est déjà enregistré.")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Nom complet
        fullname = self.cleaned_data.get('fullname', '')
        name_parts = fullname.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user.email = self.cleaned_data.get('email')
        user.phone = self.cleaned_data.get('phone')
        user.username = self.cleaned_data.get('email')  # Email = username
        
        # ✅ SAUVEGARDE EN CHARFIELD
        user.school = self.cleaned_data.get('etablissement', '')
        user.class_level = self.cleaned_data.get('classe', '')
        
        if commit:
            user.save()
        
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Email ou téléphone',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            'class': 'form-input'
        })
    )
    remember = forms.BooleanField(required=False)