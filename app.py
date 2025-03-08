from flask import Flask, request, jsonify, render_template, session, send_from_directory, url_for
import subprocess
import os
import sys
import json
import logging
import time
import threading
import shlex
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Configuration des logs avec rotation
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Configuration du logger principal
logger = logging.getLogger("assistant_ia")
logger.setLevel(logging.INFO)

# Handler pour les fichiers avec rotation (10 fichiers de 5MB max)
file_handler = RotatingFileHandler(
    os.path.join(log_directory, "app.log"),
    maxBytes=5*1024*1024,
    backupCount=10
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Ajout des handlers au logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Création de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'cle_secrete_pour_assistant_ai_v2')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Limite de 50MB pour les uploads
app.config['JSON_SORT_KEYS'] = False  # Préserver l'ordre des clés dans les réponses JSON

# Constantes
CONFIG_FILE = 'ollama_config.json'
STATS_DIRECTORY = 'stats'
INFERENCE_STATS_FILE = os.path.join(STATS_DIRECTORY, 'inference_stats.json')
MAX_INFERENCE_HISTORY = 200  # Nombre maximum d'entrées dans l'historique d'inférence

# Classe pour gérer les configurations
class ConfigManager:
    @staticmethod
    def get_config():
        """Récupère la configuration depuis le fichier JSON"""
        if not os.path.exists(CONFIG_FILE):
            default_config = {"default_model": "llama3"}
            ConfigManager.save_config(default_config)
            return default_config
            
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la configuration: {e}")
            return {"default_model": "llama3"}
    
    @staticmethod
    def save_config(config_data):
        """Enregistre la configuration dans le fichier JSON"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la configuration: {e}")
            return False

# Classe pour gérer les statistiques
class StatsManager:
    @staticmethod
    def init_stats_directory():
        """Initialise le répertoire des statistiques"""
        os.makedirs(STATS_DIRECTORY, exist_ok=True)
        if not os.path.exists(INFERENCE_STATS_FILE):
            with open(INFERENCE_STATS_FILE, 'w') as f:
                json.dump([], f)
    
    @staticmethod
    def save_inference_stats(model, prompt, max_tokens, output, execution_time=0):
        """Enregistre les statistiques d'inférence"""
        StatsManager.init_stats_directory()
        
        try:
            stats = []
            if os.path.exists(INFERENCE_STATS_FILE):
                with open(INFERENCE_STATS_FILE, 'r') as f:
                    stats = json.load(f)
            
            # Ajouter la nouvelle inférence
            stats.append({
                "timestamp": time.time(),
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": model,
                "prompt_length": len(prompt.split()),
                "max_tokens": max_tokens,
                "output_length": len(output.split()),
                "execution_time": execution_time
            })
            
            # Limiter le nombre d'entrées
            if len(stats) > MAX_INFERENCE_HISTORY:
                stats = stats[-MAX_INFERENCE_HISTORY:]
            
            # Enregistrer les statistiques
            with open(INFERENCE_STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des statistiques: {e}")
            return False
    
    @staticmethod
    def get_inference_history():
        """Récupère l'historique des inférences"""
        StatsManager.init_stats_directory()
        
        try:
            if os.path.exists(INFERENCE_STATS_FILE):
                with open(INFERENCE_STATS_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []

# Classe pour gérer Ollama
class OllamaManager:
    @staticmethod
    def is_ollama_running():
        """Vérifie si Ollama est en cours d'exécution"""
        try:
            result = subprocess.run(
                ['python', 'manage-models.py', 'ping', '--json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            response = json.loads(result.stdout)
            return response.get('status') == 'ok'
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'Ollama: {e}")
            return False
    
    @staticmethod
    def get_models():
        """Récupère la liste des modèles Ollama"""
        try:
            result = subprocess.run(
                ['python', 'manage-models.py', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de la récupération des modèles: {result.stderr}")
                return {"error": result.stderr, "models": []}
            
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de la récupération des modèles")
            return {"error": "Timeout lors de la récupération des modèles", "models": []}
        except Exception as e:
            logger.error(f"Exception lors de la récupération des modèles: {e}")
            return {"error": str(e), "models": []}
    
    @staticmethod
    def get_current_model():
        """Récupère le modèle actuel"""
        try:
            result = subprocess.run(
                ['python', 'manage-models.py', 'current', '--json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.error(f"Erreur lors de la récupération du modèle actuel: {result.stderr}")
                return {"error": result.stderr, "current": "none"}
            
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Exception lors de la récupération du modèle actuel: {e}")
            return {"error": str(e), "current": "none"}

# Fonction de vérification des dépendances
def check_dependencies():
    """Vérifie et initialise les dépendances de l'application"""
    logger.info("Vérification des dépendances...")
    
    # Vérifier les répertoires nécessaires
    os.makedirs(STATS_DIRECTORY, exist_ok=True)
    os.makedirs(os.path.join('static', 'img'), exist_ok=True)
    
    # Vérifier le fichier de statistiques
    StatsManager.init_stats_directory()
    
    # Vérifier la configuration Ollama
    try:
        # Essayer de détecter les modèles disponibles localement
        models_data = OllamaManager.get_models()
        local_models = models_data.get('models', [])
        
        # Définir le modèle par défaut en fonction des modèles disponibles
        config = ConfigManager.get_config()
        default_model = config.get('default_model', 'none')
        
        # Vérifier si le modèle par défaut existe toujours
        if local_models:
            model_exists = any(model['name'] == default_model for model in local_models)
            if not model_exists:
                # Si le modèle par défaut n'existe plus, utiliser le premier disponible
                default_model = local_models[0]['name']
                config['default_model'] = default_model
                ConfigManager.save_config(config)
                logger.info(f"Modèle par défaut mis à jour: {default_model}")
        else:
            # Aucun modèle disponible
            if default_model != 'none':
                config['default_model'] = 'none'
                ConfigManager.save_config(config)
                logger.warning("Aucun modèle disponible. Le modèle par défaut a été défini à 'none'.")
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des modèles Ollama: {e}")
    
    logger.info("Vérification des dépendances terminée")

# Dictionnaire pour stocker les processus interactifs actifs
active_shells = {}

# Routes de l'application
@app.route('/')
def index():
    """Page d'accueil - Console interactive"""
    return render_template('index.html')

@app.route('/ollama')
def ollama_manager():
    """Page de gestion des modèles Ollama"""
    return render_template('ollama_manager.html')

@app.route('/execute', methods=['POST'])
def execute_command():
    """Exécute une commande shell"""
    command = request.json.get('command', '')
    if not command:
        return jsonify({'error': 'Commande vide'})
    
    # Journalisation sécurisée de la commande
    logger.info(f"Exécution de la commande: {command}")
    
    try:
        # Utiliser timeout pour éviter les blocages
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=30  # 30 secondes maximum
        )
        
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout lors de l'exécution de la commande: {command}")
        return jsonify({
            'stdout': '',
            'stderr': 'Erreur: La commande a dépassé le délai d\'exécution (30 secondes)',
            'returncode': 124  # Code d'erreur pour timeout
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la commande: {e}")
        return jsonify({'error': str(e)})

@app.route('/execute_interactive', methods=['POST'])
def execute_interactive():
    """Exécute une commande en mode interactif"""
    command = request.json.get('command', '')
    input_text = request.json.get('input_text', '')
    
    if not command:
        return jsonify({'error': 'Commande vide'})
    
    logger.info(f"Commande interactive: {command}")
    logger.info(f"Input: {input_text}")
    
    # Cas spécial pour SSH - simulation
    if command.startswith('ssh '):
        # Extraire le host pour une meilleure simulation
        ssh_parts = shlex.split(command)
        host = ssh_parts[1] if len(ssh_parts) > 1 else "remote-host"
        
        # Assembler une sortie informative
        stdout = f"Tentative de connexion SSH à {host}...\n"
        stdout += "Connexion établie.\n"
        stdout += "Utilisez l'interface pour envoyer des commandes.\n"
        stdout += "Type 'exit' pour quitter la session SSH.\n\n"
        stdout += f"{host}:~$ {input_text}\n"
        
        # Simuler une réponse basée sur l'entrée
        if input_text:
            if input_text == "ls":
                stdout += "Documents  Downloads  Pictures  Music  Videos\n"
            elif input_text == "pwd":
                stdout += f"/home/user@{host}\n"
            elif input_text == "date":
                stdout += datetime.now().strftime("%a %b %d %H:%M:%S %Y") + "\n"
            elif input_text == "exit":
                stdout += "Déconnexion.\nConnexion fermée.\n"
            else:
                stdout += f"Commande '{input_text}' exécutée\n"
        
        stdout += f"{host}:~$ "
        
        return jsonify({
            'stdout': stdout,
            'stderr': '',
            'returncode': 0
        })
    
    try:
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
        stdout, stderr = process.communicate(
            input=input_text + '\n' if input_text else None,
            timeout=15
        )
        
        return jsonify({
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        })
    except subprocess.TimeoutExpired:
        process.kill()
        return jsonify({
            'error': 'Commande interrompue (timeout)',
            'stdout': '',
            'stderr': 'La commande a dépassé le délai d\'exécution (15 secondes)',
            'returncode': 124
        })
    except Exception as e:
        logger.error(f"Erreur pendant l'exécution interactive: {e}")
        return jsonify({'error': str(e)})

# API Routes

@app.route('/api/models')
def api_models():
    """API pour obtenir la liste des modèles Ollama"""
    return jsonify(OllamaManager.get_models())

@app.route('/api/current-model')
def api_current_model():
    """API pour obtenir le modèle Ollama actuel"""
    return jsonify(OllamaManager.get_current_model())

@app.route('/api/download-model', methods=['POST'])
def api_download_model():
    """API pour télécharger un modèle Ollama"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        # Vérifier que le nom du modèle ne contient pas de caractères dangereux
        if not all(c.isalnum() or c in ':-_.' for c in model):
            return jsonify({'success': False, 'error': 'Nom de modèle invalide'})
        
        result = subprocess.run(
            ['python', 'manage-models.py', 'pull', model],
            capture_output=True,
            text=True,
            timeout=60  # Les téléchargements peuvent prendre du temps
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': result.stderr})
        
        return jsonify({'success': True, 'message': f"Modèle {model} téléchargé avec succès"})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout lors du téléchargement du modèle'})
    except Exception as e:
        logger.error(f"Exception lors du téléchargement du modèle {model}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete-model', methods=['POST'])
def api_delete_model():
    """API pour supprimer un modèle Ollama"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        # Vérifier que le nom du modèle ne contient pas de caractères dangereux
        if not all(c.isalnum() or c in ':-_.' for c in model):
            return jsonify({'success': False, 'error': 'Nom de modèle invalide'})
        
        result = subprocess.run(
            ['python', 'manage-models.py', 'delete', model],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': result.stderr})
        
        return jsonify({'success': True, 'message': f"Modèle {model} supprimé avec succès"})
    except Exception as e:
        logger.error(f"Exception lors de la suppression du modèle {model}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set-default-model', methods=['POST'])
def api_set_default_model():
    """API pour définir le modèle Ollama par défaut"""
    model = request.json.get('model')
    if not model:
        return jsonify({'success': False, 'error': 'Nom de modèle non fourni'})
    
    try:
        # Vérifier que le nom du modèle ne contient pas de caractères dangereux
        if not all(c.isalnum() or c in ':-_.' for c in model):
            return jsonify({'success': False, 'error': 'Nom de modèle invalide'})
        
        result = subprocess.run(
            ['python', 'manage-models.py', 'set-default', model],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': result.stderr})
        
        return jsonify({'success': True, 'message': f"Modèle {model} défini comme modèle par défaut"})
    except Exception as e:
        logger.error(f"Exception lors de la définition du modèle par défaut {model}: {e}")
        return jsonify({'success': False, 'error': str(e)})

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
        # Valider les paramètres
        if not all(c.isalnum() or c in ':-_.' for c in model):
            return jsonify({'success': False, 'error': 'Nom de modèle invalide'})
        
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
            return jsonify({'success': False, 'error': 'Température invalide (doit être entre 0 et 1)'})
        
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 4000:
            return jsonify({'success': False, 'error': 'Nombre de tokens invalide (doit être entre 1 et 4000)'})
        
        # Construire la commande avec les options
        start_time = time.time()
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
            timeout=60  # 60 secondes maximum pour l'inférence
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"Erreur lors du test du modèle {model}: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr})
        
        # Extraire le texte généré
        output = result.stdout
        
        # Enregistrer cette inférence dans les statistiques
        StatsManager.save_inference_stats(model, prompt, max_tokens, output, execution_time)
        
        tokens_estimate = len(output.split())
        
        return jsonify({
            'success': True,
            'response': output,
            'model': model,
            'tokens': tokens_estimate,
            'execution_time': round(execution_time, 2)
        })
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout lors du test du modèle {model}")
        return jsonify({'success': False, 'error': 'L\'inférence a dépassé le délai d\'exécution (60 secondes)'})
    except Exception as e:
        logger.error(f"Exception lors du test du modèle {model}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats/inference-history')
def api_inference_history():
    """API pour récupérer l'historique des inférences"""
    try:
        history = StatsManager.get_inference_history()
        
        # Appliquer des filtres si nécessaire
        model_filter = request.args.get('model')
        if model_filter:
            history = [entry for entry in history if entry.get('model') == model_filter]
        
        # Trier par timestamp décroissant (plus récent d'abord)
        history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({"history": history})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique d'inférence: {e}")
        return jsonify({"error": str(e), "history": []})

@app.route('/api/stats/model-usage')
def api_model_usage():
    """API pour récupérer les statistiques d'utilisation des modèles"""
    try:
        history = StatsManager.get_inference_history()
        
        # Calculer les statistiques par modèle
        model_stats = {}
        for entry in history:
            model = entry.get('model')
            if model not in model_stats:
                model_stats[model] = {
                    'name': model,
                    'count': 0,
                    'total_tokens': 0,
                    'total_time': 0,
                    'prompt_tokens': 0
                }
            
            model_stats[model]['count'] += 1
            model_stats[model]['total_tokens'] += entry.get('output_length', 0)
            model_stats[model]['total_time'] += entry.get('execution_time', 0)
            model_stats[model]['prompt_tokens'] += entry.get('prompt_length', 0)
        
        # Convertir en liste pour le JSON
        models_list = list(model_stats.values())
        
        # Ajouter des statistiques moyennes
        for model in models_list:
            if model['count'] > 0:
                model['avg_tokens'] = round(model['total_tokens'] / model['count'], 2)
                model['avg_time'] = round(model['total_time'] / model['count'], 2)
                model['avg_prompt_length'] = round(model['prompt_tokens'] / model['count'], 2)
        
        return jsonify({'models': models_list})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques d'utilisation: {e}")
        return jsonify({'error': str(e), 'models': []})

@app.route('/api/stats/performance')
def api_performance():
    """API pour récupérer les statistiques de performance des modèles"""
    try:
        history = StatsManager.get_inference_history()
        
        # Générer des statistiques de performance par modèle
        model_perf = {}
        for entry in history:
            model = entry.get('model')
            if model not in model_perf:
                model_perf[model] = {
                    'name': model,
                    'total_inferences': 0,
                    'times': [],
                    'token_rates': []
                }
            
            execution_time = entry.get('execution_time', 0)
            output_length = entry.get('output_length', 0)
            
            model_perf[model]['total_inferences'] += 1
            model_perf[model]['times'].append(execution_time)
            
            if execution_time > 0:
                token_rate = output_length / execution_time
                model_perf[model]['token_rates'].append(token_rate)
        
        # Calculer les moyennes
        performance_data = {'models': []}
        for model, stats in model_perf.items():
            avg_time = sum(stats['times']) / len(stats['times']) if stats['times'] else 0
            avg_token_rate = sum(stats['token_rates']) / len(stats['token_rates']) if stats['token_rates'] else 0
            
            performance_data['models'].append({
                'name': model,
                'inferences': stats['total_inferences'],
                'avg_generation_time': round(avg_time, 2),
                'tokens_per_second': round(avg_token_rate, 2)
            })
        
        # Ajouter des informations sur le GPU si disponibles
        try:
            gpu_info = json.loads(api_gpu_info().get_data(as_text=True))
            performance_data['gpu_metrics'] = gpu_info.get('gpus', [{}])[0] if gpu_info.get('gpus') else {}
        except:
            performance_data['gpu_metrics'] = {}
        
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques de performance: {e}")
        return jsonify({'error': str(e), 'models': []})

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
            return jsonify({'error': 'Impossible d\'obtenir les informations GPU', 'gpus': []})
        
        gpu_lines = result.stdout.strip().split('\n')
        gpus = []
        
        for line in gpu_lines:
            if not line.strip():
                continue
                
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 5:
                gpus.append({
                    'index': parts[0],
                    'name': parts[1],
                    'utilization': parts[2],
                    'memory_used': parts[3],
                    'memory_total': parts[4]
                })
        
        return jsonify({'gpus': gpus})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout lors de la récupération des informations GPU', 'gpus': []})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations GPU: {e}")
        return jsonify({'error': str(e), 'gpus': []})

@app.route('/static/img/<path:filename>')
def static_images(filename):
    """Route pour servir les images statiques"""
    # Gestion du cas spécial de l'image placeholder
    if filename == "chart-placeholder.png":
        placeholder_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
        placeholder_path = os.path.join(placeholder_dir, "chart-placeholder.png")
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(placeholder_dir, exist_ok=True)
        
        # Si l'image n'existe pas, la créer
        if not os.path.exists(placeholder_path):
            try:
                from PIL import Image, ImageDraw
                import random
                
                # Créer une image 500x300 avec un fond bleu foncé
                img = Image.new('RGB', (500, 300), color=(30, 41, 59))
                d = ImageDraw.Draw(img)
                
                # Dessiner une grille
                for i in range(0, 500, 50):
                    d.line([(i, 0), (i, 300)], fill=(52, 65, 87), width=1)
                for i in range(0, 300, 50):
                    d.line([(0, i), (500, i)], fill=(52, 65, 87), width=1)
                
                # Dessiner plusieurs lignes de graphique
                colors = [(14, 165, 233), (168, 85, 247), (34, 197, 94)]
                
                for color_idx, color in enumerate(colors):
                    # Générer des points pour une courbe
                    base_y = 150 + color_idx * 30
                    amplitude = 30 - color_idx * 5
                    points = [(i, base_y + random.randint(-amplitude, amplitude)) for i in range(0, 500, 50)]
                    
                    # Dessiner la ligne
                    for i in range(len(points) - 1):
                        d.line([points[i], points[i+1]], fill=color, width=3)
                
                # Ajouter une légende
                d.rectangle([(350, 20), (480, 100)], fill=(22, 31, 49), outline=(52, 65, 87))
                d.text((360, 30), "Statistiques", fill=(255, 255, 255))
                for i, color in enumerate(colors):
                    d.line([(360, 50 + i*15), (380, 50 + i*15)], fill=color, width=3)
                    labels = ["Performance", "Inférences", "Utilisation"]
                    d.text((385, 45 + i*15), labels[i], fill=(200, 200, 200))
                
                # Enregistrer l'image
                img.save(placeholder_path)
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'image placeholder: {e}")
                return "Image non disponible", 404
    
    return send_from_directory('static/img', filename)

@app.errorhandler(404)
def page_not_found(e):
    """Gestionnaire pour les erreurs 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Gestionnaire pour les erreurs 500"""
    logger.error(f"Erreur serveur: {e}")
    return render_template('500.html'), 500

# Initialisation de l'application
with app.app_context():
    check_dependencies()

if __name__ == '__main__':
    # Afficher un message de démarrage
    logger.info("=== Démarrage de l'Assistant IA Ollama (v2.0) ===")
    app.run(host='0.0.0.0', port=5000, debug=True)
