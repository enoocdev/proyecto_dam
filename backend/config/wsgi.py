# Configuracion WSGI del proyecto
# Expone la variable application para servidores WSGI como Gunicorn

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
