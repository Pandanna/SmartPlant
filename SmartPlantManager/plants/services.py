"""
services.py — Logica di business centralizzata per SmartPlant.
"""
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from django.db import connection
import paho.mqtt.publish as publish
import ssl
from .telegram import send_telegram_message
from datetime import timedelta
from .models import Dispositivo, Pianta
from .models import Pianta, IrrigazioneLog
from .telegram import send_telegram_message
import datetime

logger = logging.getLogger(__name__)

# --- UTILITY ---

def to_bool(val):
    if isinstance(val, bool): return val
    if isinstance(val, (int, float)): return bool(val)
    if isinstance(val, str):
        v = val.lower().strip()
        if v in ('true', '1', 'yes', 'on', 'sì'): return True
        if v in ('false', '0', 'no', 'off'): return False
    return False

# --- ALLARMI ---

def check_and_send_alarms(pianta):
    """
    Controlla se i valori dei sensori sono fuori soglia e invia notifica Telegram.
    """

    # Verifica se l'utente ha Telegram configurato
    if not hasattr(pianta.utente, 'telegram_chat_id') or not pianta.utente.telegram_chat_id:
        return
        
    # non invia più di un allarme ogni ora per la stessa pianta
    if pianta.last_alarm_sent and (timezone.now() - pianta.last_alarm_sent) < timedelta(hours=1):
        return
        
    d = pianta.dispositivo
    allarme = None
    
    # 1. Temperatura
    if d.last_temp is not None:
        if d.last_temp > pianta.temp_max:
            allarme = f"Temperatura alta: {d.last_temp}°C (max {pianta.temp_max}°C)"
        elif d.last_temp < pianta.temp_min:
            allarme = f"Temperatura bassa: {d.last_temp}°C (min {pianta.temp_min}°C)"
            
    # 2. Umidità Aria
    if not allarme and d.last_hum is not None:
        if d.last_hum > pianta.humidity_max:
            allarme = f"Umidità aria alta: {d.last_hum}% (max {pianta.humidity_max}%)"
        elif d.last_hum < pianta.humidity_min:
            allarme = f"Umidità aria bassa: {d.last_hum}% (min {pianta.humidity_min}%)"

    # 3. Umidità Suolo
    if not allarme and d.last_soil is not None:
        if d.last_soil > pianta.soil_max:
            allarme = f"Umidità suolo alta: {d.last_soil}% (max {pianta.soil_max}%)"
        elif d.last_soil < pianta.soil_min:
            allarme = f"Umidità suolo bassa: {d.last_soil}% (min {pianta.soil_min}%)"
            
    # 4. Batteria
    if not allarme and d.last_battery is not None and d.last_battery < 20:
        allarme = f"Batteria scarica: {d.last_battery}%"
        
    if allarme:
        msg = f"⚠️ *Allarme {pianta.nickname}*\n{allarme}"
        if send_telegram_message(pianta.utente.telegram_chat_id, msg):
            pianta.last_alarm_sent = timezone.now()
            pianta.save(update_fields=['last_alarm_sent'])
            logger.info(f"Notifica Telegram inviata per {pianta.nickname}")

# --- ELABORAZIONE DATI ---

def process_sensor_data(device_id, sensor_type, value):
    """
    Riceve un dato, aggiorna Dispositivo e Pianta, gestisce lo storico e gli allarmi.
    """

    try:
        # 0. Sincronizzazione thread-safe database
        if connection.connection and not connection.is_usable():
            connection.close()

        # 1. Registra o recupera il dispositivo
        dispositivo, created = Dispositivo.objects.get_or_create(device_id=device_id.strip())
        
        # Mappatura tipi sensore
        mapping = {
            'temp': 'temperature', 'temperature': 'temperature',
            'hum': 'humidity', 'humidity': 'humidity',
            'soil': 'soil', 'moisture': 'soil',
            'light': 'light', 'lux': 'light',
            'batt': 'battery', 'battery': 'battery',
            'rain': 'rain', 'water': 'rain'
        }
        
        real_type = mapping.get(sensor_type.lower())
        if not real_type:
            logger.warning(f"Tipo sensore sconosciuto: {sensor_type}")
            return False

        # 2. Aggiorna il valore specifico
        try:
            if real_type == 'temperature': dispositivo.last_temp = float(value)
            elif real_type == 'humidity':    dispositivo.last_hum = float(value)
            elif real_type == 'soil':        dispositivo.last_soil = float(value)
            elif real_type == 'light':       dispositivo.last_light = float(value)
            elif real_type == 'battery':     dispositivo.last_battery = float(value)
            elif real_type == 'rain':        dispositivo.last_rain = to_bool(value)
        except (ValueError, TypeError):
            logger.error(f"Valore non valido per {real_type}: {value}")
            return False
        
        dispositivo.last_seen = timezone.now()

        # 3. Aggiorna lo storico
        history = dispositivo.history if isinstance(dispositivo.history, list) else []
        history.append({
            'ts': int(timezone.now().timestamp() * 1000),
            'temperature': dispositivo.last_temp,
            'humidity':    dispositivo.last_hum,
            'soil':        dispositivo.last_soil,
            'light':       dispositivo.last_light,
            'battery':     dispositivo.last_battery,
            'rain':        dispositivo.last_rain
        })
        dispositivo.history = history[-2000:]
        dispositivo.save()

        # 4. Sincronizza con la Pianta associata
        try:
            p = Pianta.objects.get(dispositivo=dispositivo)
            p.last_temp = dispositivo.last_temp
            p.last_hum = dispositivo.last_hum
            p.last_soil = dispositivo.last_soil
            p.last_light = dispositivo.last_light
            p.last_rain = dispositivo.last_rain
            p.last_battery = dispositivo.last_battery
            p.save()
            
            # 5. Controlla allarmi
            check_and_send_alarms(p)
            logger.info(f"✅ Dati {real_type} salvati per {device_id}")
        except Pianta.DoesNotExist:
            logger.debug(f"Dispositivo {device_id} aggiornato (nessuna pianta associata)")
            
        return True
    except Exception as e:
        logger.error(f"❌ Errore process_sensor_data ({device_id}, {sensor_type}): {e}")
        return False
    finally:
        connection.close()

