from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm
from .models import Utente
from .decorators import admin_required, login_required_custom
from plants.models import Pianta
from django.db.models import Q
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging


def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())

        return redirect('home')

    return render(request, 'login.html', {'form': form})


def logout(request):
    auth_logout(request)

    return redirect('login')


def register(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account creato. Accedi ora.')

        return redirect('login')

    return render(request, 'register.html', {'form': form})


@login_required_custom
@admin_required
def admin_utenti(request):
    utenti = Utente.objects.all().order_by('created_at')

    # Conta piante per utente
    piante_count = {
        u.username: Pianta.objects.filter(utente=u).count()
        for u in utenti
    }

    return render(request, 'admin_utenti.html', {
        'utenti': utenti,
        'piante_count': piante_count,
    })


@login_required_custom
@admin_required
def admin_elimina_utente(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        if username == request.user.username:
            messages.error(request, 'Non puoi eliminare te stesso.')

            return redirect('admin_utenti')
        
        try:
            utente = Utente.objects.get(username=username)
            utente.delete()
            messages.success(request, f'Utente {username} eliminato.')

        except Utente.DoesNotExist:
            messages.error(request, 'Utente non trovato.')

    return redirect('admin_utenti')


@login_required_custom
@admin_required
def admin_telegram_webhook_setup(request):
    if not settings.TELEGRAM_TOKEN:
        messages.error(request, 'TELEGRAM_TOKEN non configurato.')
        return redirect('admin_utenti')
        
    host = request.get_host()
    # Telegram richiede HTTPS. I tunnel (Cloudflare, Ngrok) lo forniscono sempre.
    scheme = 'https'
    webhook_url = f"{scheme}://{host}/api/telegram/webhook/"

    api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, data={'url': webhook_url})
        data = response.json()
        if data.get('ok'):
            messages.success(request, f'Webhook Telegram configurato con successo su: {webhook_url}')
        else:
            messages.error(request, f'Errore Telegram: {data.get("description")}')
    except Exception as e:
        messages.error(request, f'Errore di connessione: {e}')
        
    return redirect('admin_utenti')


@login_required_custom
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilo aggiornato con successo!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'profile.html', {'form': form})

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if 'message' in data:
                message = data['message']
                chat_id = message.get('chat', {}).get('id')
                text = message.get('text', '')
                username = message.get('from', {}).get('username', '')

                if text.startswith('/start'):
                    if username:
                        username_with_at = f"@{username}"
                        try:
                            # Troviamo l'utente che ha questo username Telegram (con o senza @)
                            utente = Utente.objects.filter(
                                Q(telegram=username_with_at) | Q(telegram=username)
                            ).first()
                            
                            if utente:
                                utente.telegram_chat_id = str(chat_id)
                                utente.save()
                                # Mandiamo conferma opzionale
                                if settings.TELEGRAM_TOKEN:
                                    requests.post(
                                        f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage",
                                        json={
                                            "chat_id": chat_id,
                                            "text": f"Benvenuto/a {utente.username}! Notifiche attivate per le tue piante."
                                        }
                                    )
                        except Exception as e:
                            logging.getLogger(__name__).error(f"Errore webhook telegram: {e}")
                            
            return JsonResponse({"ok": True})
        except json.JSONDecodeError:
            pass
    return JsonResponse({"ok": False})