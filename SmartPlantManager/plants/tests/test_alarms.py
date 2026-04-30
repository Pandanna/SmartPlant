from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from plants.services import check_and_send_alarms
from .factories import crea_utente, crea_dispositivo, crea_pianta


class AllarmiTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.utente.telegram_chat_id = '123456789'
        self.utente.save()
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def _set_sensori(self, temp=None, hum=None, soil=None, battery=None):
        if temp is not None:     self.dispositivo.last_temp = temp
        if hum is not None:      self.dispositivo.last_hum = hum
        if soil is not None:     self.dispositivo.last_soil = soil
        if battery is not None:  self.dispositivo.last_battery = battery
        self.dispositivo.save()

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_allarme_temperatura_alta(self, mock_tg):
        self._set_sensori(temp=35.0)  # > temp_max (30)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()
        self.assertIn('Temperatura alta', mock_tg.call_args[0][1])

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_allarme_temperatura_bassa(self, mock_tg):
        self._set_sensori(temp=5.0)  # < temp_min (15)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()
        self.assertIn('Temperatura bassa', mock_tg.call_args[0][1])

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_allarme_umidita_aria_alta(self, mock_tg):
        self._set_sensori(hum=80.0)  # > humidity_max (70)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()
        self.assertIn('Umidità aria alta', mock_tg.call_args[0][1])

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_allarme_umidita_suolo_bassa(self, mock_tg):
        self._set_sensori(soil=10.0)  # < soil_min (30)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()
        self.assertIn('Umidità suolo bassa', mock_tg.call_args[0][1])

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_allarme_batteria_scarica(self, mock_tg):
        self._set_sensori(battery=10.0)  # < 20%
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()
        self.assertIn('Batteria scarica', mock_tg.call_args[0][1])

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_nessun_allarme_entro_soglie(self, mock_tg):
        self._set_sensori(temp=22.0, hum=55.0, soil=50.0, battery=80.0)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_not_called()

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_throttle_1_ora(self, mock_tg):
        self.pianta.last_alarm_sent = timezone.now() - timedelta(minutes=30)
        self.pianta.save()
        self._set_sensori(temp=35.0)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_not_called()

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_throttle_scaduto_dopo_1_ora(self, mock_tg):
        self.pianta.last_alarm_sent = timezone.now() - timedelta(hours=2)
        self.pianta.save()
        self._set_sensori(temp=35.0)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_called_once()

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_no_notifica_senza_telegram(self, mock_tg):
        self.utente.telegram_chat_id = None
        self.utente.save()
        self._set_sensori(temp=35.0)
        check_and_send_alarms(self.pianta)
        mock_tg.assert_not_called()

    @patch('plants.services.send_telegram_message', return_value=True)
    def test_aggiorna_last_alarm_sent(self, mock_tg):
        self._set_sensori(temp=35.0)
        check_and_send_alarms(self.pianta)
        self.pianta.refresh_from_db()
        self.assertIsNotNone(self.pianta.last_alarm_sent)
