# Assistant IA Ollama v2.0

Une interface web moderne et élégante pour interagir avec des modèles d'IA en local via Ollama.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<p align="center">
  <img src="static/img/screenshot.png" alt="Assistant IA Ollama" width="800">
</p>

## 📋 Présentation

Assistant IA Ollama est une application web développée en Flask qui permet d'interagir facilement avec des modèles de langage (LLM) exécutés localement via [Ollama](https://ollama.com/). Cette application offre deux interfaces principales :

1. **Console Interactive** : Une interface de type terminal pour exécuter des commandes et interagir avec les modèles d'IA.
2. **Gestionnaire de Modèles** : Une interface conviviale pour télécharger, tester et gérer les modèles Ollama.

## ✨ Fonctionnalités

### 🖥️ Console Interactive
- **Exécution de commandes shell** avec affichage en temps réel
- **Inférence directe** avec les modèles d'IA locaux
- **Mode interactif** pour les sessions persistantes (SSH, etc.)
- **Historique des commandes** avec navigation facile
- **Exploration de fichiers intégrée** avec navigation visuelle
- **Copie intelligente** du contenu du terminal
- **Raccourcis clavier** pour une utilisation efficace

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

## 🖼️ Captures d'écran

<p align="center">
  <img src="static/img/console.png" alt="Console Interactive" width="400" style="margin-right: 10px;">
  <img src="static/img/models.png" alt="Gestionnaire de Modèles" width="400">
</p>

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

4. Créez les répertoires requis :
   ```bash
   mkdir -p templates static/img static/css static/js stats logs
   ```

5. Initialisez les fichiers de configuration :
   ```bash
   echo '[]' > stats/inference_stats.json
   echo '{"default_model": "llama3"}' > ollama_config.json
   ```

## 🏃‍♂️ Utilisation

1. Activez l'environnement virtuel si ce n'est pas déjà fait :
   ```bash
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

2. Lancez l'application :
   ```bash
   python app.py
   ```

3. Ouvrez votre navigateur et accédez à :
   ```
   http://localhost:5000
   ```

## 📊 Structure du Projet

```
assistant-ia-ollama/
├── app.py                  # Application Flask principale
├── run-inference.py        # Script d'inférence avec Ollama
├── manage-models.py        # Gestionnaire de modèles Ollama
├── setup-environment.sh    # Script d'installation de l'environnement
├── install-ollama.sh       # Script d'installation d'Ollama
├── requirements.txt        # Dépendances Python pour le projet
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

## 📝 Améliorations v2.0

Cette version 2.0 apporte de nombreuses améliorations par rapport à la v1.0 :

- **Architecture refactorisée** pour une meilleure maintenabilité
- **Code optimisé** avec gestion d'erreurs améliorée
- **Interface utilisateur modernisée** avec une meilleure ergonomie
- **Accessibilité WCAG** intégrée pour tous les utilisateurs
- **Mode sombre/clair** avec transitions fluides
- **Sécurité renforcée** contre les injections et vulnérabilités
- **Documentation complète** du code et des APIs
- **Tests unitaires** pour les fonctions critiques

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Si vous rencontrez des problèmes ou avez des questions, veuillez ouvrir un ticket dans la section "Issues" du dépôt GitHub.

---

Développé avec ❤️ pour la communauté de l'IA open-source
