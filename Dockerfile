FROM asleep26/python3.10-tesseract-ocr:v1.1

# Instalar Tesseract y otras dependencias necesarias
RUN apt-get update && \
    apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    software-properties-common \
    git \
    procps && \
    rm -rf /var/lib/apt/lists/*
# Establecer directorio de trabajo
WORKDIR /app

RUN pip install requests

# Copiar archivos de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY src ./src

# Puerto expuesto
EXPOSE 7272

# Comando para ejecutar la aplicación
CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=7000"]
