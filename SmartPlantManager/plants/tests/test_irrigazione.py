import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from plants.models import IrrigazioneLog
from .factories import crea_utente, crea_dispositivo, crea_pianta


class IrrigazioneManualeTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def _post(self, payload):
        return self.client.post(
            reverse('irrigazione'),
            json.dumps(payload),
            content_type='application/json',
        )

    @patch('plants.views.publish_irrigazione')
    def test_irrigazione_ok(self, mock_pub):
        r = self._post({'device_id': 'esp32-test', 'duration': 30})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(json.loads(r.content)['ok'])

    @patch('plants.views.publish_irrigazione')
    def test_chiama_publish_irrigazione(self, mock_pub):
        self._post({'device_id': 'esp32-test', 'duration': 45})
        mock_pub.assert_called_once_with('esp32-test', 45)

    @patch('plants.views.publish_irrigazione')
    def test_crea_log_manuale(self, mock_pub):
        self._post({'device_id': 'esp32-test', 'duration': 30})
        self.assertEqual(IrrigazioneLog.objects.count(), 1)
        log = IrrigazioneLog.objects.first()
        self.assertEqual(log.trigger, 'manuale')
        self.assertEqual(log.duration, 30)

    @patch('plants.views.publish_irrigazione')
    def test_aggiorna_last_irrigation(self, mock_pub):
        self._post({'device_id': 'esp32-test', 'duration': 30})
        self.pianta.refresh_from_db()
        self.assertIsNotNone(self.pianta.last_irrigation)

    @patch('plants.views.publish_irrigazione')
    def test_irrigazione_pianta_altrui_negata(self, mock_pub):
        altro = crea_utente('luigi')
        altro_disp = crea_dispositivo('esp32-luigi', '999999')
        crea_pianta(altro, altro_disp)
        r = self._post({'device_id': 'esp32-luigi', 'duration': 30})
        self.assertEqual(r.status_code, 400)  # Http404 catturato da except Exception 400
        mock_pub.assert_not_called()
        self.assertEqual(IrrigazioneLog.objects.count(), 0)

    def test_richiede_login(self):
        self.client.logout()
        r = self._post({'device_id': 'esp32-test', 'duration': 30})
        self.assertEqual(r.status_code, 302)