def run_auto_irrigation_check():
    """
    Timer orario per irrigazione automatica.
    """

    if connection.connection and not connection.is_usable():
        connection.close()

    try:
        WATERING_DAYS = {'frequent': 2, 'average': 4, 'minimum': 7, 'none': 14}
        piante = Pianta.objects.filter(auto_irrigation=True).select_related('dispositivo', 'utente')
        
        for p in piante:
            days = WATERING_DAYS.get(p.watering, 4)
            last_ts = p.last_irrigation or timezone.make_aware(datetime.datetime.min)
            elapsed = (timezone.now() - last_ts).total_seconds() / 86400

            if elapsed >= days:
                publish_irrigazione(p.dispositivo.device_id, 30)
                p.last_irrigation = timezone.now()
                p.save(update_fields=['last_irrigation'])
                IrrigazioneLog.objects.create(pianta=p, duration=30, trigger='automatica')
                if p.utente.telegram_chat_id:
                    msg = f"🤖 *Irrigazione automatica*\n🪴 {p.nickname}\n⏱️ Durata: 30s"
                    send_telegram_message(p.utente.telegram_chat_id, msg)
    finally:
        connection.close()

# --- MQTT PUBLISH ---

def publish_mqtt(topic: str, payload: dict, qos: int = 1, retain: bool = False):
    try:
        publish.single(
            topic = topic, payload = json.dumps(payload), qos = qos, retain = retain,
            hostname = settings.AWS_IOT_ENDPOINT, port = settings.AWS_IOT_PORT,
            tls = {
                'ca_certs': '/certs/rootCA.pem',
                'certfile': '/certs/device.crt',
                'keyfile': '/certs/private.key',
                'tls_version': ssl.PROTOCOL_TLSv1_2,
                'cert_reqs': ssl.CERT_REQUIRED,
            }
        )
    except Exception as e:
        logger.error(f"Errore MQTT publish: {e}")

def publish_irrigazione(device_id: str, duration: int):
    """Richiesta irrigazione via AWS Shadow (stato desired)"""
    topic = f"$aws/things/{device_id}/shadow/update"
    payload = {
        "state": {
            "desired": {
                "pump": True,
                "duration": duration
            }
        }
    }
    publish_mqtt(topic, payload)
    logger.info(f"Comando pump:True inviato alla shadow di {device_id}")

def publish_config(device_id: str, params: dict):
    """Aggiornamento soglie via AWS Shadow (stato desired)"""
    topic = f"$aws/things/{device_id}/shadow/update"
    payload = {
        "state": {
            "desired": params
        }
    }
    publish_mqtt(topic, payload)
    logger.info(f"Nuove soglie inviate alla shadow di {device_id}")

def publish_event(event_type: str, payload: dict):
    """Evento generico per servizi esterni"""
    publish_mqtt(f"smart_plants/events/{event_type}", payload, retain=False)

def plantid_identify(image_base64: str) -> dict:
    # Rimuoviamo il prefisso data:image/...;base64, se presente
    if ',' in image_base64:
        image_base64 = image_base64.split(',', 1)[1]

    api_key = settings.PLANTID_API_KEY
    url = 'https://plant.id/api/v3/identification?details=common_names,watering,best_light_condition'
    resp = requests.post(url, headers={'Api-Key': api_key}, json={'images': [image_base64]}, timeout=30)

    if resp.status_code not in (200, 201): 
        raise ValueError(f"Plant.id errore {resp.status_code}")
    
    data = resp.json()
    result = data.get('result', {})

    if result.get('is_plant', {}).get('binary') is False: 
        raise ValueError("Immagine non valida.")
    
    suggestions = result.get('classification', {}).get('suggestions', [])

    if not suggestions: 
        raise ValueError("Pianta non riconosciuta.")
    
    best = suggestions[0]
    confidence = round(best['probability'] * 100)
    species = best['name']
    details = best.get('details', {})
    common_name = details.get('common_names', [species])[0]
    watering = 'average'
    w = details.get('watering', {})

    if w.get('min') is not None and w.get('max') is not None:
        avg = (w['min'] + w['max']) / 2
        if avg >= 4: watering = 'frequent'
        elif avg >= 2.5: watering = 'average'
        elif avg >= 1.5: watering = 'minimum'
        else: watering = 'none'

    sunlight = 'full sun'
    lc = (details.get('best_light_condition') or '').lower()

    if 'shade' in lc or 'low' in lc: 
        sunlight = 'full shade'
    elif 'part' in lc or 'indirect' in lc: 
        sunlight = 'part shade'

    hum_map = {'frequent': (60, 80), 'average': (40, 70), 'minimum': (25, 50), 'none': (20, 40)}
    hum_min, hum_max = hum_map[watering]
    
    return {
        'species': species, 'common_name': common_name, 'confidence': confidence,
        'params': {
            'temp_min': 15, 'temp_max': 30, 'humidity_min': hum_min, 'humidity_max': hum_max,
            'watering': watering, 'sunlight': sunlight,
        }
    }
