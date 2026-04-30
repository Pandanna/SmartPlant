import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .factories import crea_utente, crea_dispositivo, crea_pianta


class DashboardTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.client.login(username='mario', password='Test1234!')
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def test_dashboard_status_200(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_richiede_login(self):
        self.client.logout()
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])

    def test_home_data_ritorna_json(self):
        r = self.client.get(reverse('home_data'))
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertIn('plants', data)

    def test_home_data_contiene_pianta(self):
        r = self.client.get(reverse('home_data'))
        data = json.loads(r.content)
        self.assertIn('esp32-test', data['plants'])

    def test_home_data_contiene_sensori(self):
        self.dispositivo.last_temp = 22.5
        self.dispositivo.last_hum = 45.0
        self.dispositivo.last_soil = 60.0
        self.dispositivo.save()
        r = self.client.get(reverse('home_data'))
        data = json.loads(r.content)
        sensori = data['plants']['esp32-test']['sensors']
        self.assertEqual(sensori['temperature'], 22.5)
        self.assertEqual(sensori['humidity'], 45.0)
        self.assertEqual(sensori['soil'], 60.0)

    def test_home_data_contiene_history(self):
        self.dispositivo.history = [{'ts': 1000, 'temperature': 20.0}]
        self.dispositivo.save()
        r = self.client.get(reverse('home_data'))
        data = json.loads(r.content)
        self.assertEqual(len(data['plants']['esp32-test']['history']), 1)

    def test_home_data_non_mostra_piante_altrui(self):
        altro = crea_utente('luigi')
        altro_disp = crea_dispositivo('esp32-luigi', '999999')
        crea_pianta(altro, altro_disp)
        r = self.client.get(reverse('home_data'))
        data = json.loads(r.content)
        self.assertNotIn('esp32-luigi', data['plants'])

    def test_home_data_richiede_login(self):
        self.client.logout()
        r = self.client.get(reverse('home_data'))
        self.assertEqual(r.status_code, 302)
