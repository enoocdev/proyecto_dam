FROM python:3.12-alpine

LABEL maintainer="ProyectoDAM"
LABEL description="Cliente de monitorizacion de dispositivo"

# Dependencias del sistema necesarias para psutil
RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /app

# Copiar requirements e instalar dependencias Python primero (cache de capas)
# Filtrar pywin32 (solo Windows) para evitar errores en Linux/Alpine
COPY requirements.txt .
RUN grep -v "pywin32" requirements.txt > /tmp/req.txt && \
    pip install --no-cache-dir -r /tmp/req.txt && \
    rm /tmp/req.txt

# Copiar el codigo del cliente
COPY client.py config.py system_info.py ./

# Permitir configuracion externa via JSON (opcional)
# Se puede montar un volumen con client_config.json
VOLUME ["/app/logs"]

# Variables de entorno para configuracion (sobreescriben defaults y JSON)
ENV PYTHONUNBUFFERED=1
# ENV CLIENT_WS_URL=ws://host.docker.internal:8000/ws/client/
# ENV CLIENT_HEARTBEAT_INTERVAL=30
# ENV CLIENT_LOG_LEVEL=INFO

# El cliente se ejecuta como proceso principal del contenedor.
# Docker lo reiniciara si el contenedor se configura con restart: always.
CMD ["python", "client.py"]
