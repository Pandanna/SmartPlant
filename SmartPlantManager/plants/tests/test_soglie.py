import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from .factories import crea_utente, crea_dispositivo, crea_pianta


class SoglieTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def _post(self, payload):
        return self.client.post(
            reverse('soglie'),
            json.dumps(payload),
            content_type='application/json',
        )

    def _payload_base(self, **kwargs):
        base = {
            'device_id': 'esp32-test',
            'temp_min': 18.0, 'temp_max': 26.0,
            'humidity_min': 50.0, 'humidity_max': 65.0,
            'soil_min': 35.0, 'soil_max': 75.0,
            'sunlight': 'part shade',
            'watering': 'frequent',
            'auto_irrigation': False,
        }
        base.update(kwargs)
        return base

    @patch('plants.views.publish_config')
    def test_aggiorna_soglie_ok(self, mock_config):
        r = self._post(self._payload_base())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(json.loads(r.content)['ok'])

    @patch('plants.views.publish_config')
    def test_soglie_salvate_nel_db(self, mock_config):
        self._post(self._payload_base(temp_min=18.0, temp_max=26.0))
        self.pianta.refresh_from_db()
        self.assertEqual(self.pianta.temp_min, 18.0)
        self.assertEqual(self.pianta.temp_max, 26.0)

    @patch('plants.views.publish_config')
    def test_watering_aggiornato(self, mock_config):
        self._post(self._payload_base(watering='frequent'))
        self.pianta.refresh_from_db()
        self.assertEqual(self.pianta.watering, 'frequent')

    @patch('plants.views.publish_config')
    def test_auto_irrigation_attivata(self, mock_config):
        self._post(self._payload_base(auto_irrigation=True))
        self.pianta.refresh_from_db()
        self.assertTrue(self.pianta.auto_irrigation)

    @patch('plants.views.publish_config')
    def test_chiama_publish_config(self, mock_config):
        self._post(self._payload_base())
        mock_config.assert_called_once()

    @patch('plants.views.publish_config')
    def test_soglie_pianta_altrui_negate(self, mock_config):
        altro = crea_utente('luigi')
        altro_disp = crea_dispositivo('esp32-luigi', '999999')
        crea_pianta(altro, altro_disp)
        r = self._post(self._payload_base(device_id='esp32-luigi'))
        self.assertEqual(r.status_code, 400)  # Http404 catturato da except Exception 400
        mock_config.assert_not_called()

    def test_richiede_login(self):
        self.client.logout()
        r = self._post(self._payload_base())
        self.assertEqual(r.status_code, 302)
