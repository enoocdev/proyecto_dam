# Modelo de usuario personalizado que extiende AbstractUser de Django
from django.contrib.auth.models import AbstractUser


# Se extiende para poder anadir campos personalizados en el futuro
class User(AbstractUser):
    pass
