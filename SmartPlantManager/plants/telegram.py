import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text):
    if not settings.TELEGRAM_TOKEN or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Errore invio Telegram: {e}")
        return False
