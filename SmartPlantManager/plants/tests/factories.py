from accounts.models import Utente
from plants.models import Dispositivo, Pianta


def crea_utente(username='mario', password='Test1234!', is_admin=False):
    return Utente.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password=password,
        is_admin=is_admin,
    )


def crea_dispositivo(device_id='esp32-test', pin='123456'):
    return Dispositivo.objects.create(device_id=device_id, pin=pin)


def crea_pianta(utente, dispositivo, nickname='Ficus test'):
    return Pianta.objects.create(
        dispositivo=dispositivo,
        utente=utente,
        nickname=nickname,
        species='Ficus benjamina',
        common_name='Ficus',
        temp_min=15, temp_max=30,
        humidity_min=40, humidity_max=70,
        soil_min=30, soil_max=80,
        sunlight='part shade',
        watering='average',
    )
