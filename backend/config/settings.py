# Configuracion principal del proyecto Django

from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# Clave secreta cargada desde variables de entorno
SECRET_KEY = os.getenv('SECRET_KEY')

# Activar modo debug solo en desarrollo
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Hosts permitidos separados por coma en la variable de entorno
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'users.User'

# Configuracion de Django REST Framework con autenticacion JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        'rest_framework.authentication.SessionAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# Duracion de los tokens JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# Application definition

# Aplicaciones instaladas
INSTALLED_APPS = [
    'daphne',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',
    'channels',

    # Aplicaciones propias del proyecto
    'apps.users',
    'apps.devices',
]
    

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Configuracion de la base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
    }
}


# Validadores de contrasena
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internacionalizacion

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Archivos estaticos

STATIC_URL = 'static/'

# Directorio donde collectstatic recopila todos los ficheros estaticos
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Tipo de clave primaria por defecto

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CONFIGURACION DE CORS Y SEGURIDAD PARA TAURI 

_cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')

# Origenes obligatorios para que Tauri funcione en Windows, Linux y macOS
TAURI_ORIGINS = [
    "tauri://localhost",       # Windows / macOS
    "http://tauri.localhost",  # Linux (WebKitGTK)
    "https://tauri.localhost", # Linux SSL
    "http://localhost:5173",   # Dev mode
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    # Procesar origenes del .env
    env_origins = [o.strip() for o in _cors_origins.split(',') if o.strip()]
    # Fusionar con los de Tauri sin duplicados
    CORS_ALLOWED_ORIGINS = list(set(env_origins + TAURI_ORIGINS))

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['Allow', 'Content-Type']

# Configuracion CSRF: Crucial para permitir POST/PUT desde Tauri
_csrf_origins = [o.strip() for o in _cors_origins.split(',') if o.strip()] if _cors_origins else []
CSRF_TRUSTED_ORIGINS = list(set(_csrf_origins + TAURI_ORIGINS))

# CONFIGURACION DE CHANNELS / WEBSOCKETS 

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                os.getenv("REDIS_HOST", "127.0.0.1"),
                int(os.getenv("REDIS_PORT", 6379)),
            )],
            "capacity": 300,
            "expiry": 60,
        },
    },
}