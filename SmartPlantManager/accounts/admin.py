from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utente

class UtenteAdmin(UserAdmin):
    model = Utente
    list_display = ('username', 'email', 'is_admin', 'is_staff', 'is_active')
    list_filter = ('is_admin', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'telegram', 'password')}),
        ('Permessi', {'fields': ('is_admin', 'is_staff', 'is_active', 'is_superuser')}),
        ('Date importanti', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
        'classes': ('wide',),
        'fields':  ('username', 'email', 'password1', 'password2', 'is_admin', 'is_staff', 'is_active'),
    }),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(Utente, UtenteAdmin)