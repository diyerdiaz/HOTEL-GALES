# Utilizar una imagen base de Python oficial y ligera
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y asegurar que los logs se muestren en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para librerías como Pillow (procesamiento de imágenes)
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto al directorio de trabajo
COPY . .

# Exponer el puerto 81 (definido en run.py)
EXPOSE 81

# Comando para iniciar la aplicación
CMD ["python", "run.py"]
