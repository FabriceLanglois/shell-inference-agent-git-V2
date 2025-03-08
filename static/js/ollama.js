/**
 * Fonctions JavaScript pour la page de gestion Ollama
 * Version 2.0
 */

// Namespace pour éviter les conflits globaux
const OllamaManager = {
    // Configuration
    config: {
        modelGridColumns: 3,
        downloadTimeout: 600000,  // 10 minutes
        testTimeout: 60000,       // 1 minute
        defaultTemperature: 0.7,
        refreshInterval: 30000    // 30 secondes
    },
    
    // États
    state: {
        downloadingModel: false,
        testingModel: false,
        confirmCallback: null,
        refreshTimers: [],
        cachedModels: null,
        lastModelsFetch: 0,
        cacheDuration: 60000      // 1 minute
    },
    
    // Éléments DOM
    elements: {
        downloadModelBtn: null,
        modelInput: null,
        testModelBtn: null,
        testModelSelect: null,
        testPromptInput: null,
        testResult: null,
        testResultContent: null,
        modelGrid: null,
        modelLoadingSpinner: null,
        temperatureSlider: null,
        temperatureValue: null,
        confirmModal: null,
        confirmTitle: null,
        confirmText: null,
        confirmYesBtn: null,
        confirmNoBtn: null,
        closeConfirmModal: null,
        statsModelSelect: null,
        totalInferences: null,
        avgTime: null,
        avgTokens: null,
        memoryUsage: null
    },
    
    /**
     * Initialisation du module de gestion Ollama
     */
    init: function() {
        console.log('Initialisation du OllamaManager...');
        
        // Récupérer les éléments DOM
        this.cacheElements();
        
        // Initialiser les écouteurs d'événements
        this.initEventListeners();
        
        // Charger les modèles
        this.loadModelsList();
        
        // Configurer les rafraîchissements automatiques
        const timer = setInterval(() => this.loadInferenceStats(), this.config.refreshInterval);
        this.state.refreshTimers.push(timer);
        
        console.log('OllamaManager initialisé');
    },
    
    /**
     * Met en cache les éléments DOM
     */
    cacheElements: function() {
        this.elements.downloadModelBtn = document.getElementById('downloadModelBtn');
        this.elements.modelInput = document.getElementById('modelInput');
        this.elements.testModelBtn = document.getElementById('testModelBtn');
        this.elements.testModelSelect = document.getElementById('testModelSelect');
        this.elements.testPromptInput = document.getElementById('testPromptInput');
        this.elements.testResult = document.getElementById('testResult');
        this.elements.testResultContent = document.getElementById('testResultContent');
        this.elements.modelGrid = document.getElementById('modelGrid');
        this.elements.modelLoadingSpinner = document.getElementById('modelLoadingSpinner');
        this.elements.temperatureSlider = document.getElementById('temperatureSlider');
        this.elements.temperatureValue = document.getElementById('temperatureValue');
        this.elements.confirmModal = document.getElementById('confirmModal');
        this.elements.confirmTitle = document.getElementById('confirmTitle');
        this.elements.confirmText = document.getElementById('confirmText');
        this.elements.confirmYesBtn = document.getElementById('confirmYesBtn');
        this.elements.confirmNoBtn = document.getElementById('confirmNoBtn');
        this.elements.closeConfirmModal = document.getElementById('closeConfirmModal');
        this.elements.statsModelSelect = document.getElementById('statsModelSelect');
        this.elements.totalInferences = document.getElementById('totalInferences');
        this.elements.avgTime = document.getElementById('avgTime');
        this.elements.avgTokens = document.getElementById('avgTokens');
        this.elements.memoryUsage = document.getElementById('memoryUsage');
    },
    
    /**
     * Initialise les écouteurs d'événements
     */
    initEventListeners: function() {
        // Bouton de téléchargement de modèle
        if (this.elements.downloadModelBtn) {
            this.elements.downloadModelBtn.addEventListener('click', () => {
                if (this.elements.modelInput) {
                    this.downloadModel(this.elements.modelInput.value.trim());
                }
            });
        }
        
        // Input de modèle (pour détecter Entrée)
        if (this.elements.modelInput) {
            this.elements.modelInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !this.state.downloadingModel) {
                    e.preventDefault();
                    if (this.elements.downloadModelBtn) {
                        this.elements.downloadModelBtn.click();
                    }
                }
            });
        }
        
        // Bouton de test de modèle
        if (this.elements.testModelBtn) {
            this.elements.testModelBtn.addEventListener('click', () => {
                this.testModel();
            });
        }
        
        // Input de prompt (pour détecter Entrée)
        if (this.elements.testPromptInput) {
            this.elements.testPromptInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey && !this.state.testingModel) {
                    e.preventDefault();
                    if (this.elements.testModelBtn) {
                        this.elements.testModelBtn.click();
                    }
                }
            });
        }
        
        // Slider de température
        if (this.elements.temperatureSlider) {
            this.elements.temperatureSlider.addEventListener('input', () => {
                if (this.elements.temperatureValue) {
                    this.elements.temperatureValue.textContent = this.elements.temperatureSlider.value;
                }
            });
        }
        
        // Modal de confirmation
        if (this.elements.confirmYesBtn) {
            this.elements.confirmYesBtn.addEventListener('click', () => {
                if (this.state.confirmCallback) {
                    this.state.confirmCallback();
                }
                if (this.elements.confirmModal) {
                    this.elements.confirmModal.style.display = 'none';
                }
            });
        }
        
        if (this.elements.confirmNoBtn) {
            this.elements.confirmNoBtn.addEventListener('click', () => {
                if (this.elements.confirmModal) {
                    this.elements.confirmModal.style.display = 'none';
                }
            });
        }
        
        if (this.elements.closeConfirmModal) {
            this.elements.closeConfirmModal.addEventListener('click', () => {
                if (this.elements.confirmModal) {
                    this.elements.confirmModal.style.display = 'none';
                }
            });
        }
        
        // Sélecteur des statistiques
        if (this.elements.statsModelSelect) {
            this.elements.statsModelSelect.addEventListener('change', () => {
                this.loadInferenceStats();
            });
        }
        
        // Fermer le modal si on clique à l'extérieur
        window.addEventListener('click', (e) => {
            if (this.elements.confirmModal && e.target === this.elements.confirmModal) {
                this.elements.confirmModal.style.display = 'none';
            }
        });
    },
    
    /**
     * Charge la liste des modèles avec une gestion améliorée des erreurs
     * @param {string} [selectElementId='testModelSelect'] - ID de l'élément select à mettre à jour
     * @param {Function} [callback] - Fonction à exécuter après le chargement
     */
    loadModelsList: function(selectElementId = 'testModelSelect', callback) {
        AssistantIA.loadModelsList(selectElementId, (data) => {
            // Une fois les modèles chargés, afficher un message approprié
            if (this.elements.modelLoadingSpinner) {
                this.elements.modelLoadingSpinner.style.display = 'none';
            }
            
            if (!data || data.error || !data.models || data.models.length === 0) {
                // Aucun modèle disponible
                if (this.elements.modelGrid) {
                    this.elements.modelGrid.innerHTML = `
                        <div class="alert alert-warning" style="width: 100%;">
                            <i class="fas fa-exclamation-triangle"></i> Aucun modèle disponible. 
                            <div style="margin-top: 10px;">
                                Vérifiez que le service Ollama est en cours d'exécution en tapant 
                                <code>ollama serve</code> dans un terminal.
                            </div>
                            <div style="margin-top: 10px;">
                                Puis utilisez le formulaire ci-dessus pour télécharger un modèle.
                            </div>
                        </div>
                    `;
                }
                
                if (this.elements.downloadModelBtn) {
                    this.elements.downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle <small>(Vérifiez que Ollama est en cours d\'exécution)</small>';
                }
            } else {
                // Des modèles sont disponibles, continuer normalement
                this.loadModelsGrid(data);
            }
            
            // Exécuter le callback si présent
            if (callback && typeof callback === 'function') {
                callback(data);
            }
        });
    },
    
    /**
     * Charge la grille de modèles
     * @param {Object} data - Données contenant les modèles
     */
    loadModelsGrid: function(data) {
        if (!this.elements.modelGrid) return;
        
        if (this.elements.modelLoadingSpinner) {
            this.elements.modelLoadingSpinner.style.display = 'none';
        }
        
        if (data.error) {
            this.elements.modelGrid.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        if (!data.models || data.models.length === 0) {
            this.elements.modelGrid.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> Aucun modèle disponible. Utilisez le formulaire ci-dessus pour télécharger un modèle.
                </div>
            `;
            return;
        }
        
        // Construire la grille de modèles
        let gridHTML = '';
        
        data.models.forEach(model => {
            const isDefault = model.name === data.default;
            const size = (model.size / (1024 * 1024)).toFixed(0); // Convertir en MB
            
            gridHTML += `
                <div class="model-card" data-model="${model.name}">
                    <div class="model-name">${model.name} ${isDefault ? '<span class="badge badge-info">Défaut</span>' : ''}</div>
                    <div class="model-info">
                        <div><i class="fas fa-hdd"></i> Taille: ${AssistantIA.formatNumber(size)} MB</div>
                        <div><i class="fas fa-clock"></i> Modifié: ${AssistantIA.formatTimestamp(model.modified)}</div>
                    </div>
                    <div>
                        <span class="model-tag"><i class="fas fa-tag"></i> ollama</span>
                        ${this.getModelTags(model.name)}
                    </div>
                    <div class="model-actions">
                        <button class="btn test-model-btn" data-model="${model.name}">
                            <i class="fas fa-vial"></i> Tester
                        </button>
                        <button class="btn ${isDefault ? 'btn-danger delete-model-btn' : 'set-default-btn'}" data-model="${model.name}">
                            ${isDefault ? '<i class="fas fa-trash"></i> Supprimer' : '<i class="fas fa-check"></i> Définir par défaut'}
                        </button>
                    </div>
                </div>
            `;
        });
        
        // Mettre à jour la grille
        this.elements.modelGrid.innerHTML = gridHTML;
        
        // Ajouter les écouteurs d'événements pour les boutons
        document.querySelectorAll('.test-model-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const model = btn.getAttribute('data-model');
                if (this.elements.testModelSelect) {
                    this.elements.testModelSelect.value = model;
                    
                    // Faire défiler jusqu'au formulaire de test
                    const testCard = document.querySelector('.card:nth-child(2)');
                    if (testCard) {
                        testCard.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            });
        });
        
        document.querySelectorAll('.delete-model-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const model = btn.getAttribute('data-model');
                this.showConfirmModal(
                    'Suppression du modèle',
                    `Êtes-vous sûr de vouloir supprimer le modèle "${model}" ? Cette action est irréversible.`,
                    () => this.deleteModel(model)
                );
            });
        });
        
        document.querySelectorAll('.set-default-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const model = btn.getAttribute('data-model');
                this.setDefaultModel(model);
            });
        });
        
        // Ajouter les modèles au select des statistiques
        this.updateStatsModelSelect(data.models.map(m => m.name));
    },
    
    /**
     * Génère des tags basés sur le nom du modèle
     * @param {string} modelName - Nom du modèle
     * @returns {string} - HTML contenant les tags
     */
    getModelTags: function(modelName) {
        const tags = [];
        const lowerName = modelName.toLowerCase();
        
        // Modèles
        if (lowerName.includes('llama')) tags.push('llama');
        if (lowerName.includes('mistral')) tags.push('mistral');
        if (lowerName.includes('phi')) tags.push('phi');
        if (lowerName.includes('gemma')) tags.push('gemma');
        if (lowerName.includes('chat')) tags.push('chat');
        if (lowerName.includes('code')) tags.push('code');
        if (lowerName.includes('neural')) tags.push('neural');
        if (lowerName.includes('dolph')) tags.push('dolphin');
        if (lowerName.includes('qwen')) tags.push('qwen');
        if (lowerName.includes('falcon')) tags.push('falcon');
        if (lowerName.includes('stable')) tags.push('stable');
        if (lowerName.includes('wizard')) tags.push('wizard');
        if (lowerName.includes('mpt')) tags.push('mpt');
        if (lowerName.includes('openchat')) tags.push('openchat');
        if (lowerName.includes('solar')) tags.push('solar');
        
        // Tailles
        if (lowerName.includes('7b')) tags.push('7B');
        if (lowerName.includes('13b')) tags.push('13B');
        if (lowerName.includes('34b')) tags.push('34B');
        if (lowerName.includes('70b')) tags.push('70B');
        if (lowerName.includes('8b')) tags.push('8B');
        if (lowerName.includes('2b')) tags.push('2B');
        if (lowerName.includes('3b')) tags.push('3B');
        
        // Caractéristiques spéciales
        if (lowerName.includes('mini')) tags.push('mini');
        if (lowerName.includes('tiny')) tags.push('tiny');
        if (lowerName.includes('small')) tags.push('small');
        if (lowerName.includes('large')) tags.push('large');
        if (lowerName.includes('vision') || lowerName.includes('llava')) tags.push('vision');
        if (lowerName.includes('quantized') || lowerName.includes('-q')) tags.push('quantized');
        
        return tags.map(tag => `<span class="model-tag">${tag}</span>`).join('');
    },
    
    /**
     * Télécharge un modèle
     * @param {string} modelName - Nom du modèle à télécharger
     */
    downloadModel: function(modelName) {
        if (!modelName) {
            AssistantIA.showToast('Veuillez entrer un nom de modèle', null, 'warning');
            return;
        }
        
        // Éviter les téléchargements multiples
        if (this.state.downloadingModel) {
            AssistantIA.showToast('Un téléchargement est déjà en cours', null, 'warning');
            return;
        }
        
        this.state.downloadingModel = true;
        
        // Désactiver le bouton et montrer le chargement
        if (this.elements.downloadModelBtn) {
            this.elements.downloadModelBtn.disabled = true;
            this.elements.downloadModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Téléchargement...';
        }
        
        // Vérifier d'abord si Ollama est en cours d'exécution
        AssistantIA.isOllamaRunning().then(isRunning => {
            if (!isRunning) {
                throw new Error('Ollama n\'est pas en cours d\'exécution');
            }
            
            // Si Ollama est disponible, continuer avec le téléchargement
            return fetch(AssistantIA.API_ENDPOINTS.DOWNLOAD_MODEL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelName })
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Réactiver le bouton
            this.state.downloadingModel = false;
            
            if (this.elements.downloadModelBtn) {
                this.elements.downloadModelBtn.disabled = false;
                this.elements.downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle';
            }
            
            if (data.error) {
                AssistantIA.showToast(`Erreur: ${data.error}`, null, 'error');
                return;
            }
            
            if (data.success) {
                AssistantIA.showToast(`Modèle ${modelName} téléchargé avec succès`, null, 'success');
                
                // Recharger la liste des modèles
                this.loadModelsList('testModelSelect', this.loadModelsGrid.bind(this));
                
                // Vider l'input
                if (this.elements.modelInput) {
                    this.elements.modelInput.value = '';
                }
            } else {
                AssistantIA.showToast(`Erreur lors du téléchargement: ${data.error || 'Erreur inconnue'}`, null, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors du téléchargement:', error);
            
            this.state.downloadingModel = false;
            
            if (this.elements.downloadModelBtn) {
                this.elements.downloadModelBtn.disabled = false;
                this.elements.downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle';
            }
            
            if (error.message === 'Ollama n\'est pas en cours d\'exécution') {
                AssistantIA.showToast('Erreur: Ollama n\'est pas en cours d\'exécution. Exécutez "ollama serve" dans un terminal.', 5000, 'error');
                
                // Afficher un message d'erreur dans l'interface
                if (this.elements.modelGrid) {
                    this.elements.modelGrid.innerHTML = `
                        <div class="alert alert-danger" style="width: 100%;">
                            <i class="fas fa-exclamation-circle"></i> <strong>Erreur:</strong> Ollama n'est pas en cours d'exécution.
                            <div style="margin-top: 10px;">
                                Exécutez <code>ollama serve</code> dans un terminal, puis rafraîchissez cette page.
                            </div>
                        </div>
                    `;
                }
            } else {
                AssistantIA.showToast(`Erreur de connexion: ${error.message}`, null, 'error');
            }
        });
    },
    
    /**
     * Supprime un modèle
     * @param {string} modelName - Nom du modèle à supprimer
     */
    deleteModel: function(modelName) {
        fetch(AssistantIA.API_ENDPOINTS.DELETE_MODEL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                AssistantIA.showToast(`Erreur: ${data.error}`, null, 'error');
                return;
            }
            
            if (data.success) {
                AssistantIA.showToast(`Modèle ${modelName} supprimé avec succès`, null, 'success');
                
                // Recharger la liste des modèles
                this.loadModelsList('testModelSelect', this.loadModelsGrid.bind(this));
            } else {
                AssistantIA.showToast(`Erreur lors de la suppression: ${data.error || 'Erreur inconnue'}`, null, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la suppression:', error);
            AssistantIA.showToast(`Erreur de connexion: ${error.message}`, null, 'error');
        });
    },
    
    /**
     * Définit le modèle par défaut
     * @param {string} modelName - Nom du modèle à définir comme défaut
     */
    setDefaultModel: function(modelName) {
        AssistantIA.updateCurrentModel(modelName)
            .then(success => {
                if (success) {
                    AssistantIA.showToast(`Modèle ${modelName} défini comme modèle par défaut`, null, 'success');
                    
                    // Recharger la liste des modèles
                    this.loadModelsList('testModelSelect', this.loadModelsGrid.bind(this));
                } else {
                    AssistantIA.showToast(`Erreur lors de la définition du modèle par défaut`, null, 'error');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la définition du modèle par défaut:', error);
                AssistantIA.showToast(`Erreur: ${error.message}`, null, 'error');
            });
    },
    
    /**
     * Teste un modèle
     */
    testModel: function() {
        if (!this.elements.testModelSelect || !this.elements.testPromptInput || !this.elements.testResult || !this.elements.testResultContent) {
            return;
        }
        
        const model = this.elements.testModelSelect.value;
        const prompt = this.elements.testPromptInput.value.trim();
        const temperature = this.elements.temperatureSlider ? parseFloat(this.elements.temperatureSlider.value) : this.config.defaultTemperature;
        
        if (!model || model === 'loading' || model === 'none') {
            AssistantIA.showToast('Erreur: Aucun modèle sélectionné', null, 'error');
            return;
        }
        
        if (!prompt) {
            AssistantIA.showToast('Erreur: Le prompt est vide', null, 'error');
            return;
        }
        
        // Éviter les tests multiples
        if (this.state.testingModel) {
            AssistantIA.showToast('Un test est déjà en cours', null, 'warning');
            return;
        }
        
        this.state.testingModel = true;
        
        // Afficher le chargement
        this.elements.testResult.style.display = 'block';
        this.elements.testResultContent.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
                <div>Génération en cours avec le modèle "${model}"...</div>
            </div>
        `;
        
        // Désactiver le bouton
        if (this.elements.testModelBtn) {
            this.elements.testModelBtn.disabled = true;
            this.elements.testModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Test en cours...';
        }
        
        // Envoyer la requête de test
        fetch(AssistantIA.API_ENDPOINTS.TEST_MODEL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                prompt,
                temperature,
                max_tokens: 500
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Réactiver le bouton
            this.state.testingModel = false;
            
            if (this.elements.testModelBtn) {
                this.elements.testModelBtn.disabled = false;
                this.elements.testModelBtn.innerHTML = '<i class="fas fa-vial"></i> Tester le modèle';
            }
            
            if (data.error) {
                // Vérifier si l'erreur est liée à Ollama
                if (AssistantIA.isOllamaConnectionError(data.error)) {
                    this.elements.testResultContent.innerHTML = `
                        <div class="error">
                            <strong>Erreur:</strong> Le service Ollama n'est pas en cours d'exécution.<br>
                            Exécutez <code>ollama serve</code> dans un terminal, puis essayez à nouveau.
                        </div>
                    `;
                } else {
                    this.elements.testResultContent.innerHTML = `<div class="error">Erreur: ${data.error}</div>`;
                }
                return;
            }
            
            if (data.success) {
                // Afficher les méta-données de l'inférence
                const metaHTML = `
                    <div class="test-metadata">
                        <div class="meta-item" title="Durée de l'inférence">
                            <i class="fas fa-clock"></i> ${data.execution_time || '?'} sec
                        </div>
                        <div class="meta-item" title="Tokens générés">
                            <i class="fas fa-file-alt"></i> ${data.tokens || '?'} tokens
                        </div>
                        <div class="meta-item" title="Température">
                            <i class="fas fa-thermometer-half"></i> ${temperature}
                        </div>
                    </div>
                `;
                
                // Afficher le résultat
                this.elements.testResultContent.innerHTML = metaHTML + `<pre class="result-text">${data.response}</pre>`;
                
                // Mettre à jour les statistiques
                this.loadInferenceStats();
                
                // Définir ce modèle comme modèle par défaut si ce n'est pas déjà le cas
                AssistantIA.updateCurrentModel(model).catch(error => {
                    console.error('Erreur lors de la mise à jour du modèle par défaut:', error);
                });
            } else {
                this.elements.testResultContent.innerHTML = `<div class="error">Erreur: ${data.error || 'Erreur inconnue'}</div>`;
            }
        })
        .catch(error => {
            console.error('Erreur lors du test:', error);
            
            this.state.testingModel = false;
            
            if (this.elements.testModelBtn) {
                this.elements.testModelBtn.disabled = false;
                this.elements.testModelBtn.innerHTML = '<i class="fas fa-vial"></i> Tester le modèle';
            }
            
            if (this.elements.testResultContent) {
                this.elements.testResultContent.innerHTML = `<div class="error">Erreur de connexion: ${error.message}</div>`;
            }
        });
    },
    
    /**
     * Charge les statistiques d'inférence
     */
    loadInferenceStats: function() {
        if (!this.elements.totalInferences || !this.elements.avgTime || !this.elements.avgTokens || !this.elements.memoryUsage) {
            return;
        }
        
        fetch(AssistantIA.API_ENDPOINTS.STATS_INFERENCE)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Erreur lors du chargement des statistiques:', data.error);
                    this.updateStatsDisplay(0, 0, 0, 0);
                    return;
                }
                
                if (!data.history || data.history.length === 0) {
                    this.updateStatsDisplay(0, 0, 0, 0);
                    return;
                }
                
                // Filtrer par modèle si nécessaire
                const selectedModel = this.elements.statsModelSelect ? this.elements.statsModelSelect.value : 'all';
                let filteredHistory = data.history;
                
                if (selectedModel !== 'all') {
                    filteredHistory = data.history.filter(entry => entry.model === selectedModel);
                }
                
                // Calculer les statistiques
                const totalCount = filteredHistory.length;
                const totalTokens = filteredHistory.reduce((sum, entry) => sum + (entry.output_length || 0), 0);
                const totalTime = filteredHistory.reduce((sum, entry) => sum + (entry.execution_time || 0), 0);
                
                // Mettre à jour l'affichage
                const avgTimeValue = totalCount > 0 ? (totalTime / totalCount).toFixed(2) : '0';
                const avgTokensValue = totalCount > 0 ? Math.round(totalTokens / totalCount) : '0';
                
                // Estimation de la mémoire utilisée (valeur approximative)
                const estimatedMemory = totalCount > 0 ? Math.round((totalTokens / totalCount) * 1.5) : '0';
                
                this.updateStatsDisplay(totalCount, avgTimeValue, avgTokensValue, estimatedMemory);
            })
            .catch(error => {
                console.error('Erreur lors du chargement des statistiques:', error);
                this.updateStatsDisplay(0, 0, 0, 0);
            });
    },
    
    /**
     * Met à jour l'affichage des statistiques
     * @param {number} count - Nombre total d'inférences
     * @param {string} time - Temps moyen d'exécution
     * @param {string} tokens - Nombre moyen de tokens
     * @param {string} memory - Utilisation mémoire estimée
     */
    updateStatsDisplay: function(count, time, tokens, memory) {
        if (this.elements.totalInferences) {
            this.elements.totalInferences.textContent = AssistantIA.formatNumber(count);
        }
        
        if (this.elements.avgTime) {
            this.elements.avgTime.textContent = time;
        }
        
        if (this.elements.avgTokens) {
            this.elements.avgTokens.textContent = tokens;
        }
        
        if (this.elements.memoryUsage) {
            this.elements.memoryUsage.textContent = AssistantIA.formatNumber(memory);
        }
    },
    
    /**
     * Met à jour le select des statistiques
     * @param {string[]} models - Liste des noms de modèles
     */
    updateStatsModelSelect: function(models) {
        if (!this.elements.statsModelSelect) return;
        
        // Conserver l'option "Tous les modèles"
        const selectedValue = this.elements.statsModelSelect.value;
        this.elements.statsModelSelect.innerHTML = '<option value="all">Tous les modèles</option>';
        
        // Ajouter les modèles
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            this.elements.statsModelSelect.appendChild(option);
        });
        
        // Restaurer la sélection si possible
        if (selectedValue) {
            for (let i = 0; i < this.elements.statsModelSelect.options.length; i++) {
                if (this.elements.statsModelSelect.options[i].value === selectedValue) {
                    this.elements.statsModelSelect.selectedIndex = i;
                    break;
                }
            }
        }
        
        // Charger les statistiques
        this.loadInferenceStats();
    },
    
    /**
     * Affiche le modal de confirmation
     * @param {string} title - Titre du modal
     * @param {string} text - Texte du modal
     * @param {Function} callback - Fonction à exécuter si l'utilisateur confirme
     */
    showConfirmModal: function(title, text, callback) {
        if (!this.elements.confirmModal || !this.elements.confirmTitle || !this.elements.confirmText) {
            return;
        }
        
        this.elements.confirmTitle.textContent = title;
        this.elements.confirmText.textContent = text;
        this.state.confirmCallback = callback;
        this.elements.confirmModal.style.display = 'block';
    },
    
    /**
     * Nettoie les ressources utilisées par le module
     */
    cleanup: function() {
        // Arrêter les timers de rafraîchissement
        this.state.refreshTimers.forEach(timer => clearInterval(timer));
        this.state.refreshTimers = [];
    }
};

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    OllamaManager.init();
});

// S'assurer que les ressources sont nettoyées quand la page est déchargée
window.addEventListener('beforeunload', function() {
    OllamaManager.cleanup();
});
