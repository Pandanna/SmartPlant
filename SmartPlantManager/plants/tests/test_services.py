from unittest.mock import patch, MagicMock
from django.test import TestCase
from plants.services import plantid_identify, openplantbook_get_care
from plants.models import PlantCareCache

PLANTID_OK_RESPONSE = {
    'result': {
        'is_plant': {'binary': True},
        'classification': {'suggestions': [{
            'name': 'Ficus benjamina',
            'probability': 0.92,
            'details': {'common_names': ['Ficus', 'Weeping fig']}
        }]}
    }
}

OPB_TOKEN_RESPONSE = {'access_token': 'token123'}

OPB_DETAIL_RESPONSE = {
    'min_temp': 15, 'max_temp': 30,
    'min_env_humid': 40, 'max_env_humid': 70,
    'min_soil_moist': 30, 'max_soil_moist': 60,
    'max_light_lux': 20000,
}


class PlantIdTest(TestCase):

    @patch('plants.services.requests.post')
    @patch('plants.services.openplantbook_get_care')
    def test_riconoscimento_ok(self, mock_opb, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = PLANTID_OK_RESPONSE
        mock_opb.return_value = {'temp_min': 15, 'temp_max': 30,
                                  'humidity_min': 40, 'humidity_max': 70,
                                  'soil_min': 30, 'soil_max': 60,
                                  'sunlight': 'part shade', 'watering': 'average'}
        result = plantid_identify('base64data')
        self.assertEqual(result['species'], 'Ficus benjamina')
        self.assertEqual(result['confidence'], 92)
        self.assertEqual(result['common_name'], 'Ficus')

    @patch('plants.services.requests.post')
    def test_immagine_non_pianta(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'result': {'is_plant': {'binary': False}, 'classification': {'suggestions': []}}
        }
        with self.assertRaises(ValueError) as ctx:
            plantid_identify('base64data')
        self.assertIn('non sembra contenere una pianta', str(ctx.exception))

    @patch('plants.services.requests.post')
    def test_confidence_troppo_bassa(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'result': {
                'is_plant': {'binary': True},
                'classification': {'suggestions': [
                    {'name': 'X', 'probability': 0.05, 'details': {}}
                ]}
            }
        }
        with self.assertRaises(ValueError):
            plantid_identify('base64data')

    @patch('plants.services.requests.post')
    def test_api_key_invalida_401(self, mock_post):
        mock_post.return_value.status_code = 401
        with self.assertRaises(ValueError) as ctx:
            plantid_identify('base64data')
        self.assertIn('API Key', str(ctx.exception))

    @patch('plants.services.requests.post')
    def test_rate_limit_429(self, mock_post):
        mock_post.return_value.status_code = 429
        with self.assertRaises(ValueError) as ctx:
            plantid_identify('base64data')
        self.assertIn('giornaliere', str(ctx.exception))

    @patch('plants.services.requests.post')
    def test_prefisso_base64_rimosso(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = PLANTID_OK_RESPONSE
        with patch('plants.services.openplantbook_get_care', return_value={}):
            plantid_identify('data:image/jpeg;base64,AAAA')
        called_payload = mock_post.call_args[1]['json']
        self.assertEqual(called_payload['images'][0], 'AAAA')


class OpenPlantbookTest(TestCase):

    def test_cache_hit_non_chiama_api(self):
        PlantCareCache.objects.create(
            pid='ficus benjamina',
            temp_min=15, temp_max=30,
            humidity_min=40, humidity_max=70,
            soil_min=30, soil_max=60,
            sunlight='part shade', watering='average',
        )
        with patch('plants.services.requests.post') as mock_post:
            result = openplantbook_get_care('Ficus benjamina')
            mock_post.assert_not_called()
        self.assertEqual(result['temp_min'], 15)

    @patch('plants.services.requests.post')
    @patch('plants.services.requests.get')
    def test_cache_miss_chiama_api(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = OPB_TOKEN_RESPONSE
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = OPB_DETAIL_RESPONSE
        result = openplantbook_get_care('Ficus benjamina')
        self.assertEqual(result['temp_min'], 15)
        self.assertEqual(result['sunlight'], 'part shade')

    @patch('plants.services.requests.post')
    @patch('plants.services.requests.get')
    def test_salva_in_cache_dopo_api(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = OPB_TOKEN_RESPONSE
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = OPB_DETAIL_RESPONSE
        openplantbook_get_care('Ficus benjamina')
        self.assertTrue(PlantCareCache.objects.filter(pid='ficus benjamina').exists())

    @patch('plants.services.requests.post')
    @patch('plants.services.requests.get')
    def test_specie_non_trovata_404(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = OPB_TOKEN_RESPONSE
        mock_get.return_value.status_code = 404
        with self.assertRaises(ValueError) as ctx:
            openplantbook_get_care('Specie inesistente')
        self.assertIn('non trovata', str(ctx.exception))

    @patch('plants.services.requests.post')
    @patch('plants.services.requests.get')
    def test_lux_alto_full_sun(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = OPB_TOKEN_RESPONSE
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {**OPB_DETAIL_RESPONSE, 'max_light_lux': 60000}
        result = openplantbook_get_care('Pianta Sole')
        self.assertEqual(result['sunlight'], 'full sun')

    @patch('plants.services.requests.post')
    @patch('plants.services.requests.get')
    def test_lux_basso_full_shade(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = OPB_TOKEN_RESPONSE
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {**OPB_DETAIL_RESPONSE, 'max_light_lux': 5000}
        result = openplantbook_get_care('Pianta Ombra')
        self.assertEqual(result['sunlight'], 'full shade')
