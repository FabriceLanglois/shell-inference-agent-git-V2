#!/usr/bin/env python3

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import requests

OLLAMA_API_HOST = os.environ.get("OLLAMA_API_HOST", "localhost")
OLLAMA_API_PORT = os.environ.get("OLLAMA_API_PORT", "11434")
OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"

# Configuration des logs avec rotation des fichiers
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Créer le logger
logger = logging.getLogger("models")
logger.setLevel(logging.INFO)

# Handler pour les fichiers avec rotation (5 fichiers de 2MB max)
file_handler = RotatingFileHandler(
    os.path.join(log_directory, "models.log"),
    maxBytes=2*1024*1024,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Ajout des handlers au logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Configuration
#OLLAMA_API_HOST = os.environ.get("OLLAMA_API_HOST", "localhost")
#OLLAMA_API_PORT = os.environ.get("OLLAMA_API_PORT", "11434")
#OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")

class OllamaService:
    """
    Classe pour interagir avec le service Ollama
    """
    
    @staticmethod
    def check_ollama_running():
        """Vérifie si Ollama est en cours d'exécution"""
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'Ollama: {e}")
            return False
    
    @staticmethod
    def start_ollama_service():
        """Démarre le service Ollama"""
        logger.info("Tentative de démarrage du service Ollama...")
        try:
            # Démarrer Ollama en arrière-plan
            subprocess.Popen(
                ["ollama", "serve"], 
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Attendre que le service soit prêt
            for _ in range(5):  # Attendre jusqu'à 5 secondes
                if OllamaService.check_ollama_running():
                    logger.info("Service Ollama démarré!")
                    return True
                time.sleep(1)
            
            logger.error("Le service Ollama n'a pas pu démarrer dans le temps imparti.")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du démarrage d'Ollama: {e}")
            return False
    
    @staticmethod
    def ensure_ollama_running():
        """S'assure qu'Ollama est en cours d'exécution, le démarre si nécessaire"""
        if OllamaService.check_ollama_running():
            return True
        
        # Tentative de démarrage
        return OllamaService.start_ollama_service()
    
    @staticmethod
    def get_models():
        """Récupère la liste des modèles disponibles"""
        if not OllamaService.ensure_ollama_running():
            logger.error("Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return []
            
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=5)
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Erreur lors de la récupération des modèles: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception lors de la récupération des modèles: {e}")
            return []
    
    @staticmethod
    def check_if_model_exists(model_name):
        """Vérifie si un modèle spécifique existe localement"""
        models = OllamaService.get_models()
        return any(model.get("name") == model_name for model in models)
    
    @staticmethod
    def pull_model(model_name, show_progress=True):
        """Télécharge un modèle depuis la bibliothèque Ollama"""
        if not OllamaService.ensure_ollama_running():
            logger.error("Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return False
            
        logger.info(f"Téléchargement du modèle '{model_name}'...")
        
        try:
            url = f"{OLLAMA_API_BASE}/pull"
            headers = {"Content-Type": "application/json"}
            data = {"name": model_name}
            
            # Option pour stream=True pour suivre la progression
            response = requests.post(url, headers=headers, json=data, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors du téléchargement du modèle: {response.status_code}")
                logger.error(response.text)
                return False
            
            # Suivre la progression du téléchargement
            for line in response.iter_lines():
                if line:
                    update = json.loads(line)
                    if show_progress and "status" in update:
                        if "digest" in update:
                            print(f"Téléchargement: {update.get('status', '')}")
                        else:
                            print(f"{update.get('status', '')}")
            
            logger.info(f"Modèle '{model_name}' téléchargé avec succès!")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du modèle: {e}")
            return False
    
    @staticmethod
    def delete_model(model_name):
        """Supprime un modèle local"""
        if not OllamaService.ensure_ollama_running():
            logger.error("Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return False
            
        logger.info(f"Suppression du modèle '{model_name}'...")
        
        try:
            url = f"{OLLAMA_API_BASE}/delete"
            headers = {"Content-Type": "application/json"}
            data = {"name": model_name}
            
            response = requests.delete(url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"Erreur lors de la suppression du modèle: {response.status_code}")
                logger.error(response.text)
                return False
            
            logger.info(f"Modèle '{model_name}' supprimé avec succès!")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du modèle: {e}")
            return False

class ConfigManager:
    """
    Classe pour gérer la configuration de l'application
    """
    
    @staticmethod
    def get_config():
        """Récupère la configuration depuis le fichier JSON"""
        if not os.path.exists(CONFIG_FILE):
            return {"default_model": "llama3"}
            
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la configuration: {e}")
            return {"default_model": "llama3"}
    
    @staticmethod
    def save_config(config_data):
        """Enregistre la configuration dans le fichier JSON"""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la configuration: {e}")
            return False
    
    @staticmethod
    def get_current_model():
        """Récupère le modèle actuel utilisé par l'application"""
        config = ConfigManager.get_config()
        default_model = config.get("default_model", "llama3")
        
        # Si le modèle configuré est "none", retourner une valeur explicite
        if default_model == "none":
            return "aucun_modele_disponible"
            
        # Vérifier si le modèle existe localement
        if OllamaService.check_if_model_exists(default_model):
            return default_model
            
        # Si le modèle par défaut n'existe pas, essayer de trouver un autre modèle
        models = OllamaService.get_models()
        if models:
            # Mettre à jour la configuration avec le premier modèle disponible
            new_default = models[0].get("name")
            config["default_model"] = new_default
            ConfigManager.save_config(config)
            logger.info(f"Modèle par défaut mis à jour vers '{new_default}'")
            return new_default
            
        return "aucun_modele_disponible"
    
    @staticmethod
    def set_default_model(model_name):
        """Définit le modèle par défaut pour l'application"""
        try:
            # Vérifier si le modèle existe localement
            if not OllamaService.check_if_model_exists(model_name):
                logger.error(f"Erreur: Le modèle '{model_name}' n'existe pas localement.")
                return False
            
            # Mettre à jour la configuration
            config = ConfigManager.get_config()
            config["default_model"] = model_name
            
            if ConfigManager.save_config(config):
                logger.info(f"Modèle '{model_name}' défini comme modèle par défaut.")
                return True
            else:
                logger.error(f"Erreur lors de l'enregistrement de la configuration.")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la définition du modèle par défaut: {e}")
            return False

# Commandes

def list_models(json_output=False):
    """Liste les modèles disponibles localement"""
    if not OllamaService.ensure_ollama_running():
        if json_output:
            return json.dumps({
                "error": "Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.",
                "models": []
            })
        else:
            logger.error("Erreur: Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return 1
    
    try:
        models = OllamaService.get_models()
        default_model = ConfigManager.get_current_model()
        
        if json_output:
            return json.dumps({
                "models": models,
                "default": default_model
            })
        
        if not models:
            print("Aucun modèle n'est actuellement disponible.")
            print("Utilisez la commande 'pull' pour télécharger un modèle.")
            return 0
        
        print("\n======= Modèles disponibles =======")
        print(f"{'Nom':<20} {'Taille':<10} {'Modifié le':<20}")
        print("-" * 50)
        
        for model in models:
            name = model.get("name", "Inconnu")
            size = model.get("size", 0) // (1024 * 1024)  # Convertir en MB
            modified = model.get("modified", "Inconnu")
            default_mark = " (défaut)" if name == default_model else ""
            print(f"{name:<20} {size:>6} MB  {modified:<20}{default_mark}")
        
        print("\nPour utiliser un modèle spécifique avec run-inference.py:")
        print("python run-inference.py --model nom_du_modele \"Votre prompt ici\"")
        
        return 0
    except Exception as e:
        error_msg = f"Erreur: {e}"
        if json_output:
            return json.dumps({"error": error_msg, "models": []})
        else:
            logger.error(error_msg)
            return 1

def get_current_model_info(json_output=False):
    """Obtient les informations sur le modèle actuel"""
    current_model = ConfigManager.get_current_model()
    
    if json_output:
        return json.dumps({
            "current": current_model,
            "isDefault": True
        })
    
    print(f"Modèle actuel: {current_model}")
    return 0

def pull_model(model_name):
    """Télécharge un modèle depuis la bibliothèque Ollama"""
    if not model_name:
        logger.error("Erreur: Nom de modèle non fourni")
        return 1
        
    # Vérifier que le nom du modèle ne contient pas de caractères dangereux
    if not all(c.isalnum() or c in ':-_.' for c in model_name):
        logger.error(f"Erreur: Nom de modèle invalide: {model_name}")
        return 1
    
    success = OllamaService.pull_model(model_name)
    
    if success:
        # Si c'est le premier modèle ou s'il n'y a pas de modèle par défaut, le définir comme tel
        current_model = ConfigManager.get_current_model()
        if current_model == "aucun_modele_disponible":
            ConfigManager.set_default_model(model_name)
            logger.info(f"Le modèle '{model_name}' a été défini comme modèle par défaut.")
        
        return 0
    else:
        return 1

def delete_model(model_name):
    """Supprime un modèle local"""
    if not model_name:
        logger.error("Erreur: Nom de modèle non fourni")
        return 1
    
    # Vérifier que le nom du modèle ne contient pas de caractères dangereux
    if not all(c.isalnum() or c in ':-_.' for c in model_name):
        logger.error(f"Erreur: Nom de modèle invalide: {model_name}")
        return 1
    
    current_model = ConfigManager.get_current_model()
    
    # Supprimer le modèle
    success = OllamaService.delete_model(model_name)
    
    if success:
        # Si on a supprimé le modèle par défaut, mettre à jour la configuration
        if model_name == current_model:
            # Trouver un autre modèle à utiliser comme défaut
            models = OllamaService.get_models()
            if models:
                # Utiliser le premier modèle disponible
                new_default = models[0].get("name")
                ConfigManager.set_default_model(new_default)
                logger.info(f"Le modèle par défaut a été mis à jour vers '{new_default}'.")
            else:
                # Aucun modèle disponible, définir à "none"
                config = ConfigManager.get_config()
                config["default_model"] = "none"
                ConfigManager.save_config(config)
                logger.info("Aucun modèle disponible. Le modèle par défaut a été défini à 'none'.")
        
        return 0
    else:
        return 1

def set_default_model(model_name):
    """Définit le modèle par défaut pour l'application"""
    if not model_name:
        logger.error("Erreur: Nom de modèle non fourni")
        return 1
    
    # Vérifier que le nom du modèle ne contient pas de caractères dangereux
    if not all(c.isalnum() or c in ':-_.' for c in model_name):
        logger.error(f"Erreur: Nom de modèle invalide: {model_name}")
        return 1
    
    success = ConfigManager.set_default_model(model_name)
    return 0 if success else 1

def show_models_info():
    """Affiche des informations sur les modèles recommandés"""
    print("\n======= Modèles Ollama recommandés =======")
    print(f"{'Nom':<15} {'Taille':<10} {'Description':<50}")
    print("-" * 75)
    
    models_info = [
        ("llama3", "4.7 GB", "Le modèle le plus récent de Meta, performant et équilibré"),
        ("mistral", "4.1 GB", "Excellent modèle open-source, très performant"),
        ("phi3:mini", "1.7 GB", "Petit modèle de Microsoft, rapide et efficace"),
        ("gemma:2b", "1.4 GB", "Petit modèle de Google, idéal pour les ressources limitées"),
        ("codegemma", "4.9 GB", "Spécialisé pour le code et la programmation"),
        ("dolphin-phi3", "4.8 GB", "Version améliorée de Phi3 avec des capacités d'assistant"),
        ("neural-chat", "4.1 GB", "Optimisé pour les conversations d'assistant"),
        ("llama3:8b", "4.7 GB", "Version 8B de Llama3, plus légère"),
        ("llava", "4.8 GB", "Modèle multimodal capable de comprendre les images"),
        ("gemma:7b", "4.2 GB", "Version complète de Gemma par Google")
    ]
    
    for name, size, desc in models_info:
        print(f"{name:<15} {size:<10} {desc:<50}")
    
    print("\nPour télécharger un modèle:")
    print("python manage-models.py pull nom_du_modele")
    
    return 0

def check_ollama_ping(json_output=False):
    """Vérifie si Ollama est en cours d'exécution et renvoie un statut"""
    is_running = OllamaService.check_ollama_running()
    
    if json_output:
        return json.dumps({
            "status": "ok" if is_running else "error",
            "message": "Ollama est en cours d'exécution" if is_running else "Ollama n'est pas disponible"
        })
    
    if is_running:
        print("Ollama est en cours d'exécution.")
        return 0
    else:
        print("Erreur: Ollama n'est pas disponible.")
        return 1

def main():
    """Fonction principale"""
    # Créer le parseur d'arguments
    parser = argparse.ArgumentParser(
        description="Gestionnaire de modèles Ollama",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Ajouter des options globales
    parser.add_argument("--host", help=f"Hôte de l'API Ollama (défaut: {OLLAMA_API_HOST})")
    parser.add_argument("--port", help=f"Port de l'API Ollama (défaut: {OLLAMA_API_PORT})")
    
    # Après avoir traité les arguments
    args = parser.parse_args()
    
    # Mise à jour de la configuration globale
    global OLLAMA_API_HOST, OLLAMA_API_PORT, OLLAMA_API_BASE
    if args.host:
        OLLAMA_API_HOST = args.host
    if args.port:
        OLLAMA_API_PORT = args.port
    OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"

    # Ajouter des sous-commandes
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")
    
    # Commande list
    list_parser = subparsers.add_parser("list", help="Lister les modèles disponibles")
    list_parser.add_argument("--json", action="store_true", help="Sortie au format JSON")
    
    # Commande pull
    pull_parser = subparsers.add_parser("pull", help="Télécharger un modèle")
    pull_parser.add_argument("model", help="Nom du modèle à télécharger")
    
    # Commande delete
    delete_parser = subparsers.add_parser("delete", help="Supprimer un modèle")
    delete_parser.add_argument("model", help="Nom du modèle à supprimer")
    
    # Commande info
    info_parser = subparsers.add_parser("info", help="Informations sur les modèles recommandés")
    
    # Commande set-default
    default_parser = subparsers.add_parser("set-default", help="Définir le modèle par défaut")
    default_parser.add_argument("model", help="Nom du modèle à définir comme défaut")
    
    # Commande current
    current_parser = subparsers.add_parser("current", help="Obtenir le modèle actuel")
    current_parser.add_argument("--json", action="store_true", help="Sortie au format JSON")
    
    # Commande ping
    ping_parser = subparsers.add_parser("ping", help="Vérifier si Ollama est en cours d'exécution")
    ping_parser.add_argument("--json", action="store_true", help="Sortie au format JSON")
    
    # Options globales
    parser.add_argument("--host", help=f"Hôte de l'API Ollama (défaut: {OLLAMA_API_HOST})")
    parser.add_argument("--port", help=f"Port de l'API Ollama (défaut: {OLLAMA_API_PORT})")
    
    args = parser.parse_args()
    
    # Mise à jour de la configuration globale
    global OLLAMA_API_HOST, OLLAMA_API_PORT, OLLAMA_API_BASE
    if args.host:
        OLLAMA_API_HOST = args.host
    if args.port:
        OLLAMA_API_PORT = args.port
    OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"
    
    # Traiter les commandes
    if args.command == "list":
        result = list_models(json_output=args.json)
        if args.json and isinstance(result, str):
            print(result)
        return result
    elif args.command == "pull":
        return pull_model(args.model)
    elif args.command == "delete":
        return delete_model(args.model)
    elif args.command == "info":
        return show_models_info()
    elif args.command == "set-default":
        return set_default_model(args.model)
    elif args.command == "current":
        result = get_current_model_info(json_output=args.json)
        if args.json and isinstance(result, str):
            print(result)
        return result
    elif args.command == "ping":
        result = check_ollama_ping(json_output=args.json)
        if args.json and isinstance(result, str):
            print(result)
        return result
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
