from django.db import models

class Group(models.Model):
    name = models.CharField()


class Device(models.Model):
    mac = models.CharField(max_length=17, unique=True)
    ip = models.GenericIPAddressField()
    hostname = models.CharField(max_length=100)
    

    group = models.ManyToManyField(
        Group,
        related_name="devices",
        blank=True
    )


