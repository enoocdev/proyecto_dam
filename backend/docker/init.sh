#!/bin/sh
set -e

# Espera a que PostgreSQL este disponible antes de continuar
echo "Esperando a PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(dbname='$POSTGRES_DB', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', host='$POSTGRES_HOST', port='$POSTGRES_PORT')" 2>/dev/null; do
  echo "PostgreSQL no disponible, reintentando en 2s..."
  sleep 2
done
echo "PostgreSQL listo!"

python manage.py makemigrations users
python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser --noinput || true

# Ejecuta el comando pasado desde docker compose como daphne
exec "$@"