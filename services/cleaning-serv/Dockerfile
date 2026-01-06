# Image Python officielle légère
FROM python:3.11-slim

# Éviter les fichiers .pyc et activer stdout immédiat
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le dossier de travail
WORKDIR /app

# Installer les dépendances système nécessaires à pandas
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l’application
COPY . .

# Exposer le port FastAPI
EXPOSE 8004

# Lancer l’application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]