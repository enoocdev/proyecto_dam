# Campo de modelo personalizado con cifrado simetrico Fernet
# Cifra el valor antes de guardarlo en la base de datos
# y lo descifra automaticamente al leerlo desde el ORM
import base64

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


# Deriva una clave Fernet valida de 32 bytes a partir de la SECRET_KEY del proyecto
# Fernet requiere una clave URL-safe base64 de exactamente 32 bytes
def _get_fernet_key():
    key = settings.SECRET_KEY.encode()
    # Rellena o recorta a 32 bytes y codifica en base64 para Fernet
    key = key[:32].ljust(32, b'\0')
    return base64.urlsafe_b64encode(key)


def _get_fernet():
    return Fernet(_get_fernet_key())


# Campo que almacena texto cifrado con Fernet en la base de datos
# Al asignar un valor se cifra automaticamente antes de guardarlo
# Al leerlo se descifra de forma transparente para el resto de la aplicacion
class EncryptedCharField(models.CharField):

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        # Cifra el valor antes de enviarlo a la base de datos
        f = _get_fernet()
        return f.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        # Descifra el valor leido de la base de datos
        f = _get_fernet()
        try:
            return f.decrypt(value.encode()).decode()
        except InvalidToken:
            # Si no se puede descifrar devuelve el valor tal cual
            return value
