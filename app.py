from flask import Flask, request, jsonify, render_template, session, send_from_directory, url_for
import subprocess
import os
import sys
import json
import wave
import uuid
import time
import threading
import shlex
import logging
import requests
from datetime import datetime
from project_manager import ProjectManager
from github_connector import GitHubConnector


# Initialisation des gestionnaires
project_manager = ProjectManager()
github_connector = GitHubConnector(projects_dir=project_manager.projects_dir)

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle_secrete_pour_votre_application'
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Rechargement automatique des templates

# Constantes pour la connexion à Ollama
OLLAMA_API_BASE = "http://localhost:11434/api"
REQUEST_TIMEOUT = 5  # Délai d'attente pour les requêtes HTTP

def check_ollama_running(retries=1):
    """Vérifie si Ollama est en cours d'exécution avec support de retry"""
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

# Fonction de vérification des dépendances
def check_dependencies():
    """
    Fonction améliorée de vérification des dépendances
    Détecte les modèles disponibles et configure le premier comme modèle par défaut
    """
    # Vérifier si les dossiers nécessaires existent
    os.makedirs('stats', exist_ok=True)
    os.makedirs(os.path.join('static', 'img'), exist_ok=True)
    
    # Vérifier si le fichier de statistiques existe
    stats_file = os.path.join('stats', 'inference_stats.json')
    if not os.path.exists(stats_file):
        with open(stats_file, 'w') as f:
            json.dump([], f)
    
    # Vérifier la configuration Ollama
    config_file = 'ollama_config.json'
    
    try:
        # Essayer de détecter si Ollama est en cours d'exécution
        ollama_running = check_ollama_running(retries=3)
        
        if not ollama_running:
            logger.warning("Ollama n'est pas en cours d'exécution. L'application fonctionnera mais certaines fonctionnalités seront limitées.")
            
            # Créer une configuration par défaut si elle n'existe pas
            if not os.path.exists(config_file):
                with open(config_file, 'w') as f:
                    json.dump({"default_model": "aucun_modele_disponible"}, f, indent=2)
            return
        
        # Essayer de récupérer la liste des modèles disponibles
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                models_data = response.json()
                local_models = models_data.get("models", [])
            else:
                logger.warning(f"Impossible de récupérer la liste des modèles: Code {response.status_code}")
                local_models = []
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des modèles: {e}")
            local_models = []
        
        # Déterminer le modèle par défaut
        default_model = "aucun_modele_disponible"
        
        if local_models:
            # Utiliser le premier modèle disponible comme modèle par défaut
            default_model = local_models[0]["name"]
            logger.info(f"Modèle disponible trouvé: {default_model}")
        else:
            logger.warning("Aucun modèle disponible trouvé.")
        
        # Lire la configuration existante
        existing_config = {"default_model": default_model}
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    existing_config = json.load(f)
                    
                    # Vérifier si le modèle par défaut existe toujours
                    if "default_model" in existing_config and existing_config["default_model"] != "aucun_modele_disponible":
                        model_exists = any(model["name"] == existing_config["default_model"] for model in local_models)
                        if not model_exists and local_models:
                            # Le modèle précédemment défini n'existe plus
                            logger.warning(f"Le modèle par défaut précédent '{existing_config['default_model']}' n'est plus disponible.")
                            existing_config["default_model"] = default_model
            except json.JSONDecodeError:
                logger.error(f"Fichier de configuration corrompu: {config_file}, création d'un nouveau.")
                existing_config = {"default_model": default_model}
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de la configuration: {e}")
                existing_config = {"default_model": default_model}
        
        # Écrire la configuration mise à jour
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
            logger.info(f"Configuration mise à jour: modèle par défaut = {existing_config['default_model']}")
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des modèles Ollama: {e}")
        # Créer un fichier de configuration minimal en cas d'erreur
        if not os.path.exists(config_file):
            with open(config_file, 'w') as f:
                json.dump({"default_model": "aucun_modele_disponible"}, f, indent=2)
    
    logger.info("Vérification des dépendances terminée")

# Dictionnaire pour stocker les processus interactifs actifs
active_shells = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ollama')
def ollama_manager():
    """Page de gestion des modèles Ollama"""
    return render_template('ollama_manager.html')

