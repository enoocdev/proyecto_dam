# Despliegue en Producción — Mikrotik NetManagement

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

```
Internet ──80/443──▶ Caddy (proxy inverso + TLS automático)
                        ├─ /api/*        ──▶ backend:8000  (Django REST Framework)
                        ├─ /ws/*         ──▶ backend:8000  (Daphne — WebSockets)
                        ├─ /admin/*      ──▶ backend:8000  (Django Admin)
                        ├─ /static/*     ──▶ ficheros estáticos de Django
                        └─ /*            ──▶ React SPA (Vite build)

                     Backend ──▶ PostgreSQL 16
                             ──▶ Redis 7 (Channel Layers + Heartbeat)
```

### Redes Docker

| Red            | Tipo     | Servicios conectados        |
| -------------- | -------- | --------------------------- |
| `backend_net`  | internal | db, redis, backend, caddy   |
| `frontend_net` | externa  | backend, caddy              |

Solo **Caddy** expone puertos al exterior (80 y 443).

---

## Inicio rápido

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio> proyecto_dam
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
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

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

# 6. Crear superusuario
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

# Solo un servicio
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f caddy
```

### Reiniciar un servicio

```bash
docker compose -f docker-compose.prod.yml restart backend
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

### Ejecutar un comando de Django

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py <comando>
```

---

## Estructura de archivos

```
produccion/
├── .env.example              # Plantilla de variables de entorno
├── .env                      # Variables reales (NO subir a git)
├── docker-compose.prod.yml   # Orquestación de servicios
├── Caddyfile                 # Configuración del proxy inverso
├── deploy.sh                 # Script de despliegue (Linux/macOS)
├── deploy.bat                # Script de despliegue (Windows)
└── README.md                 # Este archivo
```

---

## TLS / HTTPS

- **Con dominio real:** Establece `DOMAIN=tu-dominio.com` en `.env`. Caddy obtiene y renueva certificados Let's Encrypt automáticamente. Asegúrate de que los puertos 80 y 443 son accesibles desde Internet.
- **Pruebas locales:** Establece `DOMAIN=:80` para servir solo HTTP sin certificado.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `ERROR: No se encontro .env` | Copia `.env.example` como `.env` y rellena los valores |
| El backend no conecta con PostgreSQL | Verifica que `POSTGRES_HOST=db` en `.env` y que el contenedor `db` esté healthy: `docker compose -f docker-compose.prod.yml ps` |
| WebSocket no conecta | Comprueba que `DOMAIN` es correcto y que Caddy hace proxy de `/ws/*`. Revisa logs con `docker compose -f docker-compose.prod.yml logs caddy` |
| `collectstatic` falla con permisos | El directorio `/app/staticfiles` debe ser propiedad del usuario `django` dentro del contenedor. El Dockerfile.prod ya lo configura |
| Certificado TLS no se genera | Asegúrate de que los puertos 80 y 443 están abiertos y el dominio apunta al servidor |
| Frontend muestra página en blanco | Verifica que el build se copió correctamente: `docker compose -f docker-compose.prod.yml exec caddy ls /var/www/frontend/` |

---

## Seguridad

- **`SECRET_KEY`**: Genera siempre una clave única para producción (`python generar_clave.py`).
- **`DEBUG=False`**: Nunca dejes Debug activo en producción.
- **Contraseñas**: Usa contraseñas fuertes para PostgreSQL y el superusuario.
- **Redes aisladas**: Solo Caddy es accesible externamente. db y redis no exponen puertos.
