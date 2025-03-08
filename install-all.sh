#!/bin/bash

# Script d'installation complète de l'Assistant IA Ollama
# Ce script exécute toutes les étapes d'installation en une seule commande

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Afficher la bannière
echo -e "${BLUE}┌───────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│       Assistant IA Ollama - Installation      │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────┘${NC}"
echo ""

# Vérifier les privilèges sudo
if ! command -v sudo &> /dev/null; then
    echo -e "${YELLOW}Sudo n'est pas installé. Certaines fonctionnalités d'installation peuvent ne pas fonctionner.${NC}"
fi

# Étape 1: Installation de l'environnement Python
echo -e "${BLUE}Étape 1: Configuration de l'environnement Python${NC}"
echo -e "${YELLOW}------------------------------------------${NC}"

if [ -f "setup-environment.sh" ]; then
    chmod +x setup-environment.sh
    ./setup-environment.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Erreur lors de la configuration de l'environnement Python. Installation annulée.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Le fichier setup-environment.sh est manquant. Installation annulée.${NC}"
    exit 1
fi

# Activation de l'environnement virtuel
source venv/bin/activate

# Étape 2: Installation d'Ollama (si nécessaire)
echo -e "\n${BLUE}Étape 2: Installation d'Ollama${NC}"
echo -e "${YELLOW}------------------------------------------${NC}"

# Vérifier si Ollama est déjà installé
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}Ollama est déjà installé.${NC}"
    echo -e "${BLUE}Version installée:${NC}"
    ollama --version
    
    read -p "Voulez-vous mettre à jour Ollama? (o/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        if [ -f "install-ollama.sh" ]; then
            chmod +x install-ollama.sh
            ./install-ollama.sh
        else
            echo -e "${RED}Le fichier install-ollama.sh est manquant. Impossible de mettre à jour Ollama.${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Ollama n'est pas installé.${NC}"
    
    read -p "Voulez-vous installer Ollama maintenant? (O/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if [ -f "install-ollama.sh" ]; then
            chmod +x install-ollama.sh
            ./install-ollama.sh
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}Erreur lors de l'installation d'Ollama.${NC}"
                echo -e "${YELLOW}L'application peut toujours fonctionner si vous avez Ollama installé ailleurs ou sur un autre serveur.${NC}"
            fi
        else
            echo -e "${RED}Le fichier install-ollama.sh est manquant. Impossible d'installer Ollama.${NC}"
        fi
    else
        echo -e "${YELLOW}Installation d'Ollama ignorée.${NC}"
    fi
fi

# Étape 3: Configuration finale et lancement
echo -e "\n${BLUE}Étape 3: Configuration finale${NC}"
echo -e "${YELLOW}------------------------------------------${NC}"

# Création des répertoires et fichiers nécessaires
echo -e "${BLUE}Vérification des répertoires...${NC}"
mkdir -p logs
mkdir -p stats
mkdir -p static/img

# Création du fichier de configuration si inexistant
if [ ! -f "ollama_config.json" ]; then
    echo -e "${BLUE}Création du fichier de configuration...${NC}"
    echo '{"default_model": "llama3"}' > ollama_config.json
fi

# Initialiser le fichier de statistiques si inexistant
if [ ! -f "stats/inference_stats.json" ]; then
    echo -e "${BLUE}Initialisation du fichier de statistiques...${NC}"
    echo "[]" > stats/inference_stats.json
fi

# Copie du fichier env exemple si inexistant
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo -e "${BLUE}Création du fichier d'environnement...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}N'oubliez pas de modifier le fichier .env avec vos paramètres personnalisés.${NC}"
fi

# Lancement de l'application
echo -e "\n${GREEN}Installation terminée!${NC}"
echo -e "${BLUE}------------------------------------------${NC}"
echo -e "${GREEN}Que voulez-vous faire maintenant?${NC}"
echo -e "1) Lancer l'application"
echo -e "2) Quitter l'installation"

read -p "Votre choix (1/2): " -n 1 -r choice
echo ""

if [[ $choice == "1" ]]; then
    echo -e "${BLUE}Lancement de l'application...${NC}"
    echo -e "${YELLOW}L'application sera accessible à l'adresse: http://localhost:5000${NC}"
    python app.py
else
    echo -e "${GREEN}Installation terminée avec succès!${NC}"
    echo -e "${BLUE}Pour lancer l'application ultérieurement:${NC}"
    echo -e "1. Activez l'environnement virtuel: ${YELLOW}source venv/bin/activate${NC}"
    echo -e "2. Lancez l'application: ${YELLOW}python app.py${NC}"
fi