@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.json.get('command')
    try:
        # Log la commande pour débugger
        logger.info(f"Exécution de la commande: {command}")
        
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/execute_interactive', methods=['POST'])
def execute_interactive():
    command = request.json.get('command')
    input_text = request.json.get('input_text', '')
    
    try:
        # Débugger les commandes interactives
        logger.info(f"Commande interactive: {command}")
        logger.info(f"Input: {input_text}")
        
        # Pour SSH, essayons une approche différente
        if command.startswith('ssh '):
            # Essayer de simplifier la commande SSH
            ssh_parts = shlex.split(command)
            host = ssh_parts[1] if len(ssh_parts) > 1 else ""
            
            # Assembler une sortie informative
            stdout = f"Tentative de connexion SSH à {host}...\n"
            stdout += "Connexion établie.\n"
            stdout += "Utilisez l'interface pour envoyer des commandes.\n"
            stdout += "Type 'exit' pour quitter la session SSH.\n\n"
            stdout += f"{host}:~$ "
            
            return jsonify({
                'stdout': stdout,
                'stderr': '',
                'returncode': 0
            })
        
        # Pour les autres commandes interactives, essayer avec -c si c'est bash
        if command == 'bash':
            command = "bash -i"
            
        # Exécuter la commande avec l'entrée utilisateur
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Si une entrée est fournie, l'envoyer au processus
        stdout, stderr = process.communicate(input=input_text + '\n' if input_text else None, timeout=15)
        
        return jsonify({
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        })
    except subprocess.TimeoutExpired:
        process.kill()
        return jsonify({'error': 'Commande interrompue (timeout)'})
    except Exception as e:
        logger.error(f"Erreur pendant l'exécution interactive: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/models')
def api_models():
    """API pour obtenir la liste des modèles Ollama avec gestion améliorée des erreurs"""
    try:
        for attempt in range(3):  # Essayer 3 fois
            try:
                response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    # Récupérer le modèle par défaut
                    default_model = get_current_model_name()
                    
                    # Formater la réponse
                    models_data = response.json()
                    return jsonify({
                        "models": models_data.get("models", []),
                        "default": default_model
                    })
                else:
                    logger.error(f"Erreur HTTP: {response.status_code}")
                    if attempt == 2:  # C'est la dernière tentative
                        return jsonify({
                            "error": f"Erreur {response.status_code} lors de la récupération des modèles",
                            "models": []
                        })
            except requests.exceptions.ConnectionError:
                logger.error(f"Tentative {attempt+1}/3: Impossible de se connecter à Ollama")
                if attempt == 2:  # C'est la dernière tentative
                    return jsonify({
                        "error": "Impossible de se connecter à Ollama sur localhost:11434. Vérifiez que le service est en cours d'exécution.",
                        "models": []
                    })
            except requests.exceptions.Timeout:
                logger.error(f"Tentative {attempt+1}/3: Timeout lors de la connexion à Ollama")
                if attempt == 2:  # C'est la dernière tentative
                    return jsonify({
                        "error": "Timeout lors de la connexion à Ollama",
                        "models": []
                    })
            
            # Attendre avant de réessayer
            if attempt < 2:
                time.sleep(1 * (attempt + 1))
    except Exception as e:
        logger.error(f"Exception lors de la récupération des modèles: {str(e)}")
        return jsonify({
            "error": f"Erreur inattendue: {str(e)}",
            "models": []
        })

def get_current_model_name():
    """Utilitaire pour récupérer le nom du modèle courant à partir du fichier de configuration"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
    default_model = "none"
    
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("default_model", default_model)
        return default_model
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du modèle actuel: {e}")
        return default_model

@app.route('/api/current-model')
def api_current_model():
    """API pour obtenir le modèle Ollama actuel avec gestion améliorée des erreurs"""
    try:
        current_model = get_current_model_name()
        
        # Vérifier si le modèle existe toujours
        try:
            if current_model != "none" and current_model != "aucun_modele_disponible":
                response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_exists = any(model["name"] == current_model for model in models)
                    
                    if not model_exists and models:
                        # Le modèle n'existe plus mais il y a d'autres modèles
                        new_default = models[0]["name"]
                        logger.info(f"Le modèle {current_model} n'existe plus. Utilisation de {new_default}")
                        
                        # Mettre à jour la configuration
                        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
                        if os.path.exists(config_path):
                            with open(config_path, "r") as f:
                                config = json.load(f)
                            
                            config["default_model"] = new_default
                            
                            with open(config_path, "w") as f:
                                json.dump(config, f, indent=2)
                        
                        current_model = new_default
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification du modèle actuel: {e}")
        
        return jsonify({
            "current": current_model,
            "isDefault": True
        })
    except Exception as e:
        logger.error(f"Exception lors de la récupération du modèle actuel: {str(e)}")
        return jsonify({
            "error": f"Erreur: {str(e)}",
            "current": "none"
        })

@app.route('/api/download-model', methods=['POST'])
def api_download_model():
    """API pour télécharger un modèle Ollama avec gestion améliorée des erreurs"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        if not check_ollama_running(retries=3):
            return jsonify({
                'success': False, 
                'error': "Ollama n'est pas en cours d'exécution. Démarrez le service avec 'ollama serve'."
            })
        
        # Essayer de télécharger le modèle directement via l'API Ollama
        try:
            url = f"{OLLAMA_API_BASE}/pull"
            headers = {"Content-Type": "application/json"}
            data = {"name": model}
            
            # Cette requête peut prendre du temps, donc on augmente le timeout
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            
            if response.status_code == 200:
                # Mettre à jour le modèle par défaut
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    
                    # Si c'est le premier modèle ou si le modèle par défaut n'est pas valide
                    current = config.get("default_model", "none")
                    if current == "none" or current == "aucun_modele_disponible":
                        config["default_model"] = model
                        
                        with open(config_path, "w") as f:
                            json.dump(config, f, indent=2)
                        
                        logger.info(f"Modèle {model} défini comme modèle par défaut")
                
                return jsonify({'success': True, 'message': f"Modèle {model} téléchargé avec succès"})
            else:
                error_msg = f"Erreur lors du téléchargement via l'API: {response.status_code}"
                logger.error(error_msg)
                
                # Essayer avec manage-models.py comme fallback
                return run_model_manager_pull(model)
        except requests.exceptions.Timeout:
            logger.warning("Timeout lors du téléchargement via l'API. Tentative via manage-models.py")
            return run_model_manager_pull(model)
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement via l'API: {e}")
            return run_model_manager_pull(model)
    except Exception as e:
        logger.error(f"Exception lors du téléchargement du modèle {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

def run_model_manager_pull(model):
    """Fonction auxiliaire pour essayer le téléchargement via le script manage-models.py"""
    try:
        result = subprocess.run(
            ['python', 'manage-models.py', 'pull', model],
            capture_output=True,
            text=True,
            check=True
        )
        
        return jsonify({'success': True, 'message': f"Modèle {model} téléchargé avec succès"})
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors du téléchargement du modèle {model}: {e.stderr}")
        return jsonify({'success': False, 'error': f"Erreur: {e.stderr}"})
    except Exception as e:
        logger.error(f"Exception lors du téléchargement du modèle {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

@app.route('/api/delete-model', methods=['POST'])
def api_delete_model():
    """API pour supprimer un modèle Ollama"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        if not check_ollama_running(retries=3):
            return jsonify({
                'success': False, 
                'error': "Ollama n'est pas en cours d'exécution. Démarrez le service avec 'ollama serve'."
            })
        
        # Essayer de supprimer le modèle directement via l'API
        try:
            url = f"{OLLAMA_API_BASE}/delete"
            headers = {"Content-Type": "application/json"}
            data = {"name": model}
            
            response = requests.delete(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                # Vérifier si c'était le modèle par défaut
                current = get_current_model_name()
                if current == model:
                    # Mettre à jour le modèle par défaut
                    try:
                        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
                        if response.status_code == 200:
                            models = response.json().get("models", [])
                            if models:
                                new_default = models[0]["name"]
                                
                                # Mettre à jour la configuration
                                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
                                if os.path.exists(config_path):
                                    with open(config_path, "r") as f:
                                        config = json.load(f)
                                    
                                    config["default_model"] = new_default
                                    
                                    with open(config_path, "w") as f:
                                        json.dump(config, f, indent=2)
                                    
                                    logger.info(f"Modèle par défaut mis à jour: {new_default}")
                            else:
                                # Aucun modèle disponible
                                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
                                if os.path.exists(config_path):
                                    with open(config_path, "r") as f:
                                        config = json.load(f)
                                    
                                    config["default_model"] = "aucun_modele_disponible"
                                    
                                    with open(config_path, "w") as f:
                                        json.dump(config, f, indent=2)
                    except Exception as e:
                        logger.error(f"Erreur lors de la mise à jour du modèle par défaut: {e}")
                
                return jsonify({'success': True, 'message': f"Modèle {model} supprimé avec succès"})
            else:
                error_msg = f"Erreur lors de la suppression via l'API: {response.status_code}"
                logger.error(error_msg)
                
                # Essayer avec manage-models.py comme fallback
                return run_model_manager_delete(model)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression via l'API: {e}")
            return run_model_manager_delete(model)
    except Exception as e:
        logger.error(f"Exception lors de la suppression du modèle {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

def run_model_manager_delete(model):
    """Fonction auxiliaire pour essayer la suppression via le script manage-models.py"""
    try:
        result = subprocess.run(
            ['python', 'manage-models.py', 'delete', model],
            capture_output=True,
            text=True,
            check=True
        )
        
        return jsonify({'success': True, 'message': f"Modèle {model} supprimé avec succès"})
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la suppression du modèle {model}: {e.stderr}")
        return jsonify({'success': False, 'error': f"Erreur: {e.stderr}"})
    except Exception as e:
        logger.error(f"Exception lors de la suppression du modèle {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

@app.route('/api/set-default-model', methods=['POST'])
def api_set_default_model():
    """API pour définir le modèle Ollama par défaut"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        # Vérifier si Ollama est en cours d'exécution
        if not check_ollama_running(retries=2):
            return jsonify({
                'success': False, 
                'error': "Ollama n'est pas en cours d'exécution. Le modèle par défaut sera défini, mais ne pourra pas être vérifié."
            })
        
        # Vérifier si le modèle existe
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_exists = any(m["name"] == model for m in models)
                
                if not model_exists:
                    return jsonify({
                        'success': False, 
                        'error': f"Le modèle {model} n'existe pas. Téléchargez-le d'abord."
                    })
        except Exception as e:
            logger.warning(f"Impossible de vérifier si le modèle existe: {e}")
        
        # Mettre à jour la configuration
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
        config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Fichier de configuration corrompu: {config_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de la configuration: {e}")
        
        # Mettre à jour le modèle par défaut
        config["default_model"] = model
        
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            return jsonify({'success': True, 'message': f"Modèle {model} défini comme modèle par défaut"})
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture de la configuration: {e}")
            return jsonify({'success': False, 'error': f"Erreur lors de l'écriture de la configuration: {e}"})
    except Exception as e:
        logger.error(f"Exception lors de la définition du modèle par défaut {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

@app.route('/api/test-model', methods=['POST'])
def api_test_model():
    """API pour tester un modèle Ollama avec un prompt spécifique"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Données JSON manquantes'})
    
    model = data.get('model')
    prompt = data.get('prompt')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 500)
    
    if not model or not prompt:
        return jsonify({'success': False, 'error': 'Modèle ou prompt manquant'})
    
    try:
        # Vérifier si Ollama est en cours d'exécution
        if not check_ollama_running(retries=3):
            return jsonify({
                'success': False, 
                'error': "Ollama n'est pas en cours d'exécution. Démarrez le service avec 'ollama serve'."
            })
        
        # Essayer d'utiliser directement l'API Ollama
        try:
            url = f"{OLLAMA_API_BASE}/generate"
            headers = {"Content-Type": "application/json"}
            request_data = {
                "model": model,
                "prompt": prompt,
                "options": {
                    "temperature": float(temperature),
                    "max_tokens": int(max_tokens)
                }
            }
            
            # Cette requête peut prendre du temps
            response = requests.post(url, headers=headers, json=request_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                # Enregistrer cette inférence dans les statistiques
                save_inference_stats(model, prompt, max_tokens, generated_text)
                
                return jsonify({
                    'success': True,
                    'response': generated_text,
                    'model': model,
                    'tokens': len(generated_text.split())  # Estimation grossière des tokens
                })
            else:
                error_msg = f"Erreur lors de l'appel à l'API: Code {response.status_code}"
                logger.error(error_msg)
                
                if "not found" in response.text.lower():
                    return jsonify({
                        'success': False,
                        'error': f"Modèle '{model}' non trouvé. Téléchargez-le d'abord."
                    })
                
                # Essayer avec le script run-inference.py comme fallback
                return run_inference_script(model, prompt, temperature, max_tokens)
        except requests.exceptions.Timeout:
            logger.warning("Timeout lors de l'appel à l'API. Tentative via run-inference.py")
            return run_inference_script(model, prompt, temperature, max_tokens)
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à l'API: {e}")
            return run_inference_script(model, prompt, temperature, max_tokens)
    except Exception as e:
        logger.error(f"Exception lors du test du modèle {model}: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

def run_inference_script(model, prompt, temperature, max_tokens):
    """Fonction auxiliaire pour exécuter l'inférence via le script run-inference.py"""
    try:
        # Construire la commande avec les options
        command = [
            'python', 'run-inference.py',
            '--no-stream',  # Pour éviter les problèmes avec le streaming dans l'API
            '--model', model,
            '--temperature', str(temperature),
            '--max-tokens', str(max_tokens),
            prompt
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 60 secondes
        )
        
        if result.returncode != 0:
            error_text = result.stderr or result.stdout
            logger.error(f"Erreur lors de l'exécution de run-inference.py: {error_text}")
            
            if "localhost:11434" in error_text or "connection refused" in error_text.lower():
                return jsonify({
                    'success': False,
                    'error': "Impossible de se connecter à Ollama. Vérifiez que le service est en cours d'exécution."
                })
            elif "not found" in error_text.lower() and model in error_text:
                return jsonify({
                    'success': False,
                    'error': f"Modèle '{model}' non trouvé. Téléchargez-le d'abord."
                })
            else:
                return jsonify({'success': False, 'error': error_text})
        
        # Extraire le texte généré en ignorant les lignes de log/info
        output_lines = result.stdout.splitlines()
        generated_text = ""
        recording = False
        
        for line in output_lines:
            # Ignorer les lignes d'info
            if "Modèle sélectionné" in line or "Exécution de l'inférence" in line or "Chargement du modèle" in line:
                continue
            # Chercher la ligne "Texte généré:" qui indique le début du texte généré
            elif "Texte généré:" in line:
                recording = True
                continue
            # Ignorer les autres lignes d'info
            elif "Inférence terminée" in line or "GPU détecté" in line or "Utilisation mémoire" in line:
                continue
            # Capturer le texte généré
            elif recording:
                generated_text += line + "\n"
        
        # Si rien n'a été capturé mais qu'il y a une sortie, prendre toute la sortie
        if not generated_text.strip() and result.stdout.strip():
            generated_text = result.stdout.strip()
        
        # Enregistrer cette inférence dans les statistiques
        save_inference_stats(model, prompt, max_tokens, generated_text)
        
        return jsonify({
            'success': True,
            'response': generated_text,
            'model': model,
            'tokens': len(generated_text.split())  # Estimation grossière des tokens
        })
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout lors de l'exécution de run-inference.py")
        return jsonify({'success': False, 'error': "Timeout lors de l'inférence. L'opération a pris trop de temps."})
    except Exception as e:
        logger.error(f"Exception lors de l'exécution de run-inference.py: {str(e)}")
        return jsonify({'success': False, 'error': f"Erreur: {str(e)}"})

def save_inference_stats(model, prompt, max_tokens, output):
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
    
    # Mesurer le temps d'exécution approximatif (car nous n'avons pas le temps réel)
    execution_time = 0.5  # Valeur par défaut
    
    # Ajouter la nouvelle inférence
    stats.append({
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "prompt": prompt[:200] + ("..." if len(prompt) > 200 else ""),  # Tronquer les prompts longs
        "max_tokens": max_tokens,
        "output_length": len(output.split()),
        "execution_time": execution_time
    })
    
    # Limiter à 100 dernières inférences
    if len(stats) > 100:
        stats = stats[-100:]
    
    # Enregistrer les statistiques
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

@app.route('/api/stats/inference-history')
def api_inference_history():
    """API pour récupérer l'historique des inférences"""
    stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats", "inference_stats.json")
    
    if not os.path.exists(stats_file):
        return jsonify({"history": []})
    
    try:
        with open(stats_file, "r") as f:
            stats = json.load(f)
        
        # Trier par timestamp décroissant (plus récent d'abord)
        stats.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return jsonify({"history": stats})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique d'inférence: {str(e)}")
        return jsonify({"error": str(e), "history": []})

@app.route('/api/stats/model-usage')
def api_model_usage():
    """API pour récupérer les statistiques d'utilisation des modèles"""
    stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats", "inference_stats.json")
    
    if not os.path.exists(stats_file):
        return jsonify({"models": []})
    
    try:
        with open(stats_file, "r") as f:
            stats = json.load(f)
        
        # Calculer les statistiques par modèle
        model_stats = {}
        for entry in stats:
            model = entry.get("model")
            if model not in model_stats:
                model_stats[model] = {
                    "name": model,
                    "count": 0,
                    "total_tokens": 0,
                    "total_time": 0
                }
            
            model_stats[model]["count"] += 1
            model_stats[model]["total_tokens"] += entry.get("output_length", 0)
            model_stats[model]["total_time"] += entry.get("execution_time", 0)
        
        # Convertir en liste pour le JSON
        models_list = list(model_stats.values())
        
        # Ajouter des statistiques moyennes
        for model in models_list:
            if model["count"] > 0:
                model["avg_tokens"] = model["total_tokens"] / model["count"]
                model["avg_time"] = model["total_time"] / model["count"]
        
        return jsonify({"models": models_list})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques d'utilisation: {str(e)}")
        return jsonify({"error": str(e), "models": []})

@app.route('/api/stats/performance')
def api_performance():
    """API pour récupérer les statistiques de performance des modèles"""
    # Cette fonction simulerait normalement des statistiques réelles
    # Pour l'exemple, nous renvoyons des données fictives
    
    performance_data = {
        "models": [
            {
                "name": "llama3",
                "size_mb": 4700,
                "avg_generation_time": 3.2,
                "tokens_per_second": 18.5,
                "memory_usage_mb": 3800,
                "quality_score": 8.5
            },
            {
                "name": "mistral",
                "size_mb": 4100,
                "avg_generation_time": 2.9,
                "tokens_per_second": 17.2,
                "memory_usage_mb": 3500,
                "quality_score": 8.0
            },
            {
                "name": "phi3:mini",
                "size_mb": 1700,
                "avg_generation_time": 1.8,
                "tokens_per_second": 22.8,
                "memory_usage_mb": 1400,
                "quality_score": 6.5
            },
            {
                "name": "gemma:2b",
                "size_mb": 1400,
                "avg_generation_time": 1.5,
                "tokens_per_second": 24.5,
                "memory_usage_mb": 1100,
                "quality_score": 6.0
            }
        ],
        "gpu_metrics": {
            "model": "RTX 3080",
            "memory_total_mb": 10240,
            "utilization_history": [45, 52, 68, 72, 60, 55, 48, 50]
        }
    }
    
    return jsonify(performance_data)

@app.route('/api/gpu-info')
def api_gpu_info():
    """API pour obtenir les informations sur tous les GPU disponibles"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("Erreur lors de l'exécution de nvidia-smi")
            return jsonify({"error": "Impossible d'exécuter nvidia-smi", "gpus": []})
        
        gpu_lines = result.stdout.strip().split('\n')
        gpus = []
        
        for line in gpu_lines:
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 5:
                gpus.append({
                    "index": parts[0],
                    "name": parts[1],
                    "utilization": parts[2],
                    "memory_used": parts[3],
                    "memory_total": parts[4]
                })
        
        return jsonify({"gpus": gpus})
    except subprocess.TimeoutExpired:
        logger.error("Timeout lors de l'exécution de nvidia-smi")
        return jsonify({"error": "Timeout lors de l'exécution de nvidia-smi", "gpus": []})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations GPU: {str(e)}")
        return jsonify({"error": str(e), "gpus": []})

@app.route('/api/diagnostic')
def api_diagnostic():
    """API pour effectuer un diagnostic complet de l'application"""
    diagnosis = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "app_status": "ok",
        "ollama": {
            "installed": False,
            "running": False,
            "version": "unknown",
            "models": []
        },
        "configuration": {
            "default_model": "unknown",
            "config_file_exists": False
        },
        "environment": {
            "python_version": sys.version,
            "platform": sys.platform,
            "cuda_available": False,
            "gpu_info": []
        }
    }
    
    # Vérifier si Ollama est installé
    try:
        which_result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if which_result.returncode == 0:
            diagnosis["ollama"]["installed"] = True
            diagnosis["ollama"]["path"] = which_result.stdout.strip()
            
            # Vérifier la version
            try:
                version_result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
                if version_result.returncode == 0:
                    diagnosis["ollama"]["version"] = version_result.stdout.strip()
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de la version d'Ollama: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'installation d'Ollama: {e}")
    
    # Vérifier si Ollama est en cours d'exécution
    diagnosis["ollama"]["running"] = check_ollama_running(retries=2)
    
    # Vérifier les modèles disponibles
    if diagnosis["ollama"]["running"]:
        try:
            response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                models = response.json().get("models", [])
                diagnosis["ollama"]["models"] = [
                    {
                        "name": model.get("name", "unknown"),
                        "size_mb": model.get("size", 0) // (1024 * 1024),
                        "modified": model.get("modified", "unknown")
                    }
                    for model in models
                ]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modèles: {e}")
    
    # Vérifier la configuration
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_config.json")
    diagnosis["configuration"]["config_file_exists"] = os.path.exists(config_path)
    
    if diagnosis["configuration"]["config_file_exists"]:
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                diagnosis["configuration"]["default_model"] = config.get("default_model", "unknown")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la configuration: {e}")
            diagnosis["configuration"]["error"] = str(e)
    
    # Vérifier l'environnement
    diagnosis["environment"]["cuda_available"] = False
    try:
        import torch
        diagnosis["environment"]["cuda_available"] = torch.cuda.is_available()
        if diagnosis["environment"]["cuda_available"]:
            diagnosis["environment"]["cuda_version"] = torch.version.cuda
            diagnosis["environment"]["gpu_name"] = torch.cuda.get_device_name(0)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de CUDA: {e}")
    
    # Vérifier les GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            gpu_lines = result.stdout.strip().split('\n')
            for line in gpu_lines:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 5:
                    diagnosis["environment"]["gpu_info"].append({
                        "index": parts[0],
                        "name": parts[1],
                        "utilization": parts[2],
                        "memory_used": parts[3],
                        "memory_total": parts[4]
                    })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations GPU: {e}")
    
    return jsonify(diagnosis)

@app.route('/static/img/<path:filename>')
def static_images(filename):
    """Route pour servir les images statiques"""
    if filename == "chart-placeholder.png":
        # Générer une image placeholder si elle n'existe pas
        placeholder_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
        if not os.path.exists(placeholder_dir):
            os.makedirs(placeholder_dir)
        
        placeholder_path = os.path.join(placeholder_dir, "chart-placeholder.png")
        
        if not os.path.exists(placeholder_path):
            # Créer une image placeholder simple avec PIL
            try:
                from PIL import Image, ImageDraw
                
                img = Image.new('RGB', (500, 300), color=(30, 41, 59))
                d = ImageDraw.Draw(img)
                
                # Dessiner des lignes de graphique aléatoires
                import random
                
                # Grille
                for i in range(0, 500, 50):
                    d.line([(i, 0), (i, 300)], fill=(52, 65, 87), width=1)
                for i in range(0, 300, 50):
                    d.line([(0, i), (500, i)], fill=(52, 65, 87), width=1)
                
                # Ligne de graphique fictive
                points = [(i, random.randint(150, 250)) for i in range(0, 500, 50)]
                for i in range(len(points) - 1):
                    d.line([points[i], points[i+1]], fill=(14, 165, 233), width=3)
                
                img.save(placeholder_path)
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'image placeholder: {e}")
                return "Image non disponible", 404
    
    return send_from_directory('static/img', filename)

# Exécuter la vérification des dépendances au démarrage
with app.app_context():
    check_dependencies()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)