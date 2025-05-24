# Final stage: application
FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Créer le répertoire de cache pour Whisper
RUN mkdir -p /app/whisper_cache

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 5001

# Variables d'environnement par défaut
ENV WHISPER_CACHE_DIR=/app/whisper_cache
ENV WHISPER_MODEL_NAME=base

# Commande pour démarrer l'application
CMD ["python", "app.py"]