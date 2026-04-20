from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('gestione/utenti/', views.admin_utenti, name='admin_utenti'),
    path('gestione/utenti/elimina/', views.admin_elimina_utente, name='admin_elimina_utente'),
    path('gestione/utenti/webhook/', views.admin_telegram_webhook_setup, name='admin_webhook'),
    path('gestione/dispositivi/crea/', views.admin_crea_dispositivo, name='admin_crea_dispositivo'),
    path('gestione/dispositivi/rigenera-pin/', views.admin_rigenera_pin, name='admin_rigenera_pin'),
    path('gestione/dispositivi/elimina/', views.admin_elimina_dispositivo, name='admin_elimina_dispositivo'),
    path('profilo/', views.profile, name='profile'),
    path('api/telegram/webhook/', views.telegram_webhook, name='telegram_webhook'),
]
