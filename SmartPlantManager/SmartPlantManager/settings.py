from pathlib import Path
from decouple import config, Csv
import re

BASE_DIR = Path(__file__).resolve().parent.parent
SHARED_ROOT = BASE_DIR / 'shared'

DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

# Assicuriamoci che sia sempre una lista
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='*', cast=Csv())

SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-default-change-me')

CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
]

# Impostazioni Proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Cookie Settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SAMESITE = 'None'

CSRF_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'plants',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SmartPlantManager.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
        SHARED_ROOT / 'templates',
        BASE_DIR / 'accounts' / 'templates',
        BASE_DIR / 'plants' / 'templates',
    ],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'SmartPlantManager.wsgi.application'

# Database
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    try:
        # Supportiamo sia postgres:// che postgresql:// e porta opzionale
        _db = re.match(
            r'postgres(?:ql)?://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^/:]+)(?::(?P<port>\d+))?/(?P<name>[^?]+)',
            DATABASE_URL
        )
        if _db:
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': _db.group('name').split('?')[0], # Pulisce eventuali parametri extra
                    'USER': _db.group('user'),
                    'PASSWORD': _db.group('password'),
                    'HOST': _db.group('host'),
                    'PORT': _db.group('port') or '5432',
                }
            }
        else:
            DATABASE_URL = None
    except Exception:
        DATABASE_URL = None

if not DATABASE_URL:
    # Se abbiamo le variabili ambiente Postgres, usiamo quelle
    if config('POSTGRES_DB', default=None):
        DATABASES = {
            'default': {
                'ENGINE':   'django.db.backends.postgresql',
                'NAME':     config('POSTGRES_DB'),
                'USER':     config('POSTGRES_USER', default='postgres'),
                'PASSWORD': config('POSTGRES_PASSWORD', default='postgres'),
                'HOST':     config('POSTGRES_HOST', default='db'),
                'PORT':     config('POSTGRES_PORT', default='5432'),
            }
        }
    else:
        # Fallback estremo per collectstatic o test locali senza DB
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

AUTH_USER_MODEL = 'accounts.Utente'
LOGIN_URL = '/login/'

LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    SHARED_ROOT / 'static',   
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Variabili IoT
AWS_IOT_ENDPOINT = config('AWS_IOT_ENDPOINT', default='')
AWS_IOT_PORT = config('AWS_IOT_PORT', default=8883, cast=int)
PLANTID_API_KEY = config('PLANTID_API_KEY', default='')
OPENPLANTBOOK_CLIENT_ID = config('OPENPLANTBOOK_CLIENT_ID', default='')
OPENPLANTBOOK_CLIENT_SECRET = config('OPENPLANTBOOK_CLIENT_SECRET', default='')
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN', default='')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
