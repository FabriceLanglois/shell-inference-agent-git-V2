#!/usr/bin/env python3

import argparse
import json
import logging
import os
import signal
import sys
import time
from logging.handlers import RotatingFileHandler
import threading

import requests
import torch

# Configuration des logs avec rotation des fichiers
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Créer le logger
logger = logging.getLogger("inference")
logger.setLevel(logging.INFO)

# Handler pour les fichiers avec rotation (5 fichiers de 2MB max)
file_handler = RotatingFileHandler(
    os.path.join(log_directory, "inference.log"),
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
OLLAMA_API_HOST = os.environ.get("OLLAMA_API_HOST", "localhost")
OLLAMA_API_PORT = os.environ.get("OLLAMA_API_PORT", "11434")
OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"
CONFIG_FILE = "ollama_config.json"
TIMEOUT = 120  # 2 minutes par défaut

# Classe pour la gestion du timeout
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    """Gestionnaire pour le signal de timeout"""
    raise TimeoutError("L'inférence a dépassé le délai d'exécution")

class OllamaClient:
    """Client pour interagir avec l'API Ollama"""
    
    @staticmethod
    def ensure_ollama_running():
        """S'assure qu'Ollama est en cours d'exécution"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=2)
                if response.status_code == 200:
                    logger.debug("Ollama est en cours d'exécution")
                    return True
                
                logger.info(f"Tentative {attempt+1}/{max_attempts}: Ollama répond mais avec le code {response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.info(f"Tentative {attempt+1}/{max_attempts}: Ollama ne répond pas, essai de démarrage...")
                try:
                    # Utilisation de popen pour éviter de bloquer
                    import subprocess
                    subprocess.Popen(
                        ["ollama", "serve"], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    # Attendre que le service démarre
                    logger.info("Service Ollama démarré, attente de 3 secondes...")
                    time.sleep(3)  # Attendre 3 secondes
                except Exception as e:
                    logger.error(f"Erreur lors du démarrage d'Ollama: {e}")
        
        logger.error("ERREUR: Impossible de démarrer ou de se connecter à Ollama après plusieurs tentatives")
        logger.error("Assurez-vous qu'Ollama est installé et peut être démarré manuellement")
        return False
    
    @staticmethod
    def get_models():
        """Récupère la liste des modèles disponibles"""
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
    def run_inference(prompt, model, temperature=0.7, max_tokens=500, stream=False):
        """
        Exécute une inférence en utilisant l'API Ollama
        
        Args:
            prompt (str): Le prompt à envoyer au modèle
            model (str): Le nom du modèle à utiliser
            temperature (float): Température pour la génération (0-1)
            max_tokens (int): Nombre maximum de tokens à générer
            stream (bool): Si True, utilise le mode streaming

        Returns:
            str: Le texte généré ou un message d'erreur
        """
        if not OllamaClient.ensure_ollama_running():
            error_msg = "Erreur: Ollama n'est pas disponible. Vérifiez l'installation et le service."
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"Exécution de l'inférence avec le prompt: {prompt[:50]}...")
        logger.info(f"Modèle sélectionné: {model}")
        
        # Vérifier si CUDA est disponible (pour information seulement)
        if torch.cuda.is_available():
            device = "cuda"
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU détecté: {device_name}")
            print(f"GPU détecté: {device_name}")
        else:
            device = "cpu"
            logger.info("Aucun GPU détecté, utilisation du CPU")
            print("Aucun GPU détecté, utilisation du CPU")
        
        # Configuration de la requête à Ollama
        url = f"{OLLAMA_API_BASE}/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
                "top_p": 0.9,
                "seed": 42  # Pour des résultats plus cohérents
            }
        }
        
        print(f"Chargement du modèle {model}...")
        start_time = time.time()
        
        try:
            if stream:
                return OllamaClient._run_inference_stream(url, headers, data, start_time)
            else:
                return OllamaClient._run_inference_basic(url, headers, data, start_time)
        except TimeoutError:
            error_msg = f"Erreur: L'inférence a dépassé le délai d'exécution ({TIMEOUT} secondes)"
            logger.error(error_msg)
            print(error_msg)
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Erreur: Impossible de se connecter à Ollama. Vérifiez qu'Ollama est bien lancé sur {OLLAMA_API_HOST}:{OLLAMA_API_PORT}"
            logger.error(error_msg)
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Erreur lors de l'inférence: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return error_msg
    
    @staticmethod
    def _run_inference_basic(url, headers, data, start_time):
        """Version non-streaming de l'inférence"""
        # Configurer le timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT)
        
        try:
            # Mode non-streaming
            response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
            response.raise_for_status()  # Gérer les erreurs HTTP
            result = response.json()
            
            # Désactiver le timeout
            signal.alarm(0)
            
            # Extraire le texte généré
            generated_text = result.get("response", "")
            
            inference_time = time.time() - start_time
            logger.info(f"Inférence terminée en {inference_time:.2f} secondes")
            print(f"\nInférence terminée en {inference_time:.2f} secondes")
            
            if torch.cuda.is_available():
                memory_usage = torch.cuda.memory_allocated() / 1024**2
                logger.info(f"Utilisation mémoire GPU: {memory_usage:.2f} MB")
                print(f"Utilisation mémoire GPU: {memory_usage:.2f} MB")
            
            return generated_text
        finally:
            # S'assurer que le timeout est désactivé
            signal.alarm(0)
    
    @staticmethod
    def _run_inference_stream(url, headers, data, start_time):
        """Version streaming de l'inférence"""
        # Pour le streaming, nous utilisons un thread séparé pour surveiller le timeout
        cancel_event = threading.Event()
        timeout_thread = threading.Timer(
            TIMEOUT, 
            lambda: (cancel_event.set(), logger.error(f"Timeout après {TIMEOUT} secondes"))
        )
        timeout_thread.daemon = True
        timeout_thread.start()
        
        try:
            # Mode streaming
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            
            generated_text = ""
            token_count = 0
            
            for line in response.iter_lines():
                if cancel_event.is_set():
                    raise TimeoutError(f"L'inférence a dépassé le délai d'exécution ({TIMEOUT} secondes)")
                
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    generated_text += token
                    
                    # Mise à jour de la progression
                    token_count += 1
                    if token_count % 5 == 0:  # Afficher tous les 5 tokens pour ne pas surcharger
                        print(f"Génération du token {token_count}...", end="\r")
                
                # Vérifier si c'est la fin de la génération
                if chunk.get("done", False):
                    break
            
            # Annuler le timeout
            timeout_thread.cancel()
            
            inference_time = time.time() - start_time
            logger.info(f"Inférence terminée en {inference_time:.2f} secondes")
            print(f"\nInférence terminée en {inference_time:.2f} secondes")
            
            if torch.cuda.is_available():
                memory_usage = torch.cuda.memory_allocated() / 1024**2
                logger.info(f"Utilisation mémoire GPU: {memory_usage:.2f} MB")
                print(f"Utilisation mémoire GPU: {memory_usage:.2f} MB")
            
            return generated_text
        except Exception as e:
            # Annuler le timeout
            timeout_thread.cancel()
            raise e

class ConfigManager:
    """Gestion de la configuration de l'application"""
    
    @staticmethod
    def get_default_model():
        """Récupère le modèle par défaut depuis la configuration"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        default_model = "llama3"
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    model = config.get("default_model", default_model)
                    
                    # Si le modèle est "none", utiliser un modèle par défaut
                    if model == "none":
                        logger.warning("Le modèle par défaut est 'none', utilisation de 'llama3'")
                        return default_model
                    
                    return model
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du modèle par défaut: {e}")
        
        return default_model
    
    @staticmethod
    def save_inference_stats(model, prompt, max_tokens, output, execution_time=0):
        """Enregistre les statistiques d'inférence pour analyse ultérieure"""
        stats_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats")
        
        # Créer le répertoire stats s'il n'existe pas
        if not os.path.exists(stats_dir):
            os.makedirs(stats_dir)
        
        # Enregistrer l'inférence dans le fichier de statistiques
        stats_file = os.path.join(stats_dir, "inference_stats.json")
        
        stats = []
        if os.path.exists(stats_file):
            try:
                with open(stats_file, "r") as f:
                    stats = json.load(f)
            except:
                stats = []
        
        # Ajouter la nouvelle inférence
        stats.append({
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "output_length": len(output.split()),
            "execution_time": execution_time
        })
        
        # Limiter à 200 dernières inférences
        if len(stats) > 200:
            stats = stats[-200:]
        
        # Enregistrer les statistiques
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

def run_inference(prompt, model, max_length=500, temperature=0.7):
    """
    Exécute une inférence en utilisant Ollama
    
    Args:
        prompt (str): Le prompt à envoyer au modèle
        model (str): Le nom du modèle à utiliser
        max_length (int): Nombre maximum de tokens à générer
        temperature (float): Température pour la génération (0-1)
        
    Returns:
        str: Le texte généré
    """
    print(f"\033[1mExécution de l'inférence avec le modèle {model}\033[0m")
    print(f"Prompt: {prompt}")
    print(f"Paramètres: température={temperature}, max_tokens={max_length}")
    
    # Mesurer le temps d'exécution
    start_time = time.time()
    result = OllamaClient.run_inference(prompt, model, temperature, max_length, stream=False)
    execution_time = time.time() - start_time
    
    # Enregistrer les statistiques
    ConfigManager.save_inference_stats(model, prompt, max_length, result, execution_time)
    
    print("\n\033[1mTexte généré:\033[0m")
    print("\033[94m" + result + "\033[0m")
    
    return result

def run_inference_stream(prompt, model, max_length=500, temperature=0.7):
    """
    Version streaming de l'inférence pour afficher les tokens en temps réel
    
    Args:
        prompt (str): Le prompt à envoyer au modèle
        model (str): Le nom du modèle à utiliser
        max_length (int): Nombre maximum de tokens à générer
        temperature (float): Température pour la génération (0-1)
        
    Returns:
        str: Le texte généré
    """
    print(f"\033[1mExécution de l'inférence (streaming) avec le modèle {model}\033[0m")
    print(f"Prompt: {prompt}")
    print(f"Paramètres: température={temperature}, max_tokens={max_length}")
    
    # Mesurer le temps d'exécution
    start_time = time.time()
    result = OllamaClient.run_inference(prompt, model, temperature, max_length, stream=True)
    execution_time = time.time() - start_time
    
    # Enregistrer les statistiques
    ConfigManager.save_inference_stats(model, prompt, max_length, result, execution_time)
    
    print("\n\033[1mTexte généré:\033[0m")
    print("\033[94m" + result + "\033[0m")
    
    return result

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Exécuter une inférence avec un modèle Ollama",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--model", help="Nom du modèle à utiliser (par défaut: configuré dans ollama_config.json)")
    parser.add_argument("--no-stream", action="store_true", help="Désactiver le mode streaming")
    parser.add_argument("--temperature", type=float, default=0.7, help="Température pour la génération (0-1)")
    parser.add_argument("--max-tokens", type=int, default=500, help="Nombre maximum de tokens à générer")
    parser.add_argument("--timeout", type=int, default=TIMEOUT, help=f"Délai d'exécution maximum en secondes (défaut: {TIMEOUT})")
    parser.add_argument("--list-models", action="store_true", help="Lister les modèles disponibles")
    parser.add_argument("--host", help=f"Hôte de l'API Ollama (défaut: {OLLAMA_API_HOST})")
    parser.add_argument("--port", help=f"Port de l'API Ollama (défaut: {OLLAMA_API_PORT})")
    parser.add_argument("prompt", nargs="*", help="Prompt à envoyer au modèle")
    
    args = parser.parse_args()
    
    # Mise à jour de la configuration globale
    global OLLAMA_API_HOST, OLLAMA_API_PORT, OLLAMA_API_BASE, TIMEOUT
    if args.host:
        OLLAMA_API_HOST = args.host
    if args.port:
        OLLAMA_API_PORT = args.port
    OLLAMA_API_BASE = f"http://{OLLAMA_API_HOST}:{OLLAMA_API_PORT}/api"
    if args.timeout:
        TIMEOUT = args.timeout
    
    # Lister les modèles si demandé
    if args.list_models:
        if not OllamaClient.ensure_ollama_running():
            print("Erreur: Ollama n'est pas disponible. Vérifiez l'installation et le service.")
            return 1
        
        models = OllamaClient.get_models()
        if not models:
            print("Aucun modèle disponible.")
            return 0
        
        print("\n=== Modèles disponibles ===")
        print(f"{'Nom':<20} {'Taille':<10} {'Modifié le':<20}")
        print("-" * 50)
        
        default_model = ConfigManager.get_default_model()
        
        for model in models:
            name = model.get("name", "Inconnu")
            size = model.get("size", 0) // (1024 * 1024)  # Convertir en MB
            modified = model.get("modified", "Inconnu")
            default_mark = " (défaut)" if name == default_model else ""
            print(f"{name:<20} {size:>6} MB  {modified:<20}{default_mark}")
        
        print("\nPour utiliser un modèle spécifique:")
        print("python run-inference.py --model nom_du_modele \"Votre prompt ici\"")
        
        return 0
    
    # Vérifier si un prompt est fourni
    if not args.prompt:
        parser.print_help()
        return 1
    
    # Assembler le prompt complet
    prompt = " ".join(args.prompt)
    
    # Si aucun modèle n'est spécifié, utiliser le modèle par défaut
    model = args.model if args.model else ConfigManager.get_default_model()
    
    # Afficher clairement le modèle sélectionné
    print(f"\033[1;36mModèle sélectionné: {model}\033[0m")  # En cyan pour le mettre en évidence
    
    # Choisir la méthode d'inférence en fonction du paramètre
    use_streaming = not args.no_stream
    result = None
    
    try:
        if use_streaming:
            result = run_inference_stream(prompt, model, args.max_tokens, args.temperature)
        else:
            result = run_inference(prompt, model, args.max_tokens, args.temperature)
        
        # Un code de retour 0 indique un succès
        return 0
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'inférence: {e}")
        print(f"Erreur: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
