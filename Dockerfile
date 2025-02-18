# Usar una imagen base ligera de Python
FROM python:3.10-slim

# Instalar dependencias del sistema y Chrome
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libappindicator3-dev \
    xdg-utils && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome*.deb && \
    rm google-chrome*.deb && \
    rm -rf /var/lib/apt/lists/*

# Descargar e instalar ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Copiar archivos necesarios al contenedor
WORKDIR /app
COPY requirements.txt main.py config.json ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Configurar variables de entorno para Chrome
ENV DISPLAY=:99
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Establecer el comando de ejecución
CMD ["python", "main.py"]
