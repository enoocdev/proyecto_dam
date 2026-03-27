#!/usr/bin/env bash
# deploy.sh — Script de despliegue para produccion
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROD_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DOCKER_FILE="docker-compose.prod.yml"
MIKROTIK_CERTS_DIR="$PROD_DIR/mikrotik_certs"

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

docker compose -f "$DOCKER_FILE" build
docker compose -f "$DOCKER_FILE" up -d --wait

# Migraciones y ficheros estaticos 
info "Ejecutando migraciones de base de datos..."
docker compose -f "$DOCKER_FILE" exec backend python manage.py migrate --noinput

info "Recopilando ficheros estaticos..."
docker compose -f "$DOCKER_FILE" exec backend python manage.py collectstatic --noinput

# Crear superusuario automaticamente
info "Creando superusuario (si no existe)..."
docker compose -f "$DOCKER_FILE" exec backend python manage.py createsuperuser --noinput 2>/dev/null || true

# Recargar Caddy para que lea los nuevos ficheros 
info "Recargando Caddy..."
docker compose -f "$DOCKER_FILE" exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true

# SECCION DE CERTIFICADOS PARA MIKROTIK
info "Extrayendo certificados de Caddy para MikroTik (API SSL)..."
mkdir -p "$MIKROTIK_CERTS_DIR"

# Extraer certificados
docker compose -f "$DOCKER_FILE" cp caddy:/data/caddy/pki/authorities/local/root.crt "$MIKROTIK_CERTS_DIR/caddy_root.crt"

docker compose -f "$DOCKER_FILE" cp caddy:/data/caddy/pki/authorities/local/intermediate.crt "$MIKROTIK_CERTS_DIR/server.crt"
docker compose -f "$DOCKER_FILE" cp caddy:/data/caddy/pki/authorities/local/intermediate.key "$MIKROTIK_CERTS_DIR/server.key"

info "Certificados extraidos en: $MIKROTIK_CERTS_DIR"
info "Sube estos 3 archivos a tu MikroTik e importalos."


# Resumen
echo ""
info "Despliegue completado con exito!"
info "Servicios activos:"
docker compose -f "$DOCKER_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""