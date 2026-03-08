# Registro del modelo Device en el panel de administracion de Django
from django.contrib import admin
from .models import Device

admin.site.register(Device)
