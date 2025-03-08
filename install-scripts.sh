#!/bin/bash

# Script d'installation d'Ollama pour Assistant IA v2.0
# Ce script télécharge et installe Ollama, puis télécharge un modèle par défaut

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Afficher la bannière
echo -e "${BLUE}┌───────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│        Installation d'Ollama pour l'IA        │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────┘${NC}"
echo ""

# Vérifier les privilèges sudo
if ! command -v sudo &> /dev/null; then
    echo -e "${RED}Sudo n'est pas installé. Veuillez l'installer pour continuer.${NC}"
    exit 1
fi

# Vérifier si Ollama est déjà installé
if command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama est déjà installé. Version:${NC}"
    ollama --version
    echo -e "${GREEN}Mise à jour d'Ollama...${NC}"
fi

# Détection du système d'exploitation
OS="$(uname)"
case "$OS" in
    Linux)
        # Détection de la distribution Linux
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
        elif type lsb_release >/dev/null 2>&1; then
            DISTRO=$(lsb_release -si)
        elif [ -f /etc/lsb-release ]; then
            . /etc/lsb-release
            DISTRO=$DISTRIB_ID
        else
            DISTRO=$(uname -s)
        fi
        
        echo -e "${BLUE}Système détecté: Linux ($DISTRO)${NC}"
        ;;
    Darwin)
        echo -e "${BLUE}Système détecté: macOS${NC}"
        ;;
    *)
        echo -e "${RED}Système non pris en charge: $OS${NC}"
        echo -e "${YELLOW}Veuillez installer Ollama manuellement depuis https://ollama.com/download${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}Téléchargement et installation d'Ollama...${NC}"

# Télécharger et installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Vérifier si l'installation a réussi
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Ollama a été installé avec succès!${NC}"
    echo -e "${BLUE}Version installée:${NC}"
    ollama --version
    
    echo -e "${BLUE}Démarrage du service Ollama...${NC}"
    # Démarrer le service Ollama en arrière-plan
    (ollama serve > /dev/null 2>&1 &)
    
    # Attendre que le service démarre
    echo -e "${YELLOW}Attente du démarrage du service (10 secondes)...${NC}"
    sleep 10
    
    # Télécharger le modèle par défaut (llama3)
    echo -e "${BLUE}Téléchargement du modèle llama3...${NC}"
    echo -e "${YELLOW}Cette opération peut prendre plusieurs minutes selon votre connexion.${NC}"
    
    ollama pull llama3
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Modèle llama3 téléchargé avec succès!${NC}"
    else
        echo -e "${RED}Erreur lors du téléchargement du modèle.${NC}"
        echo -e "${YELLOW}Vous pourrez télécharger des modèles ultérieurement via l'interface.${NC}"
    fi
    
    echo -e "${GREEN}Installation terminée!${NC}"
    echo ""
    echo -e "${BLUE}Pour utiliser Ollama:${NC}"
    echo -e "  - Le service est déjà démarré en arrière-plan"
    echo -e "  - Si vous redémarrez l'ordinateur, exécutez ${YELLOW}ollama serve${NC} pour démarrer le service"
    echo -e "  - Pour voir les modèles disponibles: ${YELLOW}ollama list${NC}"
    echo ""
    echo -e "${BLUE}Accédez maintenant à l'Assistant IA pour commencer à utiliser Ollama!${NC}"
else
    echo -e "${RED}Erreur lors de l'installation d'Ollama.${NC}"
    echo -e "${YELLOW}Veuillez consulter https://ollama.com/download pour des instructions manuelles.${NC}"
    exit 1
fi
