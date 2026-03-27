
# Despliegue en Producción — NetManagement

Guía completa para levantar el proyecto en un entorno de producción usando Docker Compose.

---

## Requisitos previos

| Herramienta      | Versión mínima | Enlace                                      |
| ---------------- | -------------- | ------------------------------------------- |
| Docker           | 24+            | https://docs.docker.com/engine/install/     |
| Docker Compose   | v2+            | Incluido con Docker Desktop / plugin CLI     |
| Bun              | 1.0+           | https://bun.sh                               |
| Git              | 2.x            | https://git-scm.com                          |

> **Nota:** Si prefieres npm o yarn en lugar de Bun, sustituye `bun install` y `bun run build` por los comandos equivalentes en los pasos manuales.

---

## Arquitectura

```text
Internet ──80/443──▶ Caddy (proxy inverso + TLS automático)
                        ├─ /api/* ──▶ backend:8000  (Django REST Framework)
                        ├─ /ws/* ──▶ backend:8000  (Daphne — WebSockets)
                        ├─ /admin/* ──▶ backend:8000  (Django Admin)
                        ├─ /static/* ──▶ ficheros estáticos de Django
                        └─ /* ──▶ React SPA (Vite build)

                     Backend ──▶ PostgreSQL 16
                             ──▶ Redis 7 (Channel Layers + Heartbeat)
                             ──▶ Routers MikroTik (API TLS por puerto 8729)
```

### Redes Docker

| Red            | Tipo                | Servicios conectados        | Propósito |
| -------------- | ------------------- | --------------------------- | --------- |
| `backend_net`  | bridge (no interna) | db, redis, backend, caddy   | Comunicación entre servicios base y salida hacia la red local para la gestión de los switches MikroTik. |
| `frontend_net` | bridge              | backend, caddy              | Exposición del proxy Caddy hacia el exterior. |

*Nota Crítica:* La red `backend_net` **no debe ser `internal: true`**. El backend necesita salir del entorno aislado de Docker para comunicarse con las direcciones IP de la red local donde residen los routers MikroTik.

Solo **Caddy** expone puertos al exterior (80 y 443).

---

## Inicio rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/enoocdev/proyecto_dam.git
cd proyecto_dam
```

### 2. Configurar las variables de entorno

```bash
cd produccion
cp .env.example .env
```

Edita `.env` con tus valores reales:

```dotenv
# --- PostgreSQL ---
POSTGRES_DB=monitor_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_segura

# --- Django ---
SECRET_KEY=genera-una-con-python-generar_clave.py
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,[www.tu-dominio.com](https://www.tu-dominio.com),localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=[https://tu-dominio.com](https://tu-dominio.com),[https://www.tu-dominio.com](https://www.tu-dominio.com)

# --- Superusuario ---
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=password_segura
DJANGO_SUPERUSER_EMAIL=admin@tu-dominio.com

# --- Caddy ---
# Usa tu dominio real para TLS automático, o :80 para pruebas locales
DOMAIN=tu-dominio.com
```

> **Generar SECRET_KEY:**
> ```bash
> cd ../backend
> python generar_clave.py
> ```

### 3. Desplegar con el script automático

```bash
cd produccion
chmod +x deploy.sh
./deploy.sh
```

El script realizará automáticamente:

1. `bun install` + `bun run build` del frontend
2. Construcción de la imagen Docker del backend
3. Levantamiento de todos los contenedores
4. Copia del build de React al contenedor de Caddy
5. `python manage.py migrate`
6. `python manage.py collectstatic`
7. Creación del superusuario con las variables de entorno

---

## Despliegue manual (paso a paso)

Si prefieres ejecutar cada paso por separado:

```bash
# 1. Compilar el frontend
cd frontend
bun install
bun run build
cd ..

# 2. Construir y levantar contenedores
cd produccion
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --wait

# 3. Copiar el build del frontend al contenedor de Caddy
CADDY_ID=$(docker compose -f docker-compose.prod.yml ps -q caddy)
docker cp ../frontend/dist/. "$CADDY_ID:/var/www/frontend/"

# 4. Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

# 5. Recopilar archivos estáticos
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# 6. Crear superusuario (si no existe)
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser --noinput
```

---

## Comandos útiles

### Ver estado de los servicios

```bash
docker compose -f docker-compose.prod.yml ps
```

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Solo un servicio (ej: ver si falla la conexión TLS con MikroTik)
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f caddy
```

### Aplicar cambios de código sin destruir la base de datos

Si realizas cambios en el código de Python (ej: modificar serializadores o `mikrotik_service.py`), debes forzar la recreación del contenedor para evitar hilos "zombies" en memoria:

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build --force-recreate backend
```

### Detener todo

```bash
docker compose -f docker-compose.prod.yml down
```

### Detener y eliminar volúmenes (⚠️ borra la base de datos)

```bash
docker compose -f docker-compose.prod.yml down -v
```

### Abrir una shell en el backend

```bash
docker compose -f docker-compose.prod.yml exec backend sh
```

---

## Estructura de archivos

```text
produccion/
├── .env.example              # Plantilla de variables de entorno
├── .env                      # Variables reales
├── docker-compose.prod.yml   # Orquestación de servicios
├── Caddyfile                 # Configuración del proxy inverso
├── deploy.sh                 # Script de despliegue (Linux/macOS)
├── deploy.bat                # Script de despliegue (Windows)
└── README.md                 # Este archivo
```

---

## TLS / HTTPS y MikroTik

- **Caddy (Web):** Establece `DOMAIN=tu-dominio.com` en `.env`. Caddy obtiene y renueva certificados Let's Encrypt automáticamente. Asegúrate de que los puertos 80 y 443 son accesibles desde Internet. Para pruebas locales, usa `DOMAIN=:80`.
- **Backend a MikroTik (API):** La conexión entre el backend y los routers se realiza por el puerto `8729` (TLS). El backend está configurado con `OP_LEGACY_SERVER_CONNECT` y `SECLEVEL=0` para evitar "cuelgues" durante el apretón de manos con versiones antiguas de OpenSSL en RouterOS. Asegúrate de que el certificado en el MikroTik esté marcado como de confianza (`Trusted=yes` o flag **T** en WinBox).

---

## Solución de problemas frecuentes

| Problema | Solución |
|---|---|
| `ERROR: No se encontro .env` | Copia `.env.example` como `.env` y rellena los valores. |
| El backend no conecta con PostgreSQL | Verifica que `POSTGRES_HOST=db` en `.env` y que el contenedor `db` esté *healthy* usando `docker compose ps`. |
| Las URLs de la API devuelven el dominio de Docker en vez del real | Asegúrate de usar `serializers.ModelSerializer` y `PrimaryKeyRelatedField` en Django en lugar de `HyperlinkedModelSerializer`. Caddy altera el host al hacer proxy. |
| El backend se queda colgado infinitamente al conectar con MikroTik | Verifica que en el `docker-compose.prod.yml`, la red `backend_net` tenga `internal: false`. Revisa que la librería `librouteros` use el parámetro `ssl_wrapper=ctx.wrap_socket`. |
| La web no se actualiza con los puertos de los PCs | Asegúrate de tener al menos un cliente enviando un "latido" (Heartbeat) al servidor para disparar la búsqueda en la tabla ARP/Bridge. |
| Frontend muestra página en blanco | Verifica que el build de Vite se copió correctamente: `docker compose exec caddy ls /var/www/frontend/`. |