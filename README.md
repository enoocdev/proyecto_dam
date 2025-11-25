# 🛡️ Sistema de Monitorización y Control de Equipos con Gestión de Red Mikrotik

![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)
![Django](https://img.shields.io/badge/Backend-Django_Rest_Framework-092E20?style=for-the-badge&logo=django)
![React](https://img.shields.io/badge/Frontend-React_Vite-61DAFB?style=for-the-badge&logo=react)
![Postgres](https://img.shields.io/badge/DB-PostgreSQL-336791?style=for-the-badge&logo=postgresql)
![Mikrotik](https://img.shields.io/badge/Network-Mikrotik-E10B18?style=for-the-badge)

> **Proyecto de Fin de Grado (PFG)**
> Sistema integral para la gestión de aulas de informática, permitiendo el control remoto de equipos y el aislamiento de red automatizado mediante infraestructura Mikrotik.

---

## 📋 Descripción del Proyecto

Este sistema soluciona la necesidad de administrar aulas informáticas de forma centralizada. A diferencia de soluciones tradicionales, este proyecto integra el **control de hardware** (pantallas, energía) con el **control de red física** (Switching), permitiendo aislar equipos de internet o de la red local dinámicamente durante exámenes o incidencias.

### 🌟 Funcionalidades Clave

#### 1. Monitorización y Control (Agente PC)
* **📡 Transmisión en Tiempo Real:** Visualización de pantallas de los alumnos mediante WebSockets de baja latencia.
* **⚡ Control de Energía:** Comandos remotos de Apagado, Reinicio y Suspensión.
* **📸 Capturas:** Toma de evidencias visuales bajo demanda.

#### 2. Gestión de Infraestructura (Network Fencing)
* **🔒 Aislamiento Dinámico:** Integración con API de Mikrotik RouterOS.
* **🚫 Modos de Restricción:**
    * *Modo Examen:* Bloquea internet y LAN, permitiendo solo conexión con el servidor.
    * *Modo Bloqueo Total:* Aísla completamente el puerto del switch.
* **🆔 Identificación Hardware:** Mapeo automático de direcciones MAC a puertos del switch.

#### 3. Panel de Administración (Web)
* **Dashboard Interactivo:** Interfaz React moderna para ver el estado de todos los equipos.
* **Gestión de Roles:** Permisos diferenciados para Profesores (Control de aula) y Administradores (Configuración de red).

---

## 🏗️ Arquitectura Técnica

El sistema utiliza una arquitectura distribuida basada en eventos asíncronos para el tiempo real.

```mermaid
graph TD
    subgraph "AULA (Clientes)"
      PC1[🖥️ Agente PC 1]
      PC2[🖥️ Agente PC 2]
    end

    subgraph "INFRAESTRUCTURA DE RED"
      Switch[🔌 Switch Mikrotik]
    end

    subgraph "SERVIDOR (Dockerizado)"
      Redis[⚡ Redis (Canales)]
      DB[(🐘 PostgreSQL)]
      Backend[🐍 Django + Channels]
    end

    subgraph "PROFESOR"
      Frontend[⚛️ React Dashboard]
    end

    %% Conexiones
    PC1 <-->|WebSockets (Tiempo Real)| Backend
    PC2 <-->|WebSockets (Tiempo Real)| Backend
    
    Frontend <-->|API REST / WS| Backend
    
    Backend -->|SQL| DB
    Backend <-->|Pub/Sub| Redis
    Backend -->|API RouterOS| Switch
    
    Switch -.->|Filtra Tráfico| PC1
    Switch -.->|Filtra Tráfico| PC2
```

### 🛠️ Stack Tecnológico

Capa	Tecnología	Justificación
Backend	Python, Django 5, DRF	Robustez, seguridad y facilidad de gestión de datos.
Real-Time	Django Channels (Daphne)	Manejo de WebSockets asíncronos (ASGI).
Frontend	React 18, Vite, Material UI	Interfaz rápida y reactiva (SPA).
Base de Datos	PostgreSQL 16	Soporte nativo de JSONB y alta concurrencia.
Cache/Bus	Redis 7	Motor de mensajes para comunicar procesos y WebSockets.
Redes	Librouteros (Python)	Librería para comunicar con la API de Mikrotik.
Agente	Python (mss, psutil, websockets)	Ligero y multiplataforma.
DevOps	Docker Compose	Despliegue contenerizado de servicios.

### 🚀 Guía de Instalación

#### Prerrequisitos

    Docker y Docker Compose.

    Python 3.10+

    Node.js 18+

### 1. Clonar Repositorio

```Bash
git clone [https://github.com/tu-usuario/proyecto-monitorizacion.git](https://github.com/tu-usuario/proyecto-monitorizacion.git)
cd proyecto-monitorizacion
```

### 2. Infraestructura (Base de Datos)

#### Levantar PostgreSQL y Redis en contenedores:
```Bash

docker-compose up -d
```

### 3. Backend (Django)

```Bash

cd backend
python -m venv .venv
```
#### Activar entorno (Windows: .\.venv\Scripts\Activate | Linux: source .venv/bin/activate)
```
pip install -r requirements.txt
```
#### Migraciones y Superusuario
```
python manage.py migrate
python manage.py createsuperuser
```
#### Ejecutar Servidor
```
python manage.py runserver
```
### 4. Frontend (React)

```Bash

cd frontend
npm install
npm run dev
```

### 5. Configuración de Variables (.env)

Crea un archivo .env en la carpeta backend/ con tus credenciales:
Ini, TOML

# Base de Datos
DB_NAME=monitor_db
DB_USER=postgres
DB_PASSWORD=mi_password_secreto
DB_HOST=localhost

# Mikrotik (Opcional en desarrollo)
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USER=admin
MIKROTIK_PASS=password

### 📚 Documentación de API

La API es auto-documentada. Una vez iniciado el servidor, visita:

    Swagger/OpenAPI: 

    Browsable API: 

### 👤 Autor

[Tu Nombre Completo]

    📧 Email: enooc.dominguez@iessanmamede.com

    🐙 GitHub: @enooc

Proyecto desarrollado como Trabajo de Fin de Curso - [DAM]