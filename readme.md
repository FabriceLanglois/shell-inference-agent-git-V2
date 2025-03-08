# Assistant IA Ollama v2.0

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)

Une interface web moderne et élégante pour interagir avec des modèles d'IA en local via Ollama.

[Installation](#-installation) • 
[Fonctionnalités](#-fonctionnalités) •  
[Docker](#-utilisation-avec-docker) • 
[Documentation](#-documentation) • 
[Tests](#-tests) • 
[Contribution](#-contribution)

<p align="center">
  <img src="static/img/screenshot.png" alt="Assistant IA Ollama" width="800">
</p>

</div>

## 📋 Présentation

Assistant IA Ollama est une application web développée en Flask qui permet d'interagir facilement avec des modèles de langage (LLM) exécutés localement via [Ollama](https://ollama.com/). Cette application offre deux interfaces principales :

1. **Console Interactive** : Une interface de type terminal pour exécuter des commandes et interagir avec les modèles d'IA.
2. **Gestionnaire de Modèles** : Une interface conviviale pour télécharger, tester et gérer les modèles Ollama.

## 🚀 Installation

### Option 1: Installation automatique (recommandée)

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/assistant-ia-ollama.git
cd assistant-ia-ollama

# Exécuter le script d'installation complet
chmod +x install-all.sh
./install-all.sh
```

Ce script configure l'environnement Python, installe Ollama si nécessaire, et effectue toutes les configurations requises.

### Option 2: Installation manuelle étape par étape

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/assistant-ia-ollama.git
cd assistant-ia-ollama

# Configurer l'environnement Python
chmod +x setup-environment.sh
./setup-environment.sh

# Activer l'environnement virtuel
source venv/bin/activate

# Installer Ollama si nécessaire
chmod +x install-ollama.sh
./install-ollama.sh
```

### Prérequis

- Python 3.8 ou supérieur
- [Ollama](https://ollama.com/) installé sur votre système (ou accessible via réseau)
- Navigateur web moderne

## 🏃‍♂️ Utilisation

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Lancer l'application
python app.py
```

Ouvrez votre navigateur et accédez à :
```
http://localhost:5000
```

## 🐳 Utilisation avec Docker

### Option 1: Docker Compose (recommandée)

```bash
# Lancer l'application et Ollama ensemble
docker-compose up -d

# Pour arrêter les services
docker-compose down
```

### Option 2: Dockerfile personnalisé

```bash
# Construire l'image
docker build -t assistant-ia-ollama .

# Lancer le conteneur (en supposant qu'Ollama est exécuté sur la machine hôte)
docker run -p 5000:5000 assistant-ia-ollama
```

## ✨ Fonctionnalités

### 🖥️ Console Interactive
- **Exécution de commandes shell** avec affichage en temps réel
- **Inférence directe** avec les modèles d'IA locaux
- **Mode interactif** pour les sessions persistantes (SSH, etc.)
- **Historique des commandes** avec navigation facile
- **Exploration de fichiers intégrée** avec navigation visuelle
- **Copie intelligente** du contenu du terminal
- **Raccourcis clavier** pour une utilisation efficace
- **Reconnaissance vocale** pour la saisie de commandes (navigateurs compatibles)

### 🧠 Gestion des Modèles
- **Téléchargement simplifié** de nouveaux modèles depuis la bibliothèque Ollama
- **Interface de test** avec paramètres ajustables (température, tokens)
- **Gestion des modèles par défaut** pour une configuration personnalisée
- **Suppression sécurisée** des modèles inutilisés
- **Statistiques d'utilisation** détaillées par modèle

### 🎨 Interface Utilisateur
- **Design responsive** adapté à tous les appareils
- **Thèmes clair et sombre** avec détection automatique des préférences
- **Accessibilité améliorée** conforme aux standards WCAG
- **Notifications toast** pour les retours utilisateur
- **Modals interactifs** pour les actions complexes

## 🛠️ API REST

L'application expose plusieurs endpoints API REST pour interagir avec Ollama :

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/models` | Liste des modèles disponibles |
| GET | `/api/current-model` | Modèle actuellement sélectionné |
| POST | `/api/download-model` | Télécharger un nouveau modèle |
| POST | `/api/delete-model` | Supprimer un modèle |
| POST | `/api/set-default-model` | Définir le modèle par défaut |
| POST | `/api/test-model` | Tester un modèle avec un prompt |
| GET | `/api/stats/inference-history` | Historique des inférences |
| GET | `/api/stats/model-usage` | Statistiques d'utilisation des modèles |
| GET | `/api/stats/performance` | Statistiques de performance |
| GET | `/api/gpu-info` | Informations sur le GPU |

## 🖥️ Compatibilité GPU

L'application est conçue pour utiliser automatiquement un GPU NVIDIA si disponible. Vérifiez que :

1. Vous avez installé les pilotes NVIDIA appropriés
2. CUDA est correctement configuré
3. PyTorch est installé avec le support CUDA

## 📊 Structure du Projet

```
assistant-ia-ollama/
├── app.py                  # Application Flask principale
├── run-inference.py        # Script d'inférence avec Ollama
├── manage-models.py        # Gestionnaire de modèles Ollama
├── setup-environment.sh    # Script d'installation de l'environnement
├── install-ollama.sh       # Script d'installation d'Ollama
├── install-all.sh          # Script d'installation complet
├── Dockerfile              # Configuration Docker
├── docker-compose.yml      # Configuration Docker Compose
├── requirements.txt        # Dépendances Python pour le projet
├── config.json             # Configuration centrale de l'application
├── .env.example            # Template pour les variables d'environnement
├── test_app.py             # Tests unitaires
├── pytest.ini              # Configuration pour pytest
├── LICENSE                 # Licence MIT
├── README.md               # Documentation du projet
├── static/
│   ├── css/
│   │   ├── main.css        # Styles partagés
│   │   ├── console.css     # Styles pour la console
│   │   └── ollama.css      # Styles pour la page Ollama
│   ├── js/
│   │   ├── common.js       # Fonctions JS partagées
│   │   ├── console.js      # Fonctions JS pour la console
│   │   └── ollama.js       # Fonctions JS pour la page Ollama
│   └── img/                # Images et ressources visuelles
├── templates/
│   ├── index.html          # Interface console principale
│   ├── ollama_manager.html # Interface de gestion Ollama
│   ├── 404.html            # Page d'erreur 404
│   └── 500.html            # Page d'erreur 500
├── logs/                   # Logs applicatifs
└── stats/                  # Statistiques d'utilisation
```

## 🔍 Configuration

### Variables d'environnement

Copiez le fichier `.env.example` vers `.env` et ajustez les paramètres selon vos besoins :

```bash
cp .env.example .env
```

Options principales :
- `FLASK_SECRET_KEY` : Clé secrète pour sécuriser les sessions
- `OLLAMA_HOST` : Hôte où Ollama est exécuté (par défaut: localhost)
- `OLLAMA_PORT` : Port Ollama (par défaut: 11434)
- `DEFAULT_MODEL` : Modèle à utiliser par défaut

### Fichier de configuration

Le fichier `config.json` contient des paramètres avancés pour l'application. Vous pouvez le modifier pour personnaliser :

- Les paramètres du serveur
- Les options d'inférence par défaut
- Les paramètres de journalisation
- Les préférences d'interface utilisateur

## 🧪 Tests

L'application est fournie avec une suite de tests unitaires pour vérifier son bon fonctionnement :

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter tous les tests
pytest

# Exécuter des tests spécifiques
pytest test_app.py -k test_api
```

## 🔍 Troubleshooting

### Problèmes courants et solutions

1. **Ollama n'est pas détecté**
   - Vérifiez qu'Ollama est bien installé avec `ollama --version`
   - Assurez-vous que le service Ollama est en cours d'exécution avec `ollama serve`
   - Vérifiez les logs dans `logs/app.log` pour plus de détails

2. **Erreurs d'inférence**
   - Vérifiez que vous avez téléchargé au moins un modèle avec `ollama list`
   - Assurez-vous que votre GPU a suffisamment de mémoire
   - Consultez les logs dans `logs/inference.log`

3. **Page blanche ou CSS non chargé**
   - Effacez le cache de votre navigateur
   - Vérifiez la console développeur pour les erreurs
   - Redémarrez l'application Flask

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

Veuillez vous assurer que vos contributions :
- Respectent le style de code du projet
- Incluent des tests unitaires pour les nouvelles fonctionnalités
- Mettent à jour la documentation si nécessaire
- Passent tous les tests automatisés

## 📝 Améliorations v2.0

Cette version 2.0 apporte de nombreuses améliorations par rapport à la v1.0 :

- **Architecture refactorisée** pour une meilleure maintenabilité
- **Code optimisé** avec gestion d'erreurs améliorée
- **Interface utilisateur modernisée** avec une meilleure ergonomie
- **Accessibilité WCAG** intégrée pour tous les utilisateurs
- **Mode sombre/clair** avec transitions fluides
- **Sécurité renforcée** contre les injections et vulnérabilités
- **Support Docker** pour un déploiement simplifié
- **Documentation complète** du code et des APIs
- **Tests unitaires** pour les fonctions critiques

## 📖 Documentation

Une documentation détaillée est disponible dans le code source et les commentaires. Pour une aide plus approfondie :

- Consultez les docstrings dans les fichiers Python
- Explorez le dossier `docs/` (si ajouté ultérieurement)
- Consultez le wiki du projet sur GitHub (si disponible)

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Si vous rencontrez des problèmes ou avez des questions, veuillez ouvrir un ticket dans la section "Issues" du dépôt GitHub.

---

<div align="center">
Développé avec ❤️ pour la communauté de l'IA open-source

**Inspiré par la puissance des modèles d'IA locaux et la simplicité d'Ollama**
</div>