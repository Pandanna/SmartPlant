import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from accounts.decorators import login_required_custom
from .models import Dispositivo, Pianta, IrrigazioneLog
from .services import publish_irrigazione, publish_config, publish_event, plantid_identify
import logging


#  PAGINE HTML 

@login_required_custom
def home(request):
    """Renderizza la Dashboard principale"""
    return render(request, 'dashboard.html')


@login_required_custom
def dettaglio_pianta(request, device_id):
    """Renderizza la pagina di dettaglio di una singola pianta"""
    if request.user.is_admin:
        pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id)
    else:
        pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id, utente=request.user)
        
    return render(request, 'dettaglio.html', {'pianta': pianta})


#  API DATI E AZIONI 

@login_required_custom
@require_GET
def home_data(request):
    """API JSON consumata dal frontend per aggiornare sensori e salute"""
    piante = Pianta.objects.select_related('dispositivo', 'utente').filter(
        utente=request.user
    )

    result = {}

    for p in piante:
        logs = list(
            p.irrigation_logs.values('timestamp', 'duration', 'trigger')[:20]
        )

        result[p.dispositivo.device_id] = {
            'nickname': p.nickname,
            'species': p.species,
            'common_name': p.common_name,
            'device_id': p.dispositivo.device_id,
            'owner': p.utente.username,
            'image': p.image if p.image else None,
            'last_seen': int(p.dispositivo.last_seen.timestamp() * 1000) if getattr(p.dispositivo, 'last_seen', None) else None,
            'sensors': {
                'temperature': getattr(p.dispositivo, 'last_temp', None),
                'humidity': getattr(p.dispositivo, 'last_hum', None),
                'soil': getattr(p.dispositivo, 'last_soil', None),
                'light': getattr(p.dispositivo, 'last_light', None),
                'battery': getattr(p.dispositivo, 'last_battery', None),
                'rain': getattr(p.dispositivo, 'last_rain', None),
            },
            'params': p.params_dict(),
            'last_irrigation': p.last_irrigation.isoformat() if p.last_irrigation else None,
            'irrigation_log': [{'ts': l['timestamp'].isoformat(), 'duration': l['duration'], 'trigger': l['trigger']} for l in logs],
            'history': getattr(p.dispositivo, 'history', []),
        }

    return JsonResponse({'plants': result})


@login_required_custom
@require_POST
def soglie(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')

        if request.user.is_admin:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id)
        else:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id, utente=request.user)

        pianta.temp_min = data.get('temp_min', pianta.temp_min)
        pianta.temp_max = data.get('temp_max', pianta.temp_max)
        pianta.humidity_min = data.get('humidity_min', pianta.humidity_min)
        pianta.humidity_max = data.get('humidity_max', pianta.humidity_max)
        pianta.soil_min = data.get('soil_min', pianta.soil_min)
        pianta.soil_max = data.get('soil_max', pianta.soil_max)
        pianta.sunlight = data.get('sunlight', pianta.sunlight)
        pianta.watering = data.get('watering', pianta.watering)
        
        if 'auto_irrigation' in data:
            pianta.auto_irrigation = data['auto_irrigation']

        pianta.save()
        publish_config(device_id, pianta.params_dict())

        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required_custom
@require_POST
def irrigazione(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        duration = data.get('duration', 30)

        if request.user.is_admin:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id)
        else:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id, utente=request.user)

        publish_irrigazione(device_id, duration)
        pianta.last_irrigation = timezone.now()
        pianta.save()

        IrrigazioneLog.objects.create(
            pianta=pianta,
            duration=duration,
            trigger='manuale'
        )

        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required_custom
@require_POST
def elimina(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')

        if request.user.is_admin:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id)
        else:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id, utente=request.user)

        pianta.delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required_custom
@require_POST
def aggiorna_profilo_pianta(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        nickname = data.get('nickname')
        species = data.get('species')
        image = data.get('image')

        if request.user.is_admin:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id)
        else:
            pianta = get_object_or_404(Pianta, dispositivo__device_id=device_id, utente=request.user)

        if nickname: pianta.nickname = nickname
        if species:  pianta.species = species
        if image:    pianta.image = image

        pianta.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


#  REGISTRAZIONE PIANTA 

@login_required_custom
def registra(request):
    return render(request, 'registra.html')


@login_required_custom
@require_POST
def valida_dispositivo(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        pin = data.get('pin')

        dispositivo = Dispositivo.objects.get(device_id=device_id, pin=pin)
        
        if hasattr(dispositivo, 'pianta'):
            return JsonResponse({'error': 'Questo dispositivo è già associato a una pianta.'}, status=400)
            
        return JsonResponse({'ok': True})
    except Dispositivo.DoesNotExist:
        return JsonResponse({'error': 'ID Dispositivo o PIN non validi.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required_custom
@require_POST
def registra_analizza(request):
    data = json.loads(request.body)
    image = data.get('image')
    device_id = data.get('device_id')
    pin = data.get('pin')
    nickname = data.get('nickname')
    manual = data.get('manual')

    logger = logging.getLogger(__name__)
    logger.warning(f"[registra_analizza] device={device_id} manual={'SI' if manual else 'NO'} image={'SI' if image else 'NO'}")

    # Verifica ID e PIN
    dispositivo = get_object_or_404(Dispositivo, device_id=device_id, pin=pin)
    
    if hasattr(dispositivo, 'pianta'):
        return JsonResponse({'error': 'Dispositivo già associato a un\'altra pianta'}, status=400)

    if manual:
        result = manual
    else:
        if not image:
            return JsonResponse({'error': 'Nessuna immagine fornita.'}, status=400)
        try:
            result = plantid_identify(image)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=422)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': 'Si è verificato un errore interno nel server. Riprova più tardi.'}, status=500)

    params = result['params']
    pianta = Pianta.objects.create(
        dispositivo = dispositivo,
        utente = request.user,
        nickname = nickname,
        species = result['species'],
        common_name = result['common_name'],
        image = image or '',
        temp_min = params.get('temp_min', 15),
        temp_max = params.get('temp_max', 30),
        humidity_min = params.get('humidity_min', 40),
        humidity_max = params.get('humidity_max', 70),
        soil_min = params.get('soil_min', 30),
        soil_max = params.get('soil_max', 80),
        sunlight = params.get('sunlight', 'full sun'),
        watering = params.get('watering', 'average'),
        manual = (result['confidence'] == 0),
    )

    publish_config(device_id, pianta.params_dict())

    publish_event('registrazione', {
        'device_id': device_id,
        'nickname': nickname,
        'common_name': result['common_name'],
        'species': result['species'],
        'confidence': result['confidence'],
        'utente': request.user.username,
        'params': pianta.params_dict(),
    })

    return JsonResponse({
        'species': result['species'],
        'common_name': result['common_name'],
        'confidence': result['confidence'],
        'params': params
    }, status=201)