from .settings import *

# Forza SQLite in-memory per i test
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disabilita WhiteNoise storage per i test
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
