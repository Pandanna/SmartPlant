from django.db import models
from accounts.models import Utente
import random
import string


class Dispositivo(models.Model):
    """
    Rappresenta un dispositivo fisico.
    Un dispositivo è 'disponibile' quando non ha una pianta associata.
    """
    device_id = models.CharField(max_length=50, primary_key=True)
    label = models.CharField(max_length=100, blank=True)
    pin = models.CharField(max_length=6, blank=True, help_text="Codice di 6 cifre per la registrazione")
    last_temp = models.FloatField(null=True, blank=True)
    last_hum = models.FloatField(null=True, blank=True)
    last_soil = models.FloatField(null=True, blank=True)
    last_light = models.FloatField(null=True, blank=True)
    last_battery = models.FloatField(null=True, blank=True)
    last_rain = models.BooleanField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    history = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivi"

    def save(self, *args, **kwargs):
        if not self.pin:
            self.pin = ''.join(random.choices(string.digits, k=6))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label or self.device_id} (PIN: {self.pin})"

    @property
    def disponibile(self):
        return not hasattr(self, 'pianta')


class Pianta(models.Model):
    """
    Pianta registrata, associata a un dispositivo e a un utente.
    """
    WATERING_CHOICES = [
        ('frequent', 'Frequente'),
        ('average',  'Moderato'),
        ('minimum',  'Scarso'),
        ('none',     'Minimo'),
    ]

    SUNLIGHT_CHOICES = [
        ('full sun',   'Luce diretta'),
        ('part shade', 'Parziale'),
        ('full shade', 'Ombra'),
    ]

    dispositivo  = models.OneToOneField(Dispositivo, on_delete=models.PROTECT, related_name='pianta')
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name='piante')
    nickname = models.CharField(max_length=80)
    species = models.CharField(max_length=150, blank=True)
    common_name = models.CharField(max_length=150, blank=True)
    image = models.TextField(blank=True)

    # Soglie allarme
    temp_min = models.FloatField(default=15)
    temp_max = models.FloatField(default=30)
    humidity_min = models.FloatField(default=40)
    humidity_max = models.FloatField(default=70)
    soil_min = models.FloatField(default=30)
    soil_max = models.FloatField(default=80)
    sunlight = models.CharField(max_length=20, choices=SUNLIGHT_CHOICES, default='full sun')
    watering = models.CharField(max_length=20, choices=WATERING_CHOICES, default='average')
    auto_irrigation = models.BooleanField(default=False)

    # Stato sensori (ultimo valore ricevuto via MQTT)
    last_temperature = models.FloatField(null=True, blank=True)
    last_humidity = models.FloatField(null=True, blank=True)
    last_light = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    # Irrigazione
    last_irrigation = models.DateTimeField(null=True, blank=True)

    # Allarmi
    last_alarm_sent = models.DateTimeField(null=True, blank=True)

    registered_at = models.DateTimeField(auto_now_add=True)
    manual = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Pianta"
        verbose_name_plural = "Piante"

    def __str__(self):
        return f"{self.nickname} ({self.dispositivo.device_id})"

    def params_dict(self):
        """Restituisce i parametri nel formato usato dal frontend."""
        return {
            'temp_min':        self.temp_min,
            'temp_max':        self.temp_max,
            'humidity_min':    self.humidity_min,
            'humidity_max':    self.humidity_max,
            'soil_min':        self.soil_min,
            'soil_max':        self.soil_max,
            'sunlight':        self.sunlight,
            'watering':        self.watering,
            'auto_irrigation': self.auto_irrigation,
        }


class IrrigazioneLog(models.Model):
    """
    Log degli interventi di irrigazione.
    """
    TRIGGER_CHOICES = [
        ('manuale', 'Manuale'),
        ('automatica', 'Automatica'),
    ]

    pianta = models.ForeignKey(Pianta, on_delete=models.CASCADE, related_name='irrigation_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=30)  # secondi
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='manuale')

    class Meta:
        verbose_name = "Log irrigazione"
        verbose_name_plural = "Log irrigazioni"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.pianta.nickname} — {self.timestamp:%d/%m/%Y %H:%M}"


class PlantCareCache(models.Model):
    """
    Cache locale dei parametri di cura per specie (da Open Plantbook).
    Evita chiamate API ripetute per la stessa specie.
    """
    pid = models.CharField(max_length=200, unique=True)  # nome scientifico lowercase
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    humidity_min = models.FloatField()
    humidity_max = models.FloatField()
    soil_min = models.FloatField()
    soil_max = models.FloatField()
    sunlight = models.CharField(max_length=20)
    watering = models.CharField(max_length=20)
    cached_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cache parametri pianta"

    def __str__(self):
        return self.pid

    def to_dict(self):
        return {
            'temp_min': self.temp_min,
            'temp_max': self.temp_max,
            'humidity_min': self.humidity_min,
            'humidity_max': self.humidity_max,
            'soil_min': self.soil_min,
            'soil_max': self.soil_max,
            'sunlight': self.sunlight,
            'watering': self.watering,
        }
