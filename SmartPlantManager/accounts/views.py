from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm
from .models import Utente
from .decorators import admin_required, login_required_custom
from plants.models import Pianta, Dispositivo
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
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


def _dispositivi_data():
    now = timezone.now()
    result = []
    for d in Dispositivo.objects.select_related('pianta', 'pianta__utente').order_by('device_id'):
        ha_pianta = hasattr(d, 'pianta')
        is_online = bool(d.last_seen and (now - d.last_seen) < timedelta(minutes=2))

        if d.last_seen:
            delta = now - d.last_seen
            secs = delta.total_seconds()
            if secs < 60:
                time_ago = 'Adesso'
            elif secs < 3600:
                time_ago = f'{int(secs // 60)}min fa'
            elif secs < 86400:
                time_ago = f'{int(secs // 3600)}h fa'
            else:
                time_ago = f'{delta.days}g fa'
        else:
            time_ago = 'Mai'

        result.append({
            'obj': d,
            'ha_pianta': ha_pianta,
            'pianta': d.pianta if ha_pianta else None,
            'is_online': is_online,
            'time_ago': time_ago,
        })
    return result


@login_required_custom
@admin_required
def admin_utenti(request):
    utenti = Utente.objects.all().order_by('created_at')
    piante_count = {
        u.username: Pianta.objects.filter(utente=u).count()
        for u in utenti
    }
    
    dispositivi = _dispositivi_data()
    stats = {
        'totale': len(dispositivi),
        'liberi': sum(1 for d in dispositivi if not d['ha_pianta']),
        'associati': sum(1 for d in dispositivi if d['ha_pianta']),
        'online': sum(1 for d in dispositivi if d['is_online']),
    }
    
    return render(request, 'admin_utenti.html', {
        'utenti': utenti,
        'piante_count': piante_count,
        'dispositivi': dispositivi,
        'stats': stats,
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
def admin_crea_dispositivo(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id', '').strip()
        if not device_id:
            messages.error(request, 'Inserisci un ID dispositivo.')
        elif Dispositivo.objects.filter(device_id=device_id).exists():
            messages.error(request, f'Il dispositivo "{device_id}" esiste già.')
        else:
            Dispositivo.objects.create(device_id=device_id)
            messages.success(request, f'Dispositivo "{device_id}" creato.')
    return redirect(reverse('admin_utenti') + '?tab=dispositivi')


@login_required_custom
@admin_required
def admin_rigenera_pin(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id', '').strip()
        try:
            d = Dispositivo.objects.get(device_id=device_id)
            import random, string
            d.pin = ''.join(random.choices(string.digits, k=6))
            d.save(update_fields=['pin'])
            messages.success(request, f'PIN rigenerato per "{device_id}"')
        except Dispositivo.DoesNotExist:
            messages.error(request, 'Dispositivo non trovato.')
    return redirect(reverse('admin_utenti') + '?tab=dispositivi')


@login_required_custom
@admin_required
def admin_elimina_dispositivo(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id', '').strip()
        try:
            d = Dispositivo.objects.get(device_id=device_id)
            if hasattr(d, 'pianta'):
                messages.error(request, f'Impossibile eliminare "{device_id}": ha una pianta collegata.')
            else:
                d.delete()
                messages.success(request, f'Dispositivo "{device_id}" eliminato.')
        except Dispositivo.DoesNotExist:
            messages.error(request, 'Dispositivo non trovato.')
    return redirect(reverse('admin_utenti') + '?tab=dispositivi')


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
            user = form.save(commit=False)
            avatar = request.POST.get('avatar', '').strip()
            
            if avatar:
                user.avatar = avatar
            user.save()
            
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