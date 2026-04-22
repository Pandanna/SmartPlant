from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principale
    path('home/', views.home, name='home'),
    
    # Pagina di Dettaglio Pianta
    path('pianta/<str:device_id>/', views.dettaglio_pianta, name='dettaglio_pianta'),
    
    # API per la Dashboard e Dettaglio
    path('home/data/', views.home_data, name='home_data'),
    path('home/soglie/', views.soglie, name='soglie'),
    path('home/irrigazione/', views.irrigazione, name='irrigazione'),
    path('home/elimina/', views.elimina, name='elimina'),
    path('home/aggiorna-profilo/', views.aggiorna_profilo_pianta, name='aggiorna_profilo'),
    
    # Registrazione pianta
    path('registra/', views.registra, name='registra'),
    path('registra/valida/', views.valida_dispositivo, name='valida_dispositivo'),
    path('registra/analizza/', views.registra_analizza, name='registra_analizza'),
]