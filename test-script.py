#!/usr/bin/env python3
"""
Tests unitaires pour l'application Assistant IA Ollama

Usage:
    pytest test_app.py
    pytest test_app.py -v  # Mode verbeux
    pytest test_app.py -k test_api  # Tests spécifiques
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock

# Importer l'application Flask pour les tests
import app as flask_app

@pytest.fixture
def app():
    """Fixture pour créer l'application Flask pour les tests"""
    app = flask_app.app
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    # Créer le contexte d'application
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Fixture pour créer un client de test"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Fixture pour créer un test CLI runner"""
    return app.test_cli_runner()

# Tests de base des routes
def test_index_route(client):
    """Tester si la page d'accueil se charge"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Console Interactive' in response.data

def test_ollama_manager_route(client):
    """Tester si la page de gestion Ollama se charge"""
    response = client.get('/ollama')
    assert response.status_code == 200
    assert b'Gestionnaire de Mod' in response.data

# Tests des API
@patch('app.OllamaManager.get_models')
def test_api_models(mock_get_models, client):
    """Tester l'API de récupération des modèles"""
    # Simuler la réponse d'Ollama
    mock_get_models.return_value = {
        "models": [
            {"name": "llama3", "size": 4800000000, "modified": 1615000000},
            {"name": "mistral", "size": 4200000000, "modified": 1615000000}
        ],
        "default": "llama3"
    }
    
    response = client.get('/api/models')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["models"]) == 2
    assert data["models"][0]["name"] == "llama3"

@patch('app.OllamaManager.get_current_model')
def test_api_current_model(mock_get_current_model, client):
    """Tester l'API de récupération du modèle actuel"""
    mock_get_current_model.return_value = {"current": "llama3"}
    
    response = client.get('/api/current-model')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["current"] == "llama3"

@patch('app.StatsManager.get_inference_history')
def test_api_inference_history(mock_get_inference_history, client):
    """Tester l'API d'historique d'inférence"""
    mock_get_inference_history.return_value = [
        {
            "timestamp": 1620000000,
            "date": "2021-05-03 12:00:00",
            "model": "llama3",
            "prompt": "Bonjour",
            "max_tokens": 500,
            "output_length": 50,
            "execution_time": 2.5
        }
    ]
    
    response = client.get('/api/stats/inference-history')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["history"]) == 1
    assert data["history"][0]["model"] == "llama3"

# Tests des fonctions utilitaires
def test_config_manager():
    """Tester la classe ConfigManager"""
    from app import ConfigManager
    
    # Créer un fichier de configuration temporaire
    test_config = {"default_model": "test_model"}
    with open('test_config.json', 'w') as f:
        json.dump(test_config, f)
    
    # Sauvegarder et récupérer le chemin original
    original_config_file = flask_app.CONFIG_FILE
    flask_app.CONFIG_FILE = 'test_config.json'
    
    try:
        config = ConfigManager.get_config()
        assert config["default_model"] == "test_model"
        
        # Tester la sauvegarde
        config["default_model"] = "new_model"
        ConfigManager.save_config(config)
        
        # Vérifier que la sauvegarde a fonctionné
        new_config = ConfigManager.get_config()
        assert new_config["default_model"] == "new_model"
    finally:
        # Nettoyer
        flask_app.CONFIG_FILE = original_config_file
        if os.path.exists('test_config.json'):
            os.remove('test_config.json')

# Tests des gestionnaires d'erreurs
def test_404_handler(client):
    """Tester le gestionnaire d'erreur 404"""
    response = client.get('/page-inexistante')
    assert response.status_code == 404
    assert b'Page non trouv' in response.data

# Test de point d'entrée principal
def test_main_function():
    """Tester la fonction main (s'exécute uniquement si le script est lancé directement)"""
    with patch('app.app.run') as mock_run:
        # Sauvegarde et modification temporaire de __name__
        original_name = flask_app.__name__
        flask_app.__name__ = "__main__"
        
        try:
            # Exécuter le code qui serait exécuté si app.py était lancé directement
            exec(open('app.py').read())
            
            # Vérifier que app.run() a été appelé
            mock_run.assert_called_once()
        finally:
            # Restaurer __name__
            flask_app.__name__ = original_name

if __name__ == '__main__':
    pytest.main(['-vs', __file__])
