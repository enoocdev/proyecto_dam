# Registro de modelos en el panel de administracion de Django
from django.contrib import admin
from .models import Device, AllowedHost

admin.site.register(Device)
admin.site.register(AllowedHost)
