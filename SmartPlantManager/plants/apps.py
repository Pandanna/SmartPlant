from django.apps import AppConfig
import os

class PlantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plants'

    def ready(self):
        is_manage_py = any(arg.endswith('manage.py') for arg in os.sys.argv)
        is_runserver = 'runserver' in os.sys.argv
        
        if is_manage_py and is_runserver:
            if os.environ.get('RUN_MAIN') != 'true':
                return

        try:
            from .mqtt_client import start_mqtt_listener
            start_mqtt_listener()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Errore critico avvio MQTT in ready(): {e}")
