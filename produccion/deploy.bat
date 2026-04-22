@echo off
REM deploy.bat — Script de despliegue para produccion (Windows)
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
REM Eliminar la barra final de SCRIPT_DIR para construir PROJECT_ROOT correctamente
set "PROD_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%PROD_DIR%\..") do set "PROJECT_ROOT=%%~fI"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "DOCKER_FILE=docker-compose.prod.yml"
set "MIKROTIK_CERTS_DIR=%PROD_DIR%\mikrotik_certs"

REM Comprobar que existe .env
if not exist "%PROD_DIR%\.env" (
    echo [ERROR] No se encontro %PROD_DIR%\.env — copia .env.example y rellena los valores.
    exit /b 1
)

REM Compilar el frontend con Bun
echo [INFO] Instalando dependencias del frontend...
cd /d "%FRONTEND_DIR%"
call bun install
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias del frontend.
    exit /b 1
)

echo [INFO] Compilando el frontend para produccion...
call bun run build
if errorlevel 1 (
    echo [ERROR] Fallo al compilar el frontend.
    exit /b 1
)

if not exist "%FRONTEND_DIR%\dist" (
    echo [ERROR] No se encontro %FRONTEND_DIR%\dist — la compilacion ha fallado.
    exit /b 1
)

REM Construir y levantar los contenedores
echo [INFO] Construyendo y levantando contenedores...
cd /d "%PROD_DIR%"

docker compose -f %DOCKER_FILE% build
if errorlevel 1 ( echo [ERROR] Fallo docker compose build. & exit /b 1 )

docker compose -f %DOCKER_FILE% up -d --wait
if errorlevel 1 ( echo [ERROR] Fallo docker compose up. & exit /b 1 )

REM Migraciones y ficheros estaticos
echo [INFO] Ejecutando migraciones de base de datos...
docker compose -f %DOCKER_FILE% exec backend python manage.py migrate --noinput
if errorlevel 1 ( echo [ERROR] Fallo migrate. & exit /b 1 )

echo [INFO] Recopilando ficheros estaticos...
docker compose -f %DOCKER_FILE% exec backend python manage.py collectstatic --noinput
if errorlevel 1 ( echo [ERROR] Fallo collectstatic. & exit /b 1 )

REM Crear superusuario automaticamente
echo [INFO] Creando superusuario (si no existe)...
docker compose -f %DOCKER_FILE% exec backend python manage.py createsuperuser --noinput 2>nul

REM Recargar Caddy para que lea los nuevos ficheros
echo [INFO] Recargando Caddy...
docker compose -f %DOCKER_FILE% exec caddy caddy reload --config /etc/caddy/Caddyfile 2>nul

REM Extraer certificados de Caddy para MikroTik
echo [INFO] Extrayendo certificados de Caddy para MikroTik (API SSL)...
if not exist "%MIKROTIK_CERTS_DIR%" mkdir "%MIKROTIK_CERTS_DIR%"

docker compose -f %DOCKER_FILE% cp caddy:/data/caddy/pki/authorities/local/root.crt "%MIKROTIK_CERTS_DIR%\caddy_root.crt"
docker compose -f %DOCKER_FILE% cp caddy:/data/caddy/pki/authorities/local/intermediate.crt "%MIKROTIK_CERTS_DIR%\server.crt"
docker compose -f %DOCKER_FILE% cp caddy:/data/caddy/pki/authorities/local/intermediate.key "%MIKROTIK_CERTS_DIR%\server.key"

echo [INFO] Certificados extraidos en: %MIKROTIK_CERTS_DIR%
echo [INFO] Sube estos 3 archivos a tu MikroTik e importalos.

REM Resumen
echo.
echo [INFO] Despliegue completado con exito!
echo [INFO] Servicios activos:
docker compose -f %DOCKER_FILE% ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo.

endlocal