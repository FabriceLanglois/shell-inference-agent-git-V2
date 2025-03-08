#!/usr/bin/env python3
import requests
import json
import sys
import os
import subprocess
import argparse
import logging
import time

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("models.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes globales
OLLAMA_API_BASE = "http://localhost:11434/api"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
REQUEST_TIMEOUT = 5  # Augmenté de 2 à 5 secondes
MAX_RETRIES = 3  # Nombre de tentatives pour les opérations critiques

def check_ollama_running(retries=1):
    """Vérifie si Ollama est en cours d'exécution avec support de plusieurs tentatives"""
    for attempt in range(retries):
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return True
            logger.warning(f"Tentative {attempt+1}/{retries}: Ollama répond mais avec le code {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Tentative {attempt+1}/{retries}: Impossible de se connecter à Ollama")
        except requests.exceptions.Timeout:
            logger.warning(f"Tentative {attempt+1}/{retries}: Timeout lors de la connexion à Ollama")
        except Exception as e:
            logger.warning(f"Tentative {attempt+1}/{retries}: Erreur lors de la connexion à Ollama: {e}")
        
        if attempt < retries - 1:
            time.sleep(1)  # Attendre avant de réessayer
    
    return False

def start_ollama_service():
    """Démarre le service Ollama avec amélioration de la détection de succès"""
    logger.info("Tentative de démarrage du service Ollama...")
    try:
        # Vérifier si le processus ollama est déjà en cours d'exécution
        try:
            result = subprocess.run(["pgrep", "-f", "ollama serve"], 
                                   shell=True, 
                                   capture_output=True, 
                                   text=True)
            if result.stdout.strip():
                logger.info("Un processus Ollama semble déjà en cours d'exécution.")
                # Attendre un peu au cas où le service est en cours de démarrage
                time.sleep(2)
                return check_ollama_running(retries=3)
        except Exception:
            pass  # Ignorer les erreurs de cette vérification
        
        # Démarrer Ollama en arrière-plan
        subprocess.Popen(["ollama", "serve"], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)
        
        # Attendre que le service soit prêt avec un délai plus long (10 secondes)
        for i in range(10):
            logger.info(f"Attente du démarrage d'Ollama... ({i+1}/10)")
            if check_ollama_running():
                logger.info("Service Ollama démarré avec succès!")
                return True
            time.sleep(1)
        
        logger.error("Le service Ollama n'a pas pu démarrer dans le temps imparti.")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du démarrage d'Ollama: {e}")
        return False

def get_local_models():
    """Récupère la liste des modèles disponibles localement"""
    if not check_ollama_running():
        if not start_ollama_service():
            logger.error("Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return []

    try:
        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json().get("models", [])
        else:
            logger.error(f"Erreur lors de la récupération des modèles: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Erreur de connexion à Ollama: {e}")
        return []

def get_current_model():
    """Récupère le modèle actuellement configuré comme modèle par défaut"""
    try:
        # Récupérer la liste des modèles disponibles
        local_models = get_local_models()
        
        # Si aucun modèle n'est disponible, retourner un message spécial
        if not local_models:
            logger.warning("Aucun modèle disponible localement.")
            return "aucun_modele_disponible"
        
        # Vérifier si un modèle par défaut est configuré
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    default_model = config.get("default_model")
                    
                    # Vérifier si le modèle par défaut est toujours disponible
                    if default_model and any(model["name"] == default_model for model in local_models):
                        return default_model
            except json.JSONDecodeError:
                logger.error(f"Fichier de configuration corrompu: {CONFIG_PATH}")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de la configuration: {e}")
        
        # Si le modèle par défaut n'est pas disponible, utiliser le premier modèle
        first_model = local_models[0]["name"]
        logger.info(f"Aucun modèle par défaut configuré ou disponible. Utilisation de {first_model}")
        
        # Mettre à jour la configuration avec ce modèle
        set_default_model(first_model)
        
        return first_model
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du modèle actuel: {e}")
        return "aucun_modele_disponible"

def set_default_model(model_name):
    """Définit le modèle par défaut pour l'application"""
    try:
        # Vérifier si le modèle existe localement
        local_models = get_local_models()
        if not local_models:
            logger.error("Aucun modèle disponible localement.")
            return False
            
        model_exists = any(model["name"] == model_name for model in local_models)
        if not model_exists:
            logger.error(f"Erreur: Le modèle '{model_name}' n'existe pas localement.")
            return False
        
        # Lire la configuration existante ou créer une nouvelle
        config = {}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Fichier de configuration corrompu. Création d'un nouveau.")
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture de la configuration: {e}")
        
        # Mettre à jour le modèle par défaut
        config["default_model"] = model_name
        
        # Enregistrer la configuration
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Modèle '{model_name}' défini comme modèle par défaut.")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture de la configuration: {e}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la définition du modèle par défaut: {e}")
        return False

def get_current_model_info(json_output=False):
    """Obtient les informations sur le modèle actuel"""
    current_model = get_current_model()
    
    if json_output:
        return json.dumps({
            "current": current_model,
            "isDefault": True  # Par défaut, le modèle actuel est le modèle par défaut
        })
    
    print(f"Modèle actuel: {current_model}")
    return current_model

def pull_model(model_name):
    """Télécharge un modèle depuis la bibliothèque Ollama avec gestion améliorée des erreurs"""
    if not check_ollama_running(retries=3):
        if not start_ollama_service():
            error_msg = "Erreur: Ollama n'est pas en cours d'exécution et n'a pas pu être démarré."
            logger.error(error_msg)
            print(error_msg)
            print("Vérifiez que le service Ollama est correctement installé.")
            print("Vous pouvez l'installer avec la commande: curl -fsSL https://ollama.com/install.sh | sh")
            return False

    logger.info(f"Téléchargement du modèle '{model_name}'...")
    print(f"Démarrage du téléchargement du modèle '{model_name}'...")
    print("Cette opération peut prendre plusieurs minutes selon la taille du modèle et votre connexion.")
    
    try:
        # Utiliser l'API pour le pull
        url = f"{OLLAMA_API_BASE}/pull"
        headers = {"Content-Type": "application/json"}
        data = {"name": model_name}
        
        # Utiliser une session avec retry
        session = requests.Session()
        
        response = session.post(url, headers=headers, data=json.dumps(data), stream=True, timeout=10)
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    update = json.loads(line)
                    if "status" in update:
                        if "digest" in update:
                            print(f"Téléchargement: {update['status']}")
                        else:
                            print(f"{update['status']}")
            
            logger.info(f"Modèle '{model_name}' téléchargé avec succès!")
            print(f"\nModèle '{model_name}' téléchargé avec succès!")
            
            # Définir comme modèle par défaut s'il n'y en a pas d'autre
            current = get_current_model()
            if current == "aucun_modele_disponible":
                set_default_model(model_name)
                logger.info(f"Le modèle '{model_name}' a été défini comme modèle par défaut.")
                print(f"Le modèle '{model_name}' a été défini comme modèle par défaut.")
            
            return True
        else:
            error_msg = f"Erreur lors du téléchargement du modèle: Code {response.status_code}"
            logger.error(error_msg)
            print(error_msg)
            print(response.text)
            return False
    except requests.exceptions.ConnectionError:
        error_msg = f"Erreur de connexion à Ollama. Vérifiez que le service est en cours d'exécution."
        logger.error(error_msg)
        print(error_msg)
        return False
    except requests.exceptions.Timeout:
        error_msg = f"Timeout lors du téléchargement du modèle. Le processus prend plus de temps que prévu."
        logger.error(error_msg)
        print(error_msg)
        print("Le téléchargement peut toujours être en cours en arrière-plan.")
        print("Vérifiez l'état du téléchargement avec la commande 'ollama list'.")
        return False
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement: {e}"
        logger.error(error_msg)
        print(error_msg)
        return False

def delete_model(model_name):
    """Supprime un modèle local avec vérification améliorée"""
    if not check_ollama_running(retries=3):
        if not start_ollama_service():
            logger.error("Erreur: Ollama n'est pas en cours d'exécution et n'a pas pu être démarré.")
            return False

    logger.info(f"Suppression du modèle '{model_name}'...")
    try:
        # Vérifier si le modèle existe
        local_models = get_local_models()
        model_exists = any(model["name"] == model_name for model in local_models)
        
        if not model_exists:
            logger.error(f"Erreur: Le modèle '{model_name}' n'existe pas.")
            return False
        
        url = f"{OLLAMA_API_BASE}/delete"
        headers = {"Content-Type": "application/json"}
        data = {"name": model_name}
        
        response = requests.delete(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            logger.info(f"Modèle '{model_name}' supprimé avec succès!")
            
            # Si on a supprimé le modèle par défaut, mettre à jour la configuration
            if model_name == get_current_model():
                # Trouver un autre modèle à utiliser comme défaut
                remaining_models = get_local_models()
                if remaining_models:
                    # Utiliser le premier modèle disponible
                    new_default = remaining_models[0].get("name")
                    set_default_model(new_default)
                    logger.info(f"Le modèle par défaut a été mis à jour vers '{new_default}'.")
            
            return True
        else:
            logger.error(f"Erreur lors de la suppression du modèle: {response.status_code}")
            if response.text:
                logger.error(f"Détails: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {e}")
        return False

def list_models(json_output=False):
    """Liste les modèles disponibles localement avec gestion améliorée des erreurs"""
    if not check_ollama_running(retries=3):
        if not start_ollama_service():
            error_msg = "Erreur: Ollama n'est pas en cours d'exécution et n'a pas pu être démarré."
            if json_output:
                return json.dumps({"error": error_msg, "models": []})
            else:
                logger.error(error_msg)
                print(error_msg)
                print("Vérifiez que le service Ollama est correctement installé et en cours d'exécution.")
                print("Vous pouvez démarrer Ollama manuellement avec la commande: ollama serve")
                return

    try:
        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            models = response.json().get("models", [])
            default_model = get_current_model()
            
            if json_output:
                return json.dumps({"models": models, "default": default_model})
            
            if not models:
                print("Aucun modèle n'est actuellement disponible.")
                print("Utilisez la commande 'pull' pour télécharger un modèle.")
                return
            
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
        else:
            error_msg = f"Erreur lors de la récupération des modèles: {response.status_code}"
            if json_output:
                return json.dumps({"error": error_msg})
            else:
                logger.error(error_msg)
                print(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "Erreur: Impossible de se connecter à Ollama. Vérifiez que le service est en cours d'exécution."
        if json_output:
            return json.dumps({"error": error_msg})
        else:
            logger.error(error_msg)
            print(error_msg)
    except Exception as e:
        error_msg = f"Erreur: {e}"
        if json_output:
            return json.dumps({"error": error_msg})
        else:
            logger.error(error_msg)
            print(error_msg)

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

# Ajouter cette fonction vers la ligne ~400 dans le fichier manage-models.py
def ping_ollama():
    """Vérifie si le service Ollama est actif et répond"""
    print_step("Vérification", "Connexion à Ollama")
    
    try:
        if check_ollama_running(retries=2):
            print_result(True, "Le service Ollama est en cours d'exécution et répond correctement")
            
            # Vérifier les modèles disponibles
            try:
                response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    if models:
                        print_result(True, f"{len(models)} modèle(s) disponible(s):")
                        for model in models:
                            name = model.get("name", "Inconnu")
                            print(f"      - {name}")
                    else:
                        print_result(False, "Aucun modèle n'est installé")
            except Exception as e:
                logger.error(f"Erreur lors de la vérification des modèles: {e}")
                
            return True
        else:
            print_result(False, "Le service Ollama n'est pas en cours d'exécution ou ne répond pas")
            print("Pour démarrer Ollama, exécutez: ollama serve")
            return False
    except Exception as e:
        print_result(False, f"Erreur lors de la vérification d'Ollama: {e}")
        return False

# Puis, modifier la fonction main() pour ajouter la commande ping
# Autour de la ligne ~480-500 dans le fichier manage-models.py
def main():
    # Ajout d'un parseur d'arguments pour les options JSON
    parser = argparse.ArgumentParser(description="Gestionnaire de modèles Ollama")
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
    
    # Commande verify
    verify_parser = subparsers.add_parser("verify", help="Vérifier l'installation d'Ollama")
    
    # Ajouter la commande ping (alias de verify)
    ping_parser = subparsers.add_parser("ping", help="Vérifier si Ollama répond")
    
    args = parser.parse_args()
    
    if args.command == "list":
        if args.json:
            result = list_models(json_output=True)
            if result:
                print(result)
        else:
            list_models()
    elif args.command == "pull":
        pull_model(args.model)
    elif args.command == "delete":
        delete_model(args.model)
    elif args.command == "info":
        show_models_info()
    elif args.command == "set-default":
        set_default_model(args.model)
    elif args.command == "current":
        if args.json:
            result = get_current_model_info(json_output=True)
            if result:
                print(result)
        else:
            get_current_model_info()
    elif args.command == "verify" or args.command == "ping":
        ping_ollama()
    else:
        parser.print_help()

def verify_ollama_installation():
    """Vérifie si Ollama est correctement installé"""
    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if result.returncode == 0:
            ollama_path = result.stdout.strip()
            print(f"Ollama est installé à: {ollama_path}")
            
            # Vérifier la version
            version_result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if version_result.returncode == 0:
                print(f"Version d'Ollama: {version_result.stdout.strip()}")
            
            # Vérifier si le service est en cours d'exécution
            if check_ollama_running():
                print("Service Ollama: En cours d'exécution")
                return True
            else:
                print("Service Ollama: Non démarré")
                print("Vous pouvez démarrer Ollama avec la commande: ollama serve")
                return False
        else:
            print("Ollama n'est pas installé ou n'est pas dans le PATH.")
            print("Vous pouvez l'installer avec la commande: curl -fsSL https://ollama.com/install.sh | sh")
            return False
    except Exception as e:
        print(f"Erreur lors de la vérification d'Ollama: {e}")
        return False

def main():
    # Ajout d'un parseur d'arguments pour les options JSON
    parser = argparse.ArgumentParser(description="Gestionnaire de modèles Ollama")
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
    
    # Commande verify
    verify_parser = subparsers.add_parser("verify", help="Vérifier l'installation d'Ollama")
    
    args = parser.parse_args()
    
    if args.command == "list":
        if args.json:
            result = list_models(json_output=True)
            if result:
                print(result)
        else:
            list_models()
    elif args.command == "pull":
        pull_model(args.model)
    elif args.command == "delete":
        delete_model(args.model)
    elif args.command == "info":
        show_models_info()
    elif args.command == "set-default":
        set_default_model(args.model)
    elif args.command == "current":
        if args.json:
            result = get_current_model_info(json_output=True)
            if result:
                print(result)
        else:
            get_current_model_info()
    elif args.command == "verify":
        verify_ollama_installation()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()