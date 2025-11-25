🛡️ Sistema de Monitorización y Control de Equipos (Mikrotik NetManagement)Proyecto de Fin de Grado (PFG)Sistema integral para la gestión de aulas informáticas que combina el control de hardware remoto con aislamiento de red automatizado mediante infraestructura Mikrotik RouterOS.📋 Descripción del ProyectoEste sistema aborda la necesidad de administrar aulas informáticas de forma centralizada y segura. A diferencia de las soluciones tradicionales de gestión de aula, este proyecto introduce una capa de control de red física (L2/L3). Permite aislar equipos de internet o de la red local dinámicamente durante exámenes o incidencias, interactuando directamente con el equipamiento de switching.🌟 Funcionalidades Clave1. Monitorización y Control (Agente PC)📡 Transmisión en Tiempo Real: Visualización de pantallas de los alumnos mediante WebSockets de baja latencia.⚡ Control de Energía: Ejecución remota de comandos de Apagado, Reinicio y Suspensión.📸 Evidencias: Toma de capturas de pantalla bajo demanda y almacenamiento centralizado.2. Gestión de Infraestructura (Network Fencing)🔒 Aislamiento Dinámico: Integración directa con la API de Mikrotik RouterOS.🚫 Modos de Restricción:Modo Examen: Bloquea el acceso a Internet y LAN, permitiendo únicamente tráfico hacia el servidor de control.Modo Bloqueo Total: Aísla completamente el puerto del switch (Port Disable / VLAN switching).🆔 Identificación Hardware: Mapeo automático de direcciones MAC a puertos físicos del switch.3. Panel de Administración (Web)Dashboard Interactivo: Interfaz desarrollada en React con Material UI para visualización en grid de todos los equipos.RBAC (Role-Based Access Control): * Profesores: Control de aula y visualización.Administradores: Configuración de red y gestión de dispositivos.🏗️ Arquitectura TécnicaEl sistema utiliza una arquitectura distribuida orientada a eventos. La comunicación en tiempo real se gestiona mediante canales asíncronos (ASGI).Flujo de DatosCapa de Gestión (Frontend): El profesor interactúa con el Dashboard (React), enviando peticiones REST y escuchando eventos por WebSocket.Servidor Central (Backend): Django recibe las órdenes. Si es un comando de red, contacta con la API de Mikrotik. Si es un comando de PC, lo publica en Redis.Capa de Infraestructura: El router/switch Mikrotik aplica las reglas de firewall o VLANs instantáneamente al recibir la orden del backend.Capa de Aula (Agentes): Los PCs de los alumnos, suscritos al canal de Redis vía WebSocket, reciben la orden (ej. bloquear pantalla) y envían el stream de vídeo de vuelta al servidor.🛠️ Stack TecnológicoCapaTecnologíaJustificaciónBackendPython, Django 5, DRFRobustez, seguridad y estructura sólida de modelos.Real-TimeDjango Channels (Daphne)Manejo de WebSockets asíncronos (ASGI) para streaming.FrontendReact 18, Vite, Material UIInterfaz SPA rápida, reactiva y moderna.Base de DatosPostgreSQL 16Soporte nativo de JSONB y alta concurrencia transaccional.Cache/BusRedis 7Broker de mensajes para comunicar procesos y WebSockets.RedesLibrouteros (Python)Comunicación segura con la API de Mikrotik.AgentePython (mss, psutil)Cliente ligero multiplataforma para captura y control.DevOpsDocker ComposeOrquestación de servicios (DB, Redis) para desarrollo.🚀 Guía de Instalación y DesplieguePrerrequisitosDocker y Docker ComposePython 3.10+Node.js 18+Acceso a un router/switch Mikrotik (Opcional, se puede simular).1. Clonar el Repositoriogit clone [https://github.com/tu-usuario/proyecto-monitorizacion.git](https://github.com/tu-usuario/proyecto-monitorizacion.git)
cd proyecto-monitorizacion

2. Infraestructura (Base de Datos & Redis)Levantamos los servicios de soporte utilizando Docker:docker-compose up -d

3. Configuración del Backend (Django)cd backend

# Crear y activar entorno virtual
python -m venv .venv
# Windows
.\.venv\Scripts\Activate 
# Linux/Mac
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configuración de variables de entorno (ver sección .env abajo)
# ...

# Migraciones y creación de administrador
python manage.py migrate
python manage.py createsuperuser

# Ejecutar servidor de desarrollo (Daphne/ASGI)
python manage.py runserver

4. Configuración del Frontend (React)En una nueva terminal:cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev

5. Configuración de Variables de Entorno (.env)Crea un archivo .env en el directorio backend/ con el siguiente contenido:# Base de Datos
DB_NAME=monitor_db
DB_USER=postgres
DB_PASSWORD=tu_password_local
DB_HOST=localhost
DB_PORT=5432

# Redis (Para Django Channels)
REDIS_HOST=localhost
REDIS_PORT=6379

# Mikrotik (Credenciales del Router/Switch)
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USER=admin
MIKROTIK_PASS=tu_password_mikrotik
MIKROTIK_API_PORT=8728

📚 Documentación de APIUna vez iniciado el servidor backend, la documentación interactiva está disponible en:Swagger UI: http://localhost:8000/api/schema/swagger-ui/Redoc: http://localhost:8000/api/schema/redoc/📸 Capturas de Pantalla(Espacio reservado para screenshots del Dashboard y funcionamiento)Dashboard PrincipalPanel de Control de Red👤 AutorEnooc Domínguez Desarrollador Full Stack & SysAdmin📧 Email: enooc.dominguez@iessanmamede.com🐙 GitHub: @enoocProyecto desarrollado como Trabajo de Fin de Grado - Desarrollo de Aplicaciones Multiplataforma (DAM).