# Modelo de usuario personalizado que extiende AbstractUser de Django
from django.contrib.auth.models import AbstractUser
from django.db import models


# Se extiende para poder anadir campos personalizados en el futuro
class User(AbstractUser):
    classrooms = models.ManyToManyField(
        'devices.Classroom',
        blank=True,
        related_name='users',
    )
