# **🛡️ NetManagement — Sistema de Monitorización y Control de Equipos**

![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)
[![Django](https://img.shields.io/badge/Backend-Django_5_+_DRF-092E20?style=for-the-badge&logo=django)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Tauri](https://img.shields.io/badge/Desktop-Tauri_2-FFC131?style=for-the-badge&logo=tauri)](https://tauri.app/)
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

#### **1. Monitorización y Control (Agente PC y Escritorio)**
* **📡 Transmisión en tiempo real:** Visualización de pantallas de los alumnos mediante [WebSockets](https://developer.mozilla.org/es/docs/Web/API/WebSockets_API) de baja latencia.
* **⚡ Control de energía:** Ejecución remota de comandos de apagado, reinicio y suspensión.
* **📸 Evidencias:** Captura de pantalla bajo demanda y almacenamiento centralizado.
* **💓 Heartbeat monitor:** Detección automática de equipos offline mediante claves TTL en Redis con notificaciones keyspace.
* **🖥️ Aplicación de escritorio:** El dashboard web de React se empaqueta como aplicación nativa multiplataforma usando [Tauri](https://tauri.app/), permitiendo gestión local y remota desde Windows, Linux y Mac.

#### **2. Gestión de Infraestructura (Network Fencing)**
* **🔒 Aislamiento dinámico:** Integración directa con la API de [Mikrotik RouterOS](https://mikrotik.com/software).
* **🚫 Modos de restricción:**
  * **Modo examen:** Bloquea el acceso a internet, permitiendo solo tráfico hacia hosts permitidos configurables.
  * **Modo bloqueo total:** Aísla completamente el puerto del switch (Port Disable / VLAN switching).
* **🆔 Identificación hardware:** Mapeo automático de direcciones MAC a puertos físicos del switch.
* **✅ Hosts permitidos:** Lista configurable de IPs que permanecen accesibles durante bloqueos de red.

#### **3. Panel de Administración (Web y Desktop)**
* **Dashboard interactivo:** Interfaz en [React 19](https://react.dev/) y [Material UI 7](https://mui.com/) para grid de equipos.
* **Tema claro/oscuro:** Soporte nativo persistente en localStorage.
* **RBAC (Role-Based Access Control):**
  * *Profesores:* Control de aula y visualización de equipos asignados.
  * *Administradores:* Gestión de red, dispositivos, usuarios y grupos.
* **Gestión completa:** CRUD de aulas, dispositivos de red, hosts permitidos, usuarios y grupos de permisos.
* **Aplicación de escritorio:** Todas las funciones del dashboard web disponibles como app nativa multiplataforma (Tauri).

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
| **Desktop** | [Tauri 2](https://tauri.app/) | Empaquetado nativo multiplataforma del dashboard React. |
| **Estado (Frontend)** | [Nanostores](https://github.com/nanostores/nanostores) + [react-use-websocket](https://github.com/robtaussig/react-use-websocket) | Estado ligero y persistente; hook declarativo para WS. |
| **Base de Datos** | [PostgreSQL 16](https://www.postgresql.org/) | Alta concurrencia transaccional y fiabilidad. |
| **Cache / Bus** | [Redis 7](https://redis.io/) | Broker de Channel Layers, heartbeat TTL y pub/sub. |
| **Redes** | [Librouteros](https://librouteros.readthedocs.io/) (Python) | Comunicación segura con la API de Mikrotik. |
| **Agente** | Python ([mss](https://python-mss.readthedocs.io/), [psutil](https://psutil.readthedocs.io/)), PyInstaller, servicio residente | Cliente ligero multiplataforma, ejecutable y servicio en segundo plano. |
| **Proxy Inverso** | [Caddy 2](https://caddyserver.com/) | TLS automático, HTTP/3, proxy de API y WebSockets. |
| **DevOps / CI** | [Docker Compose](https://docs.docker.com/compose/), [GitHub Actions](https://github.com/features/actions) | Orquestación completa y pipelines CI/CD para releases automatizadas. |

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
* **[Rust / Cargo](https://www.rust-lang.org/tools/install)** (solo si deseas compilar la app de escritorio Tauri localmente)
* Acceso a un router/switch **[Mikrotik](https://mikrotik.com/products)** (opcional, se puede simular).

docker compose up -d

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

#### 5. Desktop (Tauri)
```bash
cd frontend
bun run tauri dev    # o: npm run tauri dev
```

#### 6. Cliente agente (ejecutable y servicio)
```bash
cd client
pip install -r requirements.txt
pyinstaller build/netmanagement_installer.spec
python install_service.py          # Instala el agente como servicio residente
```

#### 7. Variables de entorno (backend/.env)
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


### **Produccion**

El despliegue en produccion utiliza **Docker Compose** con **Caddy** como proxy inverso con TLS automatico. Consulta la guia completa en [`produccion/README.md`](produccion/README.md).

```bash
cd produccion
cp .env.example .env   # Editar con valores reales
chmod +x deploy.sh
./deploy.sh
```

**Arquitectura de produccion:**
```
Internet ──80/443──▶ Caddy (TLS automatico)
                        ├─ /api/*    ──▶ backend:8000 (Django REST)
                        ├─ /ws/*     ──▶ backend:8000 (Daphne WebSockets)
                        ├─ /admin/*  ──▶ backend:8000 (Django Admin)
                        ├─ /static/* ──▶ ficheros estaticos de Django
                        └─ /*        ──▶ React SPA (build compilado) o Tauri Desktop
```

---


## **📸 Capturas de Pantalla**

*(Espacio reservado para screenshots del dashboard, desktop y agente)*

| Dashboard Principal | Panel de Control de Red |
| :---- | :---- |
|  |  |

---

## **👤 Autor**

**Enooc Domínguez** — *Desarrollador Full Stack & SysAdmin*

* 📧 **Email:** [enooc.dominguez@iessanmamede.com](mailto:enooc.dominguez@iessanmamede.com)
* 🐙 **GitHub:** [@enoocdev](https://github.com/enoocdev)

Proyecto desarrollado como Trabajo de Fin de Grado — Desarrollo de Aplicaciones Multiplataforma (DAM).
