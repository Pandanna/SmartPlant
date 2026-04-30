from django.test import TestCase
from plants.services import process_sensor_data
from plants.models import Dispositivo, Pianta
from .factories import crea_utente, crea_dispositivo, crea_pianta


class ProcessSensorDataTest(TestCase):

    def setUp(self):
        self.utente = crea_utente()
        self.dispositivo = crea_dispositivo()
        self.pianta = crea_pianta(self.utente, self.dispositivo)

    def test_aggiorna_temperatura(self):
        process_sensor_data('esp32-test', 'temperature', '22.5')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_temp, 22.5)

    def test_aggiorna_umidita_aria(self):
        process_sensor_data('esp32-test', 'humidity', '55.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_hum, 55.0)

    def test_aggiorna_umidita_suolo(self):
        process_sensor_data('esp32-test', 'soil', '45.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_soil, 45.0)

    def test_aggiorna_luce(self):
        process_sensor_data('esp32-test', 'light', '8500')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_light, 8500.0)

    def test_aggiorna_batteria(self):
        process_sensor_data('esp32-test', 'battery', '85.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_battery, 85.0)

    def test_aggiorna_pioggia_true(self):
        process_sensor_data('esp32-test', 'rain', 'true')
        self.dispositivo.refresh_from_db()
        self.assertTrue(self.dispositivo.last_rain)

    def test_aggiorna_pioggia_false(self):
        process_sensor_data('esp32-test', 'rain', 'false')
        self.dispositivo.refresh_from_db()
        self.assertFalse(self.dispositivo.last_rain)

    def test_alias_temp(self):
        process_sensor_data('esp32-test', 'temp', '20.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_temp, 20.0)

    def test_alias_hum(self):
        process_sensor_data('esp32-test', 'hum', '60.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_hum, 60.0)

    def test_alias_moisture(self):
        process_sensor_data('esp32-test', 'moisture', '40.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_soil, 40.0)

    def test_alias_batt(self):
        process_sensor_data('esp32-test', 'batt', '90.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_battery, 90.0)

    def test_tipo_sconosciuto_ritorna_false(self):
        result = process_sensor_data('esp32-test', 'co2', '400')
        self.assertFalse(result)

    def test_valore_non_numerico_ritorna_false(self):
        result = process_sensor_data('esp32-test', 'temperature', 'abc')
        self.assertFalse(result)

    def test_aggiorna_last_seen(self):
        process_sensor_data('esp32-test', 'temperature', '22.5')
        self.dispositivo.refresh_from_db()
        self.assertIsNotNone(self.dispositivo.last_seen)

    def test_history_append(self):
        process_sensor_data('esp32-test', 'temperature', '22.5')
        self.dispositivo.refresh_from_db()
        self.assertEqual(len(self.dispositivo.history), 1)
        self.assertEqual(self.dispositivo.history[0]['temperature'], 22.5)

    def test_history_max_2000(self):
        self.dispositivo.history = [{'ts': i} for i in range(2000)]
        self.dispositivo.save()
        process_sensor_data('esp32-test', 'temperature', '22.5')
        self.dispositivo.refresh_from_db()
        self.assertEqual(len(self.dispositivo.history), 2000)

    def test_sincronizza_temperatura_pianta(self):
        process_sensor_data('esp32-test', 'temperature', '25.0')
        self.pianta.refresh_from_db()
        self.assertEqual(self.pianta.last_temperature, 25.0)

    def test_sincronizza_umidita_pianta(self):
        process_sensor_data('esp32-test', 'humidity', '60.0')
        self.pianta.refresh_from_db()
        self.assertEqual(self.pianta.last_humidity, 60.0)

    def test_sincronizza_last_seen_pianta(self):
        process_sensor_data('esp32-test', 'temperature', '22.0')
        self.pianta.refresh_from_db()
        self.assertIsNotNone(self.pianta.last_seen)

    def test_device_sconosciuto_crea_dispositivo(self):
        result = process_sensor_data('esp32-nuovo', 'temperature', '20.0')
        self.assertTrue(result)
        self.assertTrue(Dispositivo.objects.filter(device_id='esp32-nuovo').exists())

    def test_device_case_insensitive(self):
        process_sensor_data('ESP32-TEST', 'temperature', '21.0')
        self.dispositivo.refresh_from_db()
        self.assertEqual(self.dispositivo.last_temp, 21.0)
