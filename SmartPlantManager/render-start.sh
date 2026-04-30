#!/bin/sh

# Applica le migrazioni al database
echo "==> Migrazione database..."
python manage.py migrate

# Crea il superuser
echo "==> Creazione superuser..."
python manage.py createsuperuser --no-input || echo "Superuser già esistente o errore saltato."

# Avvia il server
echo "==> Avvio Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 SmartPlantManager.wsgi:application
