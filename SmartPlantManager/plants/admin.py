from django.contrib import admin
from .models import Dispositivo, Pianta, IrrigazioneLog

class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'label', 'pin', 'last_seen', 'disponibile')
    search_fields = ('device_id', 'label')

admin.site.register(Dispositivo, DispositivoAdmin)
admin.site.register(Pianta)
admin.site.register(IrrigazioneLog)