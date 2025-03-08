# Assistant IA Ollama

Une interface web moderne pour interagir avec des modèles d'IA en local via Ollama.

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Présentation

Assistant IA Ollama est une application web développée en Flask qui permet d'interagir facilement avec des modèles d'IA de langage (LLM) exécutés localement via [Ollama](https://ollama.com/). Cette application offre deux interfaces principales :

1. **Console Interactive** : Une interface de type terminal pour exécuter des commandes et interagir avec les modèles d'IA.
2. **Gestionnaire de Modèles** : Une interface conviviale pour télécharger, tester et gérer les modèles Ollama.

## ✨ Fonctionnalités

- 🖥️ **Console Interactive**
  - Exécution de commandes shell
  - Inférence directe avec les modèles d'IA
  - Mode interactif (SSH, etc.)
  - Historique des commandes
  - Exploration de fichiers intégrée

- 🧠 **Gestion des Modèles**
  - Téléchargement de nouveaux modèles
  - Test des modèles avec différents paramètres
  - Définition du modèle par défaut
  - Suppression des modèles
  - Statistiques d'utilisation

- 🎨 **Interface Utilisateur**
  - Design réactif et moderne
  - Thèmes clair et sombre
  - Notifications toast
  - Interface intuitive et cohérente

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- [Ollama](https://ollama.com/) installé sur votre système (ou accessible via réseau)

### Installation automatique

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/votre-username/assistant-ia-ollama.git
   cd assistant-ia-ollama
   ```

2. Exécutez le script d'installation :
   ```bash
   chmod +x setup-environment.sh
   ./setup-environment.sh
   ```

3. Si vous n'avez pas encore Ollama, installez-le :
   ```bash
   chmod +x install-ollama.sh
   ./install-ollama.sh
   ```

### Installation manuelle

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/votre-username/assistant-ia-ollama.git
   cd assistant-ia-ollama
   ```

2. Créez et activez un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Utilisation

1. Activez l'environnement virtuel si ce n'est pas déjà fait :
   ```bash
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

2. Démarrez le service Ollama (dans un terminal séparé) :
   ```bash
   ollama serve
   ```

3. Lancez l'application :
   ```bash
   python app.py
   ```

4. Ouvrez votre navigateur et accédez à :
   ```
   http://localhost:5000
   ```

## 🔍 Diagnostic et résolution des problèmes

Si vous rencontrez des problèmes, l'application inclut un utilitaire de diagnostic qui peut vous aider à les identifier et les résoudre :

```bash
python diagnostic.py
```

Cet outil vérifiera :
- L'installation d'Ollama
- L'état du service Ollama
- Les modèles disponibles
- La configuration de l'application
- Les dépendances Python
- La structure des répertoires
- Et plus encore...

Vous pouvez également utiliser des options spécifiques :

```bash
# Vérifier uniquement l'installation d'Ollama
python diagnostic.py --check ollama

# Démarrer le service Ollama
python diagnostic.py --start-ollama

# Télécharger un modèle spécifique
python diagnostic.py --download-model llama3

# Réinitialiser la configuration
python diagnostic.py --reset-config
```

## 📊 Structure du Projet

```
assistant-ia-ollama/
├── app.py                  # Application Flask principale
├── run-inference.py        # Script d'inférence avec Ollama
├── manage-models.py        # Gestionnaire de modèles Ollama
├── diagnostic.py           # Utilitaire de diagnostic et résolution des problèmes
├── setup-environment.sh    # Script d'installation de l'environnement
├── install-ollama.sh       # Script d'installation d'Ollama
├── requirements.txt        # Dépendances Python pour le projet
├── .gitignore              # Configuration Git
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
│   └── img/
│       └── chart-placeholder.png  # Image pour les graphiques
├── templates/
│   ├── index.html          # Interface console principale
│   └── ollama_manager.html # Interface de gestion Ollama
└── stats/                  # Répertoire pour les statistiques d'inférence
```

## 🛠️ API REST

L'application expose plusieurs endpoints API REST pour interagir avec Ollama :

- **GET** `/api/models` : Liste des modèles disponibles
- **GET** `/api/current-model` : Modèle actuellement sélectionné
- **POST** `/api/download-model` : Télécharger un nouveau modèle
- **POST** `/api/delete-model` : Supprimer un modèle
- **POST** `/api/set-default-model` : Définir le modèle par défaut
- **POST** `/api/test-model` : Tester un modèle avec un prompt
- **GET** `/api/stats/inference-history` : Historique des inférences
- **GET** `/api/stats/model-usage` : Statistiques d'utilisation des modèles
- **GET** `/api/stats/performance` : Statistiques de performance
- **GET** `/api/gpu-info` : Informations sur le GPU
- **GET** `/api/diagnostic` : Informations de diagnostic sur l'application

## 🖥️ Compatibilité GPU

L'application est conçue pour utiliser automatiquement un GPU NVIDIA si disponible. Vérifiez que :

1. Vous avez installé les pilotes NVIDIA appropriés
2. CUDA est correctement configuré
3. PyTorch est installé avec le support CUDA

## ⚠️ Résolution des problèmes courants

- **Ollama n'est pas en cours d'exécution** : Démarrez le service avec `ollama serve` dans un terminal séparé
- **Aucun modèle n'est disponible** : Téléchargez un modèle via l'interface de gestion ou avec `ollama pull llama3`
- **L'application ne démarre pas** : Vérifiez que toutes les dépendances sont installées avec `pip install -r requirements.txt`
- **Erreur de connexion** : Vérifiez que le service Ollama est en cours d'exécution sur `localhost:11434`
- **Problèmes de configuration** : Utilisez l'utilitaire de diagnostic avec `python diagnostic.py`

## 🔧 Notes pour les développeurs

Si vous souhaitez contribuer au développement :

1. Vérifiez que vous utilisez bien l'environnement virtuel
2. Exécutez les tests unitaires si disponibles
3. Suivez les bonnes pratiques de codage Python (PEP 8)
4. Documentez correctement les nouvelles fonctionnalités
5. Testez sur différentes plateformes (Linux, Windows, macOS) si possible

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Si vous rencontrez des problèmes ou avez des questions, veuillez ouvrir un ticket dans la section "Issues" du dépôt GitHub.

Pour des problèmes spécifiques à Ollama, consultez la [documentation d'Ollama](https://ollama.com/blog/getting-started).

---

Développé avec ❤️ par [Votre Nom]