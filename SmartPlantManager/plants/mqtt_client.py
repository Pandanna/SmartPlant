import os
import json
import logging
import threading
import time
import ssl
import socket
from django.conf import settings
import paho.mqtt.client as mqtt
from .services import process_sensor_data
import traceback
from .services import run_auto_irrigation_check


logger = logging.getLogger(__name__)

def start_mqtt_listener():
    """
    Avvia il client MQTT in un thread separato.
    """
    def run_mqtt():
        client_id = f"django-server-{socket.gethostname()}"

        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logger.info(f"✅ Django MQTT Connesso (ID: {client_id})")
                client.subscribe("smartplant/+/+")
                logger.info("📡 Sottoscritto a: smartplant/+/+")
            else:
                # AWS spesso rifiuta connessioni per certificati errati o ID duplicati
                logger.error(f"❌ Connessione MQTT fallita (Codice: {rc})")

        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode('utf-8')
                logger.info(f"📩 MQTT Ricevuto: {msg.topic} -> {payload_str}")

                parts = msg.topic.split('/')
                if len(parts) < 3: return
                
                device_id = parts[1]
                sensor_type = parts[2]
                
                if sensor_type in ('config', 'irrigate'): return

                try:
                    data = json.loads(payload_str)
                    if isinstance(data, dict):
                        for key in ['temperature', 'humidity', 'soil', 'light', 'battery', 'rain']:
                            if key in data: process_sensor_data(device_id, key, data[key])
                    else:
                        process_sensor_data(device_id, sensor_type, data)
                except json.JSONDecodeError:
                    process_sensor_data(device_id, sensor_type, payload_str)

            except Exception as e:
                logger.error(f"🔥 Errore nel processare msg: {e}")

        # Inizializzazione Client
        try:
            # Supporto versione 2 di paho-mqtt
            if hasattr(mqtt, 'CallbackAPIVersion'):
                client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
            else:
                client = mqtt.Client(client_id=client_id)
                
            client.on_connect = on_connect
            client.on_message = on_message

            # Percorsi configurabili (Default locale: /certs/)
            certs_path = os.getenv('MQTT_CERTS_PATH', '/certs/')

            client.tls_set(
                ca_certs=os.path.join(certs_path, 'rootCA.pem'),
                certfile=os.path.join(certs_path, 'device.crt'),
                keyfile=os.path.join(certs_path, 'private.key'),
                tls_version=ssl.PROTOCOL_TLSv1_2,
                cert_reqs=ssl.CERT_REQUIRED,
            )
            
            logger.info(f"🔗 Connessione a AWS IoT: {settings.AWS_IOT_ENDPOINT}:{settings.AWS_IOT_PORT}...")
            client.connect(settings.AWS_IOT_ENDPOINT, int(settings.AWS_IOT_PORT), keepalive=60)
            client.loop_forever()
        except Exception as e:
            logger.error(f"💀 Errore fatale Loop MQTT: {e}\n{traceback.format_exc()}")

    def run_timer():
        time.sleep(30)
        
        while True:
            try:
                run_auto_irrigation_check()
            except Exception as e:
                logger.error(f"⏱️ Errore timer irrigazione: {e}")
            time.sleep(3600)

    # Avvio thread daemon
    threading.Thread(target=run_mqtt, daemon=True).start()
    threading.Thread(target=run_timer, daemon=True).start()
