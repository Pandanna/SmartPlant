FROM python:3.12-slim

# Dipendenze di sistema necessarie per psycopg2 (driver PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Raccoglie i file statici
# Usiamo una chiave dummy e debug per la build
RUN DJANGO_SECRET_KEY=build_step_key \
    DJANGO_DEBUG=True \
    python manage.py collectstatic --noinput --clear

# Espone la porta 8000
EXPOSE 8000

# Avvia il server con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "SmartPlantManager.wsgi:application"]
