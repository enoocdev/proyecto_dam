#!/usr/bin/env bash
# deploy.sh — Script de despliegue para produccion
# Ejecutar desde la carpeta produccion del proyecto
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROD_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Colores para salida por consola
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Comprobar que existe .env 
if [ ! -f "$PROD_DIR/.env" ]; then
    error "No se encontro $PROD_DIR/.env — copia .env.example y rellena los valores."
fi

# Compilar el frontend con Bun 
info "Instalando dependencias del frontend..."
cd "$FRONTEND_DIR"
bun install

info "Compilando el frontend para produccion..."
bun run build

FRONTEND_BUILD="$FRONTEND_DIR/dist"
if [ ! -d "$FRONTEND_BUILD" ]; then
    error "No se encontro $FRONTEND_BUILD — la compilacion ha fallado."
fi

# Levantar los contenedores
info "Construyendo y levantando contenedores..."
cd "$PROD_DIR"

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --wait

# Copiar build del frontend al volumen de Caddy
info "Copiando build del frontend al contenedor de Caddy..."
CADDY_CONTAINER=$(docker compose -f docker-compose.prod.yml ps -q caddy)
docker cp "$FRONTEND_BUILD/." "$CADDY_CONTAINER:/var/www/frontend/"

# Migraciones y ficheros estaticos 
info "Ejecutando migraciones de base de datos..."
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

info "Recopilando ficheros estaticos..."
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Crear superusuario automaticamente
info "Creando superusuario (si no existe)..."
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser --noinput 2>/dev/null || true

# Recargar Caddy para que lea los nuevos ficheros 
info "Recargando Caddy..."
docker compose -f docker-compose.prod.yml exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true

# Resumen
echo ""
info "  Despliegue completado con exito!"
info "Servicios activos:"
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
