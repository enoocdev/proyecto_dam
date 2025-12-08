from django.db import models


class NetworkDevice(models.Model):
    name = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(unique=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    api_port = models.IntegerField(default=8728)


class Classroom(models.Model):
    name = models.CharField()
    
    def __str__(self):
        return self.name


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


class Log(models.Model):
    pass