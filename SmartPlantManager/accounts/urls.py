from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('gestione/utenti/', views.admin_utenti, name='admin_utenti'),
    path('gestione/utenti/elimina/', views.admin_elimina_utente, name='admin_elimina_utente'),
    path('gestione/utenti/webhook/', views.admin_telegram_webhook_setup, name='admin_webhook'),
    path('profilo/', views.profile, name='profile'),
    path('api/telegram/webhook/', views.telegram_webhook, name='telegram_webhook'),
]
