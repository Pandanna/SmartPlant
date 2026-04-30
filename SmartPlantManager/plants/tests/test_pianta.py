import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from plants.models import Pianta, Dispositivo
from .factories import crea_utente, crea_dispositivo, crea_pianta

MOCK_PLANTID_RESULT = {
    'species': 'Ficus benjamina',
    'common_name': 'Ficus',
    'confidence': 92,
    'params': {
        'temp_min': 15, 'temp_max': 30,
        'humidity_min': 40, 'humidity_max': 70,
        'soil_min': 30, 'soil_max': 60,
        'sunlight': 'part shade', 'watering': 'average',
    }
}


class ValidaDispositivoTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo('esp32-test', '123456')

    def _post(self, payload):
        return self.client.post(
            reverse('valida_dispositivo'),
            json.dumps(payload),
            content_type='application/json',
        )

    def test_valida_ok(self):
        r = self._post({'device_id': 'esp32-test', 'pin': '123456'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(json.loads(r.content)['ok'])

    def test_pin_errato(self):
        r = self._post({'device_id': 'esp32-test', 'pin': '000000'})
        self.assertEqual(r.status_code, 404)

    def test_device_inesistente(self):
        r = self._post({'device_id': 'esp32-xxxx', 'pin': '123456'})
        self.assertEqual(r.status_code, 404)

    def test_device_gia_associato(self):
        crea_pianta(self.utente, self.dispositivo)
        r = self._post({'device_id': 'esp32-test', 'pin': '123456'})
        self.assertEqual(r.status_code, 400)

    def test_richiede_login(self):
        self.client.logout()
        r = self._post({'device_id': 'esp32-test', 'pin': '123456'})
        self.assertEqual(r.status_code, 302)


class RegistraAnalizzaTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo('esp32-test', '123456')

    def _post(self, payload):
        return self.client.post(
            reverse('registra_analizza'),
            json.dumps(payload),
            content_type='application/json',
        )

    @patch('plants.views.plantid_identify', return_value=MOCK_PLANTID_RESULT)
    @patch('plants.services.publish_mqtt')
    def test_registrazione_automatica_crea_pianta(self, mock_mqtt, mock_plantid):
        r = self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'Il mio ficus',
            'image': 'data:image/jpeg;base64,/9j/abc',
            'manual': False,
        })
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Pianta.objects.filter(dispositivo=self.dispositivo).exists())

    @patch('plants.views.plantid_identify', return_value=MOCK_PLANTID_RESULT)
    @patch('plants.services.publish_mqtt')
    def test_registrazione_automatica_dati_corretti(self, mock_mqtt, mock_plantid):
        self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'Il mio ficus',
            'image': 'data:image/jpeg;base64,/9j/abc',
            'manual': False,
        })
        pianta = Pianta.objects.get(dispositivo=self.dispositivo)
        self.assertEqual(pianta.nickname, 'Il mio ficus')
        self.assertEqual(pianta.species, 'Ficus benjamina')
        self.assertEqual(pianta.temp_min, 15)
        self.assertEqual(pianta.temp_max, 30)

    @patch('plants.views.plantid_identify', return_value=MOCK_PLANTID_RESULT)
    @patch('plants.services.publish_mqtt')
    def test_registrazione_chiama_publish_config(self, mock_mqtt, mock_plantid):
        self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'test', 'image': 'base64...', 'manual': False,
        })
        mock_mqtt.assert_called()

    @patch('plants.services.publish_mqtt')
    def test_registrazione_manuale(self, mock_mqtt):
        r = self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'Pianta manuale',
            'manual': {
                'species': 'Specie sconosciuta',
                'common_name': 'Pianta',
                'confidence': 0,
                'params': {
                    'temp_min': 10, 'temp_max': 35,
                    'humidity_min': 30, 'humidity_max': 80,
                    'soil_min': 20, 'soil_max': 70,
                    'sunlight': 'full sun', 'watering': 'average',
                }
            },
        })
        self.assertEqual(r.status_code, 201)
        pianta = Pianta.objects.get(dispositivo=self.dispositivo)
        self.assertTrue(pianta.manual)

    @patch('plants.views.plantid_identify', side_effect=ValueError("Pianta non riconosciuta."))
    def test_plantid_fallisce_ritorna_422(self, mock_plantid):
        r = self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'test', 'image': 'base64...', 'manual': False,
        })
        self.assertEqual(r.status_code, 422)
        self.assertFalse(Pianta.objects.filter(dispositivo=self.dispositivo).exists())

    def test_senza_immagine_e_non_manual_ritorna_400(self):
        r = self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'test', 'manual': False,
        })
        self.assertEqual(r.status_code, 400)

    def test_dispositivo_gia_associato(self):
        crea_pianta(self.utente, self.dispositivo)
        r = self._post({
            'device_id': 'esp32-test', 'pin': '123456',
            'nickname': 'secondo tentativo', 'manual': False,
        })
        self.assertEqual(r.status_code, 400)

    def test_pin_errato_ritorna_404(self):
        r = self._post({
            'device_id': 'esp32-test', 'pin': '000000',
            'nickname': 'test', 'manual': False,
        })
        self.assertEqual(r.status_code, 404)


class EliminaTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def test_elimina_pianta_ok(self):
        r = self.client.post(
            reverse('elimina'),
            json.dumps({'device_id': 'esp32-test'}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Pianta.objects.filter(dispositivo=self.dispositivo).exists())

    def test_dispositivo_rimane_dopo_eliminazione(self):
        self.client.post(
            reverse('elimina'),
            json.dumps({'device_id': 'esp32-test'}),
            content_type='application/json',
        )
        self.assertTrue(Dispositivo.objects.filter(device_id='esp32-test').exists())

    def test_elimina_pianta_altrui_negato(self):
        altro = crea_utente('luigi')
        altro_disp = crea_dispositivo('esp32-luigi', '999999')
        crea_pianta(altro, altro_disp)
        r = self.client.post(
            reverse('elimina'),
            json.dumps({'device_id': 'esp32-luigi'}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 400)  # Http404 catturato da except Exception 400
        self.assertTrue(Pianta.objects.filter(dispositivo=altro_disp).exists())
