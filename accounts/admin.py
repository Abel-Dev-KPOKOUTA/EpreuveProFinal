from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserActivity

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'email', 'first_name', 'last_name', 'phone', 
        'is_student', 'is_active', 'email_verified', 
        'date_joined'
    ]
    list_filter = [
        'is_student', 'is_teacher', 'is_active', 
        'email_verified', 'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Informations scolaires', {
            'fields': ('school', 'class_level', 'is_student', 'is_teacher')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'groups', 'user_permissions')
        }),
        ('Vérifications', {
            'fields': ('email_verified', 'phone_verified')
        }),
        ('Paiement', {
            'fields': ('fedapay_customer_id',),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    ordering = ['-date_joined']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'