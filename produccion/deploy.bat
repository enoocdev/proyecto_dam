@echo off
REM deploy.bat — Script de despliegue para produccion (Windows)
REM Ejecutar desde la carpeta produccion del proyecto
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "PROD_DIR=%SCRIPT_DIR%"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

REM  Comprobar que existe .env 
if not exist "%PROD_DIR%.env" (
    echo [ERROR] No se encontro %PROD_DIR%.env — copia .env.example y rellena los valores.
    exit /b 1
)

REM  Compilar el frontend con Bun 
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

REM Verificar build
if not exist "%FRONTEND_DIR%\dist" (
    echo [ERROR] No se encontro %FRONTEND_DIR%\dist — la compilacion ha fallado.
    exit /b 1
)

REM Levantar los contenedores
echo [INFO] Levantando contenedores con Docker Compose...
cd /d "%PROD_DIR%"

docker compose -f docker-compose.prod.yml down --remove-orphans 2>nul
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d --wait

REM Copiar frontend build al volumen de Caddy 
echo [INFO] Copiando build del frontend al volumen...
docker compose -f docker-compose.prod.yml cp "%FRONTEND_DIR%\dist\." caddy:/var/www/frontend/

REM Migraciones y ficheros estaticos
echo [INFO] Ejecutando migraciones de base de datos...
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

echo [INFO] Recopilando ficheros estaticos...
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

REM Crear superusuario automaticamente
echo [INFO] Creando superusuario (si no existe)...
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser --noinput 2>nul

REM Resumen
echo.
echo [INFO] ======================================
echo [INFO]   Despliegue completado con exito!
echo [INFO] ======================================
docker compose -f docker-compose.prod.yml ps

endlocal
