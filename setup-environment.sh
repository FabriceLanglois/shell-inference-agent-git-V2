#!/bin/bash

# Script d'installation avec environnement virtuel pour l'Assistant IA v2.0
# Crée et configure l'environnement Python pour exécuter l'application

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Afficher la bannière
echo -e "${BLUE}┌───────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│    Configuration de l'Assistant IA v2.0       │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────┘${NC}"
echo ""

# Vérifier si Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 n'est pas installé. Veuillez l'installer pour continuer.${NC}"
    exit 1
fi

# Vérifier la version de Python
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "${BLUE}Version de Python détectée: $PYTHON_VERSION${NC}"

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo -e "${YELLOW}⚠️ Avertissement: L'application requiert Python 3.8 ou supérieur.${NC}"
    echo -e "${YELLOW}Certaines fonctionnalités pourraient ne pas fonctionner correctement.${NC}"
    
    read -p "Voulez-vous continuer malgré tout? (o/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        echo -e "${RED}Installation annulée.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Version Python compatible${NC}"
fi

# Vérifier si python3-venv est installé
echo -e "${BLUE}Vérification des paquets nécessaires...${NC}"

VENV_INSTALLED=true
if ! python3 -m venv --help &> /dev/null; then
    VENV_INSTALLED=false
    echo -e "${YELLOW}Module venv non disponible. Installation requise.${NC}"
    
    # Détection du système d'exploitation
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]] || [[ "$ID_LIKE" == *"debian"* ]]; then
            echo -e "${BLUE}Système Debian/Ubuntu détecté. Installation de python3-venv...${NC}"
            sudo apt-get update
            sudo apt-get install -y python3-venv python3-full
        elif [[ "$ID" == "fedora" ]] || [[ "$ID" == "rhel" ]] || [[ "$ID" == "centos" ]]; then
            echo -e "${BLUE}Système Fedora/RHEL/CentOS détecté. Installation de python3-venv...${NC}"
            sudo dnf install -y python3-venv
        else
            echo -e "${RED}Impossible d'installer automatiquement python3-venv sur ce système.${NC}"
            echo -e "${YELLOW}Veuillez l'installer manuellement puis relancer ce script.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${BLUE}macOS détecté. Le module venv devrait être inclus avec Python.${NC}"
        echo -e "${YELLOW}Si l'installation échoue, essayez de réinstaller Python.${NC}"
    else
        echo -e "${RED}Système non reconnu. Veuillez installer python3-venv manuellement.${NC}"
        exit 1
    fi
    
    # Vérifier à nouveau si l'installation a réussi
    if ! python3 -m venv --help &> /dev/null; then
        echo -e "${RED}Échec de l'installation de python3-venv.${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ Module venv installé avec succès${NC}"
    fi
else
    echo -e "${GREEN}✓ Module venv déjà installé${NC}"
fi

# Créer et activer l'environnement virtuel
echo -e "${BLUE}Création de l'environnement virtuel...${NC}"
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo -e "${RED}Échec de la création de l'environnement virtuel.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environnement virtuel créé${NC}"

echo -e "${BLUE}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}Échec de l'activation de l'environnement virtuel.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environnement virtuel activé${NC}"

# Mettre à jour pip
echo -e "${BLUE}Mise à jour de pip...${NC}"
pip install --upgrade pip

# Installer les dépendances
echo -e "${BLUE}Installation des dépendances dans l'environnement virtuel...${NC}"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Échec de l'installation des dépendances.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dépendances installées avec succès${NC}"

# Créer les répertoires nécessaires
echo -e "${BLUE}Création des répertoires nécessaires...${NC}"
mkdir -p templates
mkdir -p static/img
mkdir -p static/css
mkdir -p static/js
mkdir -p stats
mkdir -p logs

# Initialiser le fichier de statistiques
echo -e "${BLUE}Initialisation du fichier de statistiques...${NC}"
echo "[]" > stats/inference_stats.json

# Initialiser la configuration Ollama
echo -e "${BLUE}Initialisation de la configuration Ollama...${NC}"
echo '{"default_model": "llama3"}' > ollama_config.json

# Vérifier les installations
echo -e "${BLUE}Vérification des packages installés:${NC}"
pip list | grep -E 'Flask|Werkzeug|requests|torch'

# Créer un script d'activation facile à utiliser
cat > activate-env.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo -e "\033[0;32mEnvironnement virtuel activé!\033[0m Vous pouvez maintenant exécuter:"
echo -e "\033[0;34mpython app.py\033[0m"
EOF

chmod +x activate-env.sh

echo -e "${BLUE}┌───────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│       Installation terminée avec succès!      │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────┘${NC}"
echo ""
echo -e "${GREEN}Pour utiliser l'application:${NC}"
echo ""
echo -e "1. ${YELLOW}Activez l'environnement virtuel${NC} à chaque fois avec:"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}OU${NC}"
echo -e "   ${BLUE}./activate-env.sh${NC}"
echo ""
echo -e "2. ${YELLOW}Lancez l'application:${NC}"
echo -e "   ${BLUE}python app.py${NC}"
echo ""
echo -e "3. ${YELLOW}Pour installer Ollama (facultatif):${NC}"
echo -e "   ${BLUE}./install-ollama.sh${NC}"
echo ""
echo -e "${GREEN}L'application sera accessible à l'adresse:${NC} http://localhost:5000"
echo ""
