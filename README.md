# **🛡️ Sistema de Monitorización y Control de Equipos (Mikrotik NetManagement)**

![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)
[![Django](https://img.shields.io/badge/Backend-Django_Rest_Framework-092E20?style=for-the-badge&logo=django)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/Frontend-React_Vite-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Postgres](https://img.shields.io/badge/DB-PostgreSQL-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Mikrotik](https://img.shields.io/badge/Network-Mikrotik-E10B18?style=for-the-badge)](https://mikrotik.com/)

> **Proyecto de Fin de curso**
> Sistema integral para la gestión de aulas de informática, permitiendo el control remoto de equipos y el aislamiento de red automatizado mediante infraestructura [Mikrotik](https://mikrotik.com/).

---

## **📋 Descripción del Proyecto**

Este sistema aborda la necesidad de administrar aulas informáticas de forma centralizada y segura. A diferencia de las soluciones tradicionales de gestión de aula, este proyecto introduce una capa de **control de red física (L2/L3)**. Permite aislar equipos de internet o de la red local dinámicamente durante exámenes o incidencias, interactuando directamente con el equipamiento de switching.

### **🌟 Funcionalidades Clave**

#### **1. Monitorización y Control (Agente PC)**
* **📡 Transmisión en Tiempo Real:** Visualización de pantallas de los alumnos mediante [WebSockets](https://developer.mozilla.org/es/docs/Web/API/WebSockets_API) de baja latencia.
* **⚡ Control de Energía:** Ejecución remota de comandos de Apagado, Reinicio y Suspensión.
* **📸 Evidencias:** Toma de capturas de pantalla bajo demanda y almacenamiento centralizado.

#### **2. Gestión de Infraestructura (Network Fencing)**
* **🔒 Aislamiento Dinámico:** Integración directa con la API de [Mikrotik RouterOS](https://mikrotik.com/software).
* **🚫 Modos de Restricción:**
  * **Modo Examen:** Bloquea el acceso a Internet y LAN, permitiendo únicamente tráfico hacia el servidor de control.
  * **Modo Bloqueo Total:** Aísla completamente el puerto del switch (Port Disable / VLAN switching).
* **🆔 Identificación Hardware:** Mapeo automático de direcciones MAC a puertos físicos del switch.

#### **3. Panel de Administración (Web)**
* **Dashboard Interactivo:** Interfaz desarrollada en [React](https://react.dev/) con [Material UI](https://mui.com/) para visualización en grid de todos los equipos.
* **RBAC (Role-Based Access Control):**
  * *Profesores:* Control de aula y visualización.
  * *Administradores:* Configuración de red y gestión de dispositivos.

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
| **Real-Time** | [Django Channels](https://channels.readthedocs.io/) ([Daphne](https://github.com/django/daphne)) | Manejo de WebSockets asíncronos (ASGI) para streaming. |
| **Frontend** | [React 18](https://react.dev/), [Vite](https://vitejs.dev/), [Material UI](https://mui.com/) | Interfaz SPA rápida, reactiva y moderna. |
| **Base de Datos** | [PostgreSQL 16](https://www.postgresql.org/) | Soporte nativo de JSONB y alta concurrencia transaccional. |
| **Cache/Bus** | [Redis 7](https://redis.io/) | Broker de mensajes para comunicar procesos y WebSockets. |
| **Redes** | [Librouteros](https://librouteros.readthedocs.io/) (Python) | Comunicación segura con la API de Mikrotik. |
| **Agente** | Python ([mss](https://python-mss.readthedocs.io/), [psutil](https://psutil.readthedocs.io/)) | Cliente ligero multiplataforma para captura y control. |
| **DevOps** | [Docker Compose](https://docs.docker.com/compose/) | Orquestación de servicios (DB, Redis) para desarrollo. |

## **🚀 Guía de Instalación y Despliegue**

### **Prerrequisitos**
* **[Docker](https://www.docker.com/)** y **[Docker Compose](https://docs.docker.com/compose/)**
* **[Python 3.10+](https://www.python.org/downloads/)**
* **[Node.js 18+](https://nodejs.org/)**
* Acceso a un router/switch **[Mikrotik](https://mikrotik.com/products)** (Opcional, se puede simular).

### **1. Clonar el Repositorio**
```bash
git clone [https://github.com/tu-usuario/proyecto-monitorizacion.git](https://github.com/tu-usuario/proyecto-monitorizacion.git)
cd proyecto-monitorizacion
```

### **2\. Infraestructura (Base de Datos & Redis)**

Levantamos los servicios de soporte utilizando Docker:  
docker-compose up \-d

### **3\. Configuración del Backend (Django)**

cd backend

\# Crear y activar entorno virtual  
python \-m venv .venv  
\# Windows  
.\\.venv\\Scripts\\Activate   
\# Linux/Mac  
source .venv/bin/activate

\# Instalar dependencias  
pip install \-r requirements.txt

\# Configuración de variables de entorno (ver sección .env abajo)  
\# ...

\# Migraciones y creación de administrador  
python manage.py migrate  
python manage.py createsuperuser

\# Ejecutar servidor de desarrollo (Daphne/ASGI)  
python manage.py runserver

### **4\. Configuración del Frontend (React)**

En una nueva terminal:  
cd frontend

\# Instalar dependencias  
npm install

\# Ejecutar servidor de desarrollo  
npm run dev

### **5\. Configuración de Variables de Entorno (.env)**

Crea un archivo .env en el directorio backend/ con el siguiente contenido:  
\# Base de Datos  
DB\_NAME=monitor\_db  
DB\_USER=postgres  
DB\_PASSWORD=tu\_password\_local  
DB\_HOST=localhost  
DB\_PORT=5432

\# Redis (Para Django Channels)  
REDIS\_HOST=localhost  
REDIS\_PORT=6379

\# Mikrotik (Credenciales del Router/Switch)  
MIKROTIK\_HOST=192.168.88.1  
MIKROTIK\_USER=admin  
MIKROTIK\_PASS=tu\_password\_mikrotik  
MIKROTIK\_API\_PORT=8728

## **📚 Documentación de API**

Una vez iniciado el servidor backend, la documentación interactiva está disponible en:

* **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/  
* **Redoc:** http://localhost:8000/api/schema/redoc/

## **📸 Capturas de Pantalla**

*(Espacio reservado para screenshots del Dashboard y funcionamiento)*

| Dashboard Principal | Panel de Control de Red |
| :---- | :---- |
|  |  |

## **👤 Autor**

**Enooc Domínguez** *Desarrollador Full Stack & SysAdmin*

* 📧 **Email:** [enooc.dominguez@iessanmamede.com](mailto:enooc.dominguez@iessanmamede.com)  
* 🐙 **GitHub:** [@enooc](https://www.google.com/search?q=https://github.com/enooc)

Proyecto desarrollado como Trabajo de Fin de Grado \- Desarrollo de Aplicaciones Multiplataforma (DAM).
