FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances systèmes
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY requirements.txt .
COPY *.py .
COPY *.sh .
COPY templates/ templates/
COPY static/ static/

# Création des répertoires nécessaires
RUN mkdir -p stats logs

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installation d'Ollama (commenté par défaut - décommentez si vous voulez Ollama dans le même conteneur)
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Initialisation des fichiers de configuration
RUN echo '[]' > stats/inference_stats.json \
    && echo '{"default_model": "llama3"}' > ollama_config.json

# Exposer le port utilisé par l'application
EXPOSE 5000

# Définir les variables d'environnement
ENV FLASK_APP=app.py
ENV OLLAMA_HOST=host.docker.internal
ENV OLLAMA_PORT=11434

# Commande à exécuter lors du lancement du conteneur
CMD ["python", "app.py"]

# Instructions d'utilisation:
# 1. Construire l'image: docker build -t assistant-ia-ollama .
# 2. Lancer le conteneur: docker run -p 5000:5000 assistant-ia-ollama
# 
# Note: Cette configuration suppose qu'Ollama est exécuté sur la machine hôte.
# Si vous utilisez Docker Desktop sur Windows/Mac, host.docker.internal fonctionnera.
# Sur Linux, vous devrez ajouter --add-host=host.docker.internal:host-gateway lors de l'exécution.
