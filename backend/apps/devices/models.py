# Modelos de la aplicacion de dispositivos
from django.db import models
from .fields import EncryptedCharField


# Equipo de red como un switch o router con acceso por API
# La contrasena se almacena cifrada con Fernet en la base de datos
class NetworkDevice(models.Model):
    name = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(unique=True)
    username = models.CharField(max_length=50)
    password = EncryptedCharField(max_length=255)
    api_port = models.IntegerField(default=8728)


# Aula que agrupa dispositivos
class Classroom(models.Model):
    name = models.CharField(unique=True)
    is_internet_blocked = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


# Dispositivo individual que representa un equipo monitorizado
class Device(models.Model):
    mac = models.CharField(max_length=17, unique=True)
    ip = models.GenericIPAddressField()
    hostname = models.CharField(max_length=100)
    

    classroom = models.ForeignKey(Classroom,on_delete=models.SET_NULL, null=True)
    connected_device = models.ForeignKey(NetworkDevice, on_delete=models.SET_NULL, null=True)
    switch_port = models.CharField(max_length=50, default=" ")

    is_online = models.BooleanField(default=False)
    is_internet_blocked = models.BooleanField(default=False)


    def __str__(self):
        return  f'hostname = {self.hostname} , mac = {self.mac}'


# Hosts permitidos que siempre seran accesibles aunque se corte internet
# Cuando se bloquea un puerto se crean reglas accept para cada uno de estos
# Si classroom es null se aplica a todas las reglas (global)
# Si tiene classroom asignada solo se aplica a reglas de esa aula
class AllowedHost(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    classroom = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='allowed_hosts',
    )

    def __str__(self):
        return f"{self.name} ({self.ip_address})" if self.name else str(self.ip_address)

