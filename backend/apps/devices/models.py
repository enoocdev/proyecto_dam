from django.db import models


class DeviceGroup(models.Model):
    name = models.CharField()
    
    def __str__(self):
        return self.name


class Device(models.Model):
    mac = models.CharField(max_length=17, unique=True)
    ip = models.GenericIPAddressField()
    hostname = models.CharField(max_length=100)
    

    groups = models.ManyToManyField(
        DeviceGroup,
        related_name="devices",
        blank=True
    )

    def __str__(self):
        return  f'hostname = {self.hostname} , mac = {self.mac}'


