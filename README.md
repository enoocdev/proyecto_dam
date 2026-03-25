# **🛡️ NetManagement — Sistema de Monitorización y Control de Equipos**

![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)
[![Django](https://img.shields.io/badge/Backend-Django_5_+_DRF-092E20?style=for-the-badge&logo=django)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Postgres](https://img.shields.io/badge/DB-PostgreSQL_16-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Cache-Redis_7-DC382D?style=for-the-badge&logo=redis)](https://redis.io/)
[![Caddy](https://img.shields.io/badge/Proxy-Caddy_2-00A95C?style=for-the-badge)](https://caddyserver.com/)
[![Docker](https://img.shields.io/badge/Infra-Docker_Compose-2496ED?style=for-the-badge&logo=docker)](https://docs.docker.com/compose/)
[![Mikrotik](https://img.shields.io/badge/Network-Mikrotik-E10B18?style=for-the-badge)](https://mikrotik.com/)

> **Proyecto de Fin de Curso — DAM**
> Sistema integral para la gestión de aulas de informática, permitiendo el control remoto de equipos y el aislamiento de red automatizado mediante infraestructura [Mikrotik](https://mikrotik.com/).

---

## **📋 Descripción del Proyecto**

Este sistema aborda la necesidad de administrar aulas informáticas de forma centralizada y segura. A diferencia de las soluciones tradicionales de gestión de aula, este proyecto introduce una capa de **control de red física (L2/L3)**. Permite aislar equipos de internet o de la red local dinámicamente durante exámenes o incidencias, interactuando directamente con el equipamiento de switching.

---

### **🌟 Funcionalidades Clave**

#### **1. Monitorización y Control (Agente PC)**
* **📡 Transmisión en Tiempo Real:** Visualización de pantallas de los alumnos mediante [WebSockets](https://developer.mozilla.org/es/docs/Web/API/WebSockets_API) de baja latencia.
* **⚡ Control de Energía:** Ejecución remota de comandos de Apagado, Reinicio y Suspensión.
* **📸 Evidencias:** Toma de capturas de pantalla bajo demanda y almacenamiento centralizado.
* **💓 Heartbeat Monitor:** Detección automática de equipos offline mediante claves TTL en Redis con notificaciones keyspace.

#### **2. Gestión de Infraestructura (Network Fencing)**
* **🔒 Aislamiento Dinámico:** Integración directa con la API de [Mikrotik RouterOS](https://mikrotik.com/software).
* **🚫 Modos de Restricción:**
  * **Modo Examen:** Bloquea el acceso a Internet, permitiendo únicamente tráfico hacia hosts permitidos configurables.
  * **Modo Bloqueo Total:** Aísla completamente el puerto del switch (Port Disable / VLAN switching).
* **🆔 Identificación Hardware:** Mapeo automático de direcciones MAC a puertos físicos del switch.
* **✅ Hosts Permitidos:** Lista configurable de IPs que permanecen accesibles durante bloqueos de red.

#### **3. Panel de Administración (Web)**
* **Dashboard Interactivo:** Interfaz desarrollada en [React 19](https://react.dev/) con [Material UI 7](https://mui.com/) para visualización en grid de todos los equipos.
* **Tema Claro/Oscuro:** Soporte nativo de temas persistente en localStorage.
* **RBAC (Role-Based Access Control):**
  * *Profesores:* Control de aula y visualización de equipos asignados.
  * *Administradores:* Configuración de red, gestión de dispositivos, usuarios y grupos.
* **Gestión Completa:** CRUD de aulas, dispositivos de red, hosts permitidos, usuarios y grupos de permisos.

---

## **🏗️ Arquitectura Técnica**

El sistema utiliza una arquitectura distribuida orientada a eventos. La comunicación en tiempo real se gestiona mediante canales asíncronos ([ASGI](https://asgi.readthedocs.io/)).

### **Flujo de Datos**
1. **Capa de Gestión (Frontend):** El profesor interactúa con el Dashboard ([React](https://react.dev/)), enviando peticiones REST y escuchando eventos por WebSocket.
2. **Servidor Central (Backend):** [Django](https://www.djangoproject.com/) recibe las órdenes. Si es un comando de red, contacta con la **API de Mikrotik**. Si es un comando de PC, lo publica en **[Redis](https://redis.io/)**.
3. **Capa de Infraestructura:** El router/switch [Mikrotik](https://mikrotik.com/) aplica las reglas de firewall o VLANs instantáneamente al recibir la orden del backend.
4. **Capa de Aula (Agentes):** Los PCs de los alumnos, suscritos al canal de Redis vía WebSocket, reciben la orden (ej. bloquear pantalla) y envían el stream de vídeo de vuelta al servidor.

### **🛠️ Stack Tecnológico**

| Capa | Tecnología | Justificación |
| :--- | :--- | :--- |
| **Backend** | [Python](https://www.python.org/), [Django 5](https://www.djangoproject.com/), [DRF](https://www.django-rest-framework.org/) | Robustez, seguridad y estructura sólida de modelos. |
| **Real-Time** | [Django Channels](https://channels.readthedocs.io/) + [Daphne](https://github.com/django/daphne) | WebSockets asíncronos (ASGI) para streaming y heartbeat. |
| **Frontend** | [React 19](https://react.dev/), [Vite](https://vitejs.dev/), [Material UI 7](https://mui.com/) | SPA rápida con HMR y componentes modernos. |
| **Estado (Frontend)** | [Nanostores](https://github.com/nanostores/nanostores) + [react-use-websocket](https://github.com/robtaussig/react-use-websocket) | Estado ligero y persistente; hook declarativo para WS. |
| **Base de Datos** | [PostgreSQL 16](https://www.postgresql.org/) | Alta concurrencia transaccional y fiabilidad. |
| **Cache / Bus** | [Redis 7](https://redis.io/) | Broker de Channel Layers, heartbeat TTL y pub/sub. |
| **Redes** | [Librouteros](https://librouteros.readthedocs.io/) (Python) | Comunicación segura con la API de Mikrotik. |
| **Agente** | Python ([mss](https://python-mss.readthedocs.io/), [psutil](https://psutil.readthedocs.io/)) | Cliente ligero multiplataforma para captura y control. |
| **Proxy Inverso** | [Caddy 2](https://caddyserver.com/) | TLS automático, HTTP/3, proxy de API y WebSockets. |
| **DevOps** | [Docker Compose](https://docs.docker.com/compose/) | Orquestación completa para desarrollo y producción. |

---

## **📂 Estructura del Proyecto**

```
proyecto_dam/
├── backend/              # Django 5 + DRF + Channels (Daphne)
│   ├── apps/
│   │   ├── devices/      # Dispositivos, aulas, red, WebSocket consumers
│   │   └── users/        # Usuarios, grupos, permisos, JWT
│   ├── config/           # settings.py, urls.py, asgi.py
│   ├── Dockerfile.prod   # Imagen Docker multi-stage para producción
│   └── requirements.txt
├── frontend/             # React 19 + Vite + Material UI 7
│   ├── src/
│   │   ├── components/   # Tarjetas, modales, rutas protegidas
│   │   ├── hooks/        # useAuth, useDashboardSocket, useEndpointPermissions
│   │   ├── pages/        # Dashboard, Classrooms, Users, Profile…
│   │   ├── stores/       # Nanostores (screenshots, classrooms)
│   │   └── styles/       # CSS por página + tema claro/oscuro
│   └── .env.production   # VITE_API_URL=/api (relativa para Caddy)
├── client/               # Agente Python para PCs de alumnos
├── produccion/           # Configuración de despliegue
│   ├── docker-compose.prod.yml
│   ├── Caddyfile
│   ├── deploy.sh / deploy.bat
│   ├── .env.example
│   └── README.md         # Guía completa de despliegue
└── docs/                 # Documentación técnica
    └── database-er.mmd   # Modelo Entidad-Relación (Mermaid)
```

---

## **🚀 Guía de Instalación**

### **Prerrequisitos**
* **[Docker](https://www.docker.com/)** y **[Docker Compose](https://docs.docker.com/compose/)** v2+
* **[Python 3.11+](https://www.python.org/downloads/)**
* **[Bun](https://bun.sh/)** (o Node.js 18+)
* Acceso a un router/switch **[Mikrotik](https://mikrotik.com/products)** (opcional, se puede simular).

### **Desarrollo Local**

#### 1. Clonar el repositorio
```bash
git clone https://github.com/enoocdev/proyecto_dam
cd proyecto_dam
```

#### 2. Levantar infraestructura (PostgreSQL + Redis)
```bash
cd backend
docker compose up -d
```

#### 3. Backend (Django)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\Activate           # Windows

pip install -r requirements.txt

cp .envExample .env                # Editar con tus credenciales
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver         # o: daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

#### 4. Frontend (React)
```bash
cd frontend
bun install          # o: npm install
bun run dev          # o: npm run dev
```

#### 5. Variables de entorno (backend/.env)
```dotenv
POSTGRES_DB=monitor_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_local
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

SECRET_KEY=genera-con-python-generar_clave.py
DEBUG=True
ALLOWED_HOSTS=*

REDIS_HOST=localhost
REDIS_PORT=6379

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=tu_password
DJANGO_SUPERUSER_EMAIL=admin@ejemplo.com
```

---

### **Producción**

El despliegue en producción utiliza **Docker Compose** con **Caddy** como proxy inverso con TLS automático. Consulta la guía completa en [`produccion/README.md`](produccion/README.md).

```bash
cd produccion
cp .env.example .env   # Editar con valores reales
chmod +x deploy.sh
./deploy.sh
```

**Arquitectura de producción:**
```
Internet ──80/443──▶ Caddy (TLS automático)
                        ├─ /api/*    ──▶ backend:8000 (Django REST)
                        ├─ /ws/*     ──▶ backend:8000 (Daphne WebSockets)
                        ├─ /admin/*  ──▶ backend:8000 (Django Admin)
                        ├─ /static/* ──▶ ficheros estáticos de Django
                        └─ /*        ──▶ React SPA (build compilado)
```

---

## **📸 Capturas de Pantalla**

*(Espacio reservado para screenshots del Dashboard y funcionamiento)*

| Dashboard Principal | Panel de Control de Red |
| :---- | :---- |
|  |  |

---

## **👤 Autor**

**Enooc Domínguez** — *Desarrollador Full Stack & SysAdmin*

* 📧 **Email:** [enooc.dominguez@iessanmamede.com](mailto:enooc.dominguez@iessanmamede.com)
* 🐙 **GitHub:** [@enooc](https://github.com/enooc)

Proyecto desarrollado como Trabajo de Fin de Grado — Desarrollo de Aplicaciones Multiplataforma (DAM).
