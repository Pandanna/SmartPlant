FROM python:3.12-slim

# Dipendenze di sistema necessarie per psycopg2 (driver PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Puntiamo alla sottocartella SmartPlantManager presente nel repository
COPY SmartPlantManager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il contenuto della cartella SmartPlantManager nella directory di lavoro /app
COPY SmartPlantManager/ .

# Raccoglie i file statici
# Usiamo una chiave dummy e debug per la build
RUN DJANGO_SECRET_KEY=build_step_key \
    DJANGO_DEBUG=True \
    python manage.py collectstatic --noinput --clear

# Espone la porta 8000
EXPOSE 8000

# Avvia lo script di avvio che gestisce migrazioni, admin e server
CMD ["sh", "render-start.sh"]
