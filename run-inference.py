import requests
import json
import sys
import time
import torch
import argparse
import os
import logging
import subprocess

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inference.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes pour la connexion à Ollama
OLLAMA_API_BASE = "http://localhost:11434/api"
REQUEST_TIMEOUT = 10  # Augmenté de 2 à 10 secondes
MAX_RETRY_ATTEMPTS = 5  # Augmenté de 3 à 5 tentatives

def ensure_ollama_running():
    """S'assure qu'Ollama est en cours d'exécution avec une logique améliorée"""
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return True
            
            logger.info(f"Tentative {attempt+1}/{MAX_RETRY_ATTEMPTS}: Ollama répond mais avec le code {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.info(f"Tentative {attempt+1}/{MAX_RETRY_ATTEMPTS}: Ollama ne répond pas, essai de démarrage...")
            try:
                # Vérifier si ollama est déjà en cours d'exécution
                try:
                    result = subprocess.run(["pgrep", "-f", "ollama serve"], 
                                          shell=True, 
                                          capture_output=True, 
                                          text=True)
                    if result.stdout.strip():
                        logger.info("Un processus Ollama semble déjà en cours d'exécution mais ne répond pas.")
                except Exception:
                    pass  # Ignorer les erreurs de cette vérification
                
                # Utilisation de popen pour éviter de bloquer
                subprocess.Popen(
                    ["ollama", "serve"], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                # Attendre que le service démarre
                logger.info("Service Ollama démarré, attente de 5 secondes...")
                time.sleep(5)  # Attendre 5 secondes au lieu de 3
            except Exception as e:
                logger.error(f"Erreur lors du démarrage d'Ollama: {e}")
        except requests.exceptions.Timeout:
            logger.info(f"Tentative {attempt+1}/{MAX_RETRY_ATTEMPTS}: Timeout lors de la connexion à Ollama")
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
        
        # Si ce n'est pas la dernière tentative, attendre avant de réessayer
        if attempt < MAX_RETRY_ATTEMPTS - 1:
            wait_time = 2 * (attempt + 1)  # Attente exponentielle
            logger.info(f"Attente de {wait_time} secondes avant la prochaine tentative...")
            time.sleep(wait_time)
    
    # Toutes les tentatives ont échoué
    logger.error("ERREUR: Impossible de démarrer ou de se connecter à Ollama après plusieurs tentatives")
    logger.error("Assurez-vous qu'Ollama est installé et peut être démarré manuellement avec 'ollama serve'")
    
    # Vérifier si ollama est installé
    try:
        which_result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if which_result.returncode != 0:
            logger.error("Ollama n'est pas installé ou n'est pas dans le PATH")
            logger.error("Installez Ollama via https://ollama.com/download")
        else:
            logger.info(f"Ollama est installé à: {which_result.stdout.strip()}")
            logger.error("Le service ne répond pas malgré l'installation")
    except Exception:
        logger.error("Impossible de vérifier si Ollama est installé")
    
    return False

def check_available_models():
    """Vérifie les modèles disponibles et suggère des actions si aucun n'est trouvé"""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if not models:
                logger.warning("Aucun modèle disponible localement.")
                print("Aucun modèle n'est installé. Vous pouvez en télécharger un avec:")
                print("ollama pull llama3")
                return False
            return True
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des modèles: {e}")
        return False

def run_inference(prompt, model="llama3", max_length=500, temperature=0.7):
    """
    Exécute une inférence en utilisant Ollama avec gestion améliorée des erreurs
    """
    if not ensure_ollama_running():
        error_msg = "Erreur: Ollama n'est pas disponible. Vérifiez l'installation et le service."
        logger.error(error_msg)
        print("\033[1;31m" + error_msg + "\033[0m")  # Rouge
        print("Pour démarrer Ollama manuellement, exécutez: ollama serve")
        return error_msg
    
    # Vérifier si des modèles sont disponibles
    if not check_available_models():
        return "Erreur: Aucun modèle n'est disponible. Téléchargez-en un avec 'ollama pull llama3'."
    
    print(f"Exécution de l'inférence avec le prompt: {prompt}")
    print(f"\033[1;36mModèle sélectionné: {model}\033[0m")
    
    # Vérifier si CUDA est disponible (pour affichage seulement)
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        print(f"GPU détecté: {gpu_name}")
        print(f"CUDA version: {torch.version.cuda}")
    else:
        device = "cpu"
        print("Aucun GPU détecté, utilisation du CPU")
    
    # Configuration de la requête à Ollama
    url = f"{OLLAMA_API_BASE}/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "max_tokens": int(max_length),
            "top_p": 0.9,
            "seed": 42  # Pour des résultats plus cohérents
        }
    }
    
    print(f"Chargement du modèle {model}...")
    start_time = time.time()
    
    # Tentatives de connexion avec retry
    for attempt in range(3):
        try:
            # Mode non-streaming (plus simple pour l'intégration)
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT * 2)
            response.raise_for_status()  # Gérer les erreurs HTTP
            result = response.json()
            
            # Extraire le texte généré
            generated_text = result.get("response", "")
            
            inference_time = time.time() - start_time
            print(f"\nInférence terminée en {inference_time:.2f} secondes")
            
            if device == "cuda":
                print(f"Utilisation mémoire GPU: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            
            print("\nTexte généré:")
            print(generated_text)
            
            return generated_text
        
        except requests.exceptions.ConnectionError:
            if attempt < 2:  # Si ce n'est pas la dernière tentative
                wait_time = 2 * (attempt + 1)
                print(f"Erreur de connexion, nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                error_text = "Erreur: Impossible de se connecter à Ollama. Vérifiez qu'Ollama est bien lancé sur http://localhost:11434"
                logger.error(error_text)
                print("\033[1;31m" + error_text + "\033[0m")  # Rouge
                print("Pour démarrer Ollama, exécutez: ollama serve")
                return error_text
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout lors de la requête (tentative {attempt+1}/3)")
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"La requête prend plus de temps que prévu, nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                error_text = "Erreur: Timeout lors de l'inférence. Le modèle pourrait être trop grand pour votre machine."
                logger.error(error_text)
                print("\033[1;31m" + error_text + "\033[0m")  # Rouge
                return error_text
        
        except Exception as e:
            error_text = f"Erreur lors de l'inférence: {str(e)}"
            logger.error(error_text)
            print("\033[1;31m" + error_text + "\033[0m")  # Rouge
            return error_text

def run_inference_stream(prompt, model="llama3", max_length=500, temperature=0.7):
    """
    Version alternative utilisant le streaming pour afficher les tokens en temps réel
    avec gestion améliorée des erreurs
    """
    if not ensure_ollama_running():
        error_msg = "Erreur: Ollama n'est pas disponible. Vérifiez l'installation et le service."
        logger.error(error_msg)
        print("\033[1;31m" + error_msg + "\033[0m")  # Rouge
        print("Pour démarrer Ollama manuellement, exécutez: ollama serve")
        return error_msg
    
    # Vérifier si des modèles sont disponibles
    if not check_available_models():
        return "Erreur: Aucun modèle n'est disponible. Téléchargez-en un avec 'ollama pull llama3'."
    
    print(f"Exécution de l'inférence (streaming) avec le prompt: {prompt}")
    print(f"\033[1;36mModèle sélectionné: {model}\033[0m")
    
    # Configuration similaire mais avec stream=True
    url = f"{OLLAMA_API_BASE}/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": float(temperature),
            "max_tokens": int(max_length),
            "top_p": 0.9,
            "seed": 42  # Pour des résultats plus cohérents
        }
    }
    
    print(f"Chargement du modèle {model}...")
    start_time = time.time()
    generated_text = ""
    
    # Tentatives de connexion avec retry
    for attempt in range(3):
        try:
            # Mode streaming
            response = requests.post(url, headers=headers, data=json.dumps(data), stream=True, timeout=REQUEST_TIMEOUT * 2)
            response.raise_for_status()
            
            token_count = 0
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    generated_text += token
                    
                    # Mise à jour de la progression
                    token_count += 1
                    if token_count % 5 == 0:  # Afficher tous les 5 tokens pour ne pas surcharger
                        print(f"Génération du token {token_count}...", end="\r")
            
            inference_time = time.time() - start_time
            print(f"\nInférence terminée en {inference_time:.2f} secondes")
            
            # Vérifier si CUDA est disponible pour afficher l'utilisation mémoire
            if torch.cuda.is_available():
                print(f"Utilisation mémoire GPU: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            
            print("\nTexte généré:")
            print(generated_text)
            
            return generated_text
        
        except requests.exceptions.ConnectionError:
            if attempt < 2:  # Si ce n'est pas la dernière tentative
                wait_time = 2 * (attempt + 1)
                print(f"Erreur de connexion, nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                error_text = "Erreur: Impossible de se connecter à Ollama. Vérifiez qu'Ollama est bien lancé sur http://localhost:11434"
                logger.error(error_text)
                print("\033[1;31m" + error_text + "\033[0m")  # Rouge
                print("Pour démarrer Ollama, exécutez: ollama serve")
                return error_text
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout lors de la requête (tentative {attempt+1}/3)")
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"La requête prend plus de temps que prévu, nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                error_text = "Erreur: Timeout lors de l'inférence. Le modèle pourrait être trop grand pour votre machine."
                logger.error(error_text)
                print("\033[1;31m" + error_text + "\033[0m")  # Rouge
                return error_text
        
        except Exception as e:
            error_text = f"Erreur lors de l'inférence: {str(e)}"
            logger.error(error_text)
            print("\033[1;31m" + error_text + "\033[0m")  # Rouge
            return error_text

def get_default_model():
    """Récupère le modèle par défaut depuis la configuration avec vérification améliorée"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
    default_model = "llama3"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                configured_model = config.get("default_model", default_model)
                
                # Vérifier si le modèle est valide (n'est pas "aucun_modele_disponible")
                if configured_model and configured_model != "aucun_modele_disponible":
                    return configured_model
        except json.JSONDecodeError:
            logger.error(f"Erreur: Fichier de configuration corrompu: {config_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du modèle par défaut: {e}")
    
    # Vérifier s'il y a des modèles disponibles
    try:
        if ensure_ollama_running():
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if models:
                    # Utiliser le premier modèle disponible
                    return models[0].get("name")
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'un modèle disponible: {e}")
    
    return default_model

def verify_ollama_installation():
    """Vérifie l'installation d'Ollama et affiche des informations de diagnostic"""
    print("\n=== Vérification de l'installation d'Ollama ===\n")
    
    # Vérifier si ollama est installé
    try:
        which_result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if which_result.returncode == 0:
            ollama_path = which_result.stdout.strip()
            print(f"✅ Ollama est installé à: {ollama_path}")
            
            # Vérifier la version
            version_result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if version_result.returncode == 0:
                print(f"✅ Version d'Ollama: {version_result.stdout.strip()}")
            else:
                print("❌ Impossible d'obtenir la version d'Ollama")
        else:
            print("❌ Ollama n'est pas installé ou n'est pas dans le PATH")
            print("   Installez Ollama via https://ollama.com/download")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de l'installation: {e}")
        return False
    
    # Vérifier si le service est en cours d'exécution
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            print("✅ Service Ollama: En cours d'exécution")
            
            # Vérifier les modèles disponibles
            models = response.json().get("models", [])
            if models:
                print(f"✅ Modèles disponibles: {len(models)}")
                for model in models:
                    name = model.get("name", "Inconnu")
                    size = model.get("size", 0) // (1024 * 1024)  # Convertir en MB
                    print(f"   - {name} ({size} MB)")
            else:
                print("⚠️ Aucun modèle disponible")
                print("   Téléchargez un modèle avec: ollama pull llama3")
        else:
            print(f"❌ Service Ollama: Répond mais avec le code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Service Ollama: Non démarré ou inaccessible")
        print("   Démarrez le service avec: ollama serve")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du service: {e}")
    
    # Vérifier la configuration
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                default_model = config.get("default_model", "non défini")
                print(f"✅ Configuration: Modèle par défaut = {default_model}")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture de la configuration: {e}")
    else:
        print("⚠️ Fichier de configuration non trouvé")
    
    print("\n=== Fin de la vérification ===\n")
    return True

def main():
    # Configurer l'analyse des arguments
    parser = argparse.ArgumentParser(description="Exécuter une inférence avec un modèle Ollama")
    parser.add_argument("--model", help="Nom du modèle à utiliser")
    parser.add_argument("--no-stream", action="store_true", help="Désactiver le mode streaming")
    parser.add_argument("--temperature", type=float, default=0.7, help="Température pour la génération (0-1)")
    parser.add_argument("--max-tokens", type=int, default=500, help="Nombre maximum de tokens à générer")
    parser.add_argument("--verify", action="store_true", help="Vérifier l'installation d'Ollama")
    parser.add_argument("prompt", nargs="*", help="Prompt à envoyer au modèle")
    
    args = parser.parse_args()
    
    # Exécuter la vérification si demandé
    if args.verify:
        verify_ollama_installation()
        return
    
    # Vérifier si un prompt a été fourni
    if not args.prompt:
        parser.print_help()
        return
    
    # Si aucun modèle n'est spécifié, utiliser le modèle par défaut
    model = args.model if args.model else get_default_model()
    prompt = " ".join(args.prompt)
    use_streaming = not args.no_stream
    temperature = args.temperature
    max_tokens = args.max_tokens
    
    # Afficher clairement le modèle sélectionné
    print(f"\033[1;36mModèle sélectionné: {model}\033[0m")  # En cyan pour le mettre en évidence
    
    # Choisir la méthode d'inférence en fonction du paramètre
    if use_streaming:
        run_inference_stream(prompt, model, max_tokens, temperature)
    else:
        run_inference(prompt, model, max_tokens, temperature)

if __name__ == "__main__":
    main()