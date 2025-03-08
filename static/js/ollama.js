/**
 * Fonctions JavaScript pour la page de gestion Ollama
 * Version améliorée avec meilleure gestion des erreurs et de l'expérience utilisateur
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const downloadModelBtn = document.getElementById('downloadModelBtn');
    const modelInput = document.getElementById('modelInput');
    const testModelBtn = document.getElementById('testModelBtn');
    const testModelSelect = document.getElementById('testModelSelect');
    const testPromptInput = document.getElementById('testPromptInput');
    const testResult = document.getElementById('testResult');
    const testResultContent = document.getElementById('testResultContent');
    const modelGrid = document.getElementById('modelGrid');
    const modelLoadingSpinner = document.getElementById('modelLoadingSpinner');
    const temperatureSlider = document.getElementById('temperatureSlider');
    const temperatureValue = document.getElementById('temperatureValue');
    const confirmModal = document.getElementById('confirmModal');
    const confirmTitle = document.getElementById('confirmTitle');
    const confirmText = document.getElementById('confirmText');
    const confirmYesBtn = document.getElementById('confirmYesBtn');
    const confirmNoBtn = document.getElementById('confirmNoBtn');
    const closeConfirmModal = document.getElementById('closeConfirmModal');
    const statsModelSelect = document.getElementById('statsModelSelect');
    const totalInferences = document.getElementById('totalInferences');
    const avgTime = document.getElementById('avgTime');
    const avgTokens = document.getElementById('avgTokens');
    const memoryUsage = document.getElementById('memoryUsage');
    
    // Callback de confirmation
    let confirmCallback = null;
    
    // État d'avancement du téléchargement
    let downloadInProgress = false;
    
    // Charger les modèles avec une gestion améliorée des erreurs
    loadModelsList('testModelSelect', function(data) {
        // Une fois les modèles chargés, afficher un message approprié
        const modelGrid = document.getElementById('modelGrid');
        const modelLoadingSpinner = document.getElementById('modelLoadingSpinner');
        
        if (modelLoadingSpinner) {
            modelLoadingSpinner.style.display = 'none';
        }
        
        if (!data || data.error || !data.models || data.models.length === 0) {
            // Aucun modèle disponible
            if (modelGrid) {
                // Vérifier si l'erreur est liée à la connexion Ollama
                if (data && data.error && (data.error.includes("localhost:11434") || data.error.includes("connection refused"))) {
                    modelGrid.innerHTML = `
                        <div class="alert alert-danger" style="width: 100%;">
                            <i class="fas fa-exclamation-circle"></i> <strong>Erreur:</strong> Le service Ollama n'est pas en cours d'exécution.
                            <div style="margin-top: 10px;">
                                Pour démarrer Ollama, exécutez cette commande dans un terminal:
                                <pre style="margin-top: 10px; background-color: #1e293b; padding: 10px; border-radius: 5px;">ollama serve</pre>
                            </div>
                            <div style="margin-top: 10px;">
                                <button id="refreshAfterStart" class="btn" style="margin-top: 10px;">
                                    <i class="fas fa-sync-alt"></i> Rafraîchir après démarrage
                                </button>
                            </div>
                        </div>
                    `;
                    
                    // Ajouter un écouteur d'événement pour le bouton de rafraîchissement
                    const refreshButton = document.getElementById('refreshAfterStart');
                    if (refreshButton) {
                        refreshButton.addEventListener('click', function() {
                            location.reload();
                        });
                    }
                } else {
                    modelGrid.innerHTML = `
                        <div class="alert alert-warning" style="width: 100%;">
                            <i class="fas fa-exclamation-triangle"></i> Aucun modèle disponible. 
                            <div style="margin-top: 10px;">
                                Utilisez le formulaire ci-dessus pour télécharger un modèle.
                            </div>
                            <div style="margin-top: 10px;">
                                Suggestions: llama3, mistral, phi3:mini, gemma:2b
                            </div>
                        </div>
                    `;
                }
            }
            
            // Mettre à jour le bouton de téléchargement
            const downloadModelBtn = document.getElementById('downloadModelBtn');
            if (downloadModelBtn) {
                if (data && data.error && (data.error.includes("localhost:11434") || data.error.includes("connection refused"))) {
                    downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle <small>(Vérifiez que Ollama est en cours d\'exécution)</small>';
                    downloadModelBtn.disabled = true;
                } else {
                    downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle';
                    downloadModelBtn.disabled = false;
                }
            }
        } else {
            // Des modèles sont disponibles, continuer normalement
            loadModelsGrid(data);
        }
    });
    
    // Fonction pour charger la grille de modèles
    function loadModelsGrid(data) {
        if (!modelGrid) return;
        
        if (modelLoadingSpinner) {
            modelLoadingSpinner.style.display = 'none';
        }
        
        if (data.error) {
            modelGrid.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        if (!data.models || data.models.length === 0) {
            modelGrid.innerHTML = `
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
                        <div><i class="fas fa-hdd"></i> Taille: ${formatNumber(size)} MB</div>
                        <div><i class="fas fa-clock"></i> Modifié: ${formatTimestamp(model.modified)}</div>
                    </div>
                    <div>
                        <span class="model-tag"><i class="fas fa-tag"></i> ollama</span>
                        ${getModelTags(model.name)}
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
        modelGrid.innerHTML = gridHTML;
        
        // Ajouter les écouteurs d'événements pour les boutons
        document.querySelectorAll('.test-model-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const model = this.getAttribute('data-model');
                testModelSelect.value = model;
                
                // Faire défiler jusqu'au formulaire de test
                document.querySelector('.card:nth-child(2)').scrollIntoView({ behavior: 'smooth' });
                
                // Mettre en évidence le formulaire de test
                highlightElement(document.querySelector('.card:nth-child(2)'));
            });
        });
        
        document.querySelectorAll('.delete-model-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const model = this.getAttribute('data-model');
                showConfirmModal(
                    'Suppression du modèle',
                    `Êtes-vous sûr de vouloir supprimer le modèle "${model}" ? Cette action est irréversible.`,
                    () => deleteModel(model)
                );
            });
        });
        
        document.querySelectorAll('.set-default-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const model = this.getAttribute('data-model');
                setDefaultModel(model);
            });
        });
        
        // Ajouter les modèles au select des statistiques
        updateStatsModelSelect(data.models.map(m => m.name));
    }
    
    // Nouvelle fonction: met en évidence un élément temporairement
    function highlightElement(element, duration = 2000) {
        if (!element) return;
        
        // Sauvegarder le style original
        const originalBoxShadow = element.style.boxShadow;
        const originalTransition = element.style.transition;
        
        // Appliquer la mise en évidence
        element.style.transition = 'box-shadow 0.3s ease-in-out';
        element.style.boxShadow = '0 0 15px var(--primary-color)';
        
        // Restaurer le style original après la durée spécifiée
        setTimeout(() => {
            element.style.boxShadow = originalBoxShadow;
            setTimeout(() => {
                element.style.transition = originalTransition;
            }, 300);
        }, duration);
    }
    
    // Fonction pour obtenir les tags basés sur le nom du modèle
    function getModelTags(modelName) {
        const tags = [];
        const lowerName = modelName.toLowerCase();
        
        if (lowerName.includes('llama')) tags.push('llama');
        if (lowerName.includes('mistral')) tags.push('mistral');
        if (lowerName.includes('phi')) tags.push('phi');
        if (lowerName.includes('gemma')) tags.push('gemma');
        if (lowerName.includes('chat')) tags.push('chat');
        if (lowerName.includes('code')) tags.push('code');
        
        // Ajouter des tags basés sur la taille du modèle si elle est dans le nom
        if (lowerName.includes('7b')) tags.push('7B');
        if (lowerName.includes('13b')) tags.push('13B');
        if (lowerName.includes('34b')) tags.push('34B');
        if (lowerName.includes('8b')) tags.push('8B');
        if (lowerName.includes('2b')) tags.push('2B');
        
        // Ajouter un tag "mini" pour les petits modèles
        if (lowerName.includes('mini')) tags.push('mini');
        
        return tags.map(tag => `<span class="model-tag">${tag}</span>`).join('');
    }
    
    // Fonction pour télécharger un modèle
    function downloadModel(modelName) {
        if (!modelName) {
            showToast('Veuillez entrer un nom de modèle');
            return;
        }
        
        // Éviter les téléchargements simultanés
        if (downloadInProgress) {
            showToast('Un téléchargement est déjà en cours, veuillez patienter');
            return;
        }
        
        // Désactiver le bouton et montrer le chargement
        downloadModelBtn.disabled = true;
        downloadModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Téléchargement en cours...';
        downloadInProgress = true;
        
        // Afficher une notification
        showToast(`Démarrage du téléchargement de ${modelName}. Cette opération peut prendre plusieurs minutes.`, 5000);
        
        // Vérifier d'abord si Ollama est en cours d'exécution
        fetch('/api/models')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(checkData => {
                if (checkData.error && (checkData.error.includes('connection refused') || checkData.error.includes('localhost:11434'))) {
                    throw new Error('Ollama n\'est pas en cours d\'exécution');
                }
                
                // Si Ollama est disponible, continuer avec le téléchargement
                return fetch('/api/download-model', {
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
                downloadModelBtn.disabled = false;
                downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle';
                downloadInProgress = false;
                
                if (data.error) {
                    showErrorToast(`Erreur: ${data.error}`, 5000);
                    return;
                }
                
                if (data.success) {
                    showToast(`Modèle ${modelName} téléchargé avec succès`);
                    
                    // Recharger la liste des modèles
                    loadModelsList('testModelSelect', loadModelsGrid);
                    
                    // Vider l'input
                    modelInput.value = '';
                    
                    // Mettre à jour les statistiques
                    loadInferenceStats();
                } else {
                    showErrorToast(`Erreur lors du téléchargement: ${data.error || 'Erreur inconnue'}`, 5000);
                }
            })
            .catch(error => {
                console.error('Erreur lors du téléchargement:', error);
                downloadModelBtn.disabled = false;
                downloadModelBtn.innerHTML = '<i class="fas fa-cloud-download-alt"></i> Télécharger le modèle';
                downloadInProgress = false;
                
                if (error.message === 'Ollama n\'est pas en cours d\'exécution') {
                    showErrorToast('Erreur: Ollama n\'est pas en cours d\'exécution. Exécutez "ollama serve" dans un terminal.', 5000);
                    
                    // Afficher un message d'erreur dans l'interface
                    const modelGrid = document.getElementById('modelGrid');
                    if (modelGrid) {
                        modelGrid.innerHTML = `
                            <div class="alert alert-danger" style="width: 100%;">
                                <i class="fas fa-exclamation-circle"></i> <strong>Erreur:</strong> Ollama n'est pas en cours d'exécution.
                                <div style="margin-top: 10px;">
                                    Exécutez <code>ollama serve</code> dans un terminal, puis rafraîchissez cette page.
                                </div>
                                <div style="margin-top: 10px;">
                                    <button id="refreshAfterStart" class="btn" style="margin-top: 10px;">
                                        <i class="fas fa-sync-alt"></i> Rafraîchir après démarrage
                                    </button>
                                </div>
                            </div>
                        `;
                        
                        // Ajouter un écouteur d'événement pour le bouton de rafraîchissement
                        const refreshButton = document.getElementById('refreshAfterStart');
                        if (refreshButton) {
                            refreshButton.addEventListener('click', function() {
                                location.reload();
                            });
                        }
                    }
                } else {
                    showErrorToast(`Erreur de connexion: ${error.message}`, 5000);
                }
            });
    }
    
    // Fonction pour supprimer un modèle
    function deleteModel(modelName) {
        // Afficher un indicateur de chargement
        const card = document.querySelector(`.model-card[data-model="${modelName}"]`);
        if (card) {
            card.style.opacity = '0.7';
            card.innerHTML += `
                <div style="position:absolute; top:0; left:0; right:0; bottom:0; display:flex; justify-content:center; align-items:center; background:rgba(0,0,0,0.3); border-radius:8px;">
                    <div class="loading-spinner"></div>
                </div>
            `;
        }
        
        fetch('/api/delete-model', {
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
                showErrorToast(`Erreur: ${data.error}`, 5000);
                
                // Restaurer la carte en cas d'erreur
                if (card) {
                    // Recharger la grille complète pour éviter des problèmes d'affichage
                    loadModelsList('testModelSelect', loadModelsGrid);
                }
                return;
            }
            
            if (data.success) {
                showToast(`Modèle ${modelName} supprimé avec succès`);
                
                // Recharger la liste des modèles
                loadModelsList('testModelSelect', loadModelsGrid);
                
                // Mettre à jour les statistiques
                loadInferenceStats();
            } else {
                showErrorToast(`Erreur lors de la suppression: ${data.error || 'Erreur inconnue'}`, 5000);
                
                // Recharger la grille en cas d'erreur
                loadModelsList('testModelSelect', loadModelsGrid);
            }
        })
        .catch(error => {
            console.error('Erreur lors de la suppression:', error);
            showErrorToast(`Erreur de connexion: ${error.message}`, 5000);
            
            // Recharger la grille en cas d'erreur
            loadModelsList('testModelSelect', loadModelsGrid);
        });
    }
    
    // Fonction pour définir le modèle par défaut
    function setDefaultModel(modelName) {
        // Afficher un indicateur de chargement
        const allButtons = document.querySelectorAll('.set-default-btn, .delete-model-btn');
        allButtons.forEach(btn => {
            btn.disabled = true;
        });
        
        const currentButton = document.querySelector(`.model-card[data-model="${modelName}"] .set-default-btn`);
        if (currentButton) {
            currentButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Configuration...';
        }
        
        fetch('/api/set-default-model', {
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
                showErrorToast(`Erreur: ${data.error}`, 5000);
                
                // Réactiver les boutons
                allButtons.forEach(btn => {
                    btn.disabled = false;
                });
                
                if (currentButton) {
                    currentButton.innerHTML = '<i class="fas fa-check"></i> Définir par défaut';
                }
                return;
            }
            
            if (data.success) {
                showToast(`Modèle ${modelName} défini comme modèle par défaut`);
                
                // Recharger la liste des modèles
                loadModelsList('testModelSelect', loadModelsGrid);
                
                // Mettre à jour l'affichage du modèle actuel
                loadCurrentModel();
            } else {
                showErrorToast(`Erreur lors de la définition du modèle par défaut: ${data.error || 'Erreur inconnue'}`, 5000);
                
                // Réactiver les boutons
                allButtons.forEach(btn => {
                    btn.disabled = false;
                });
                
                if (currentButton) {
                    currentButton.innerHTML = '<i class="fas fa-check"></i> Définir par défaut';
                }
            }
        })
        .catch(error => {
            console.error('Erreur lors de la définition du modèle par défaut:', error);
            showErrorToast(`Erreur de connexion: ${error.message}`, 5000);
            
            // Réactiver les boutons
            allButtons.forEach(btn => {
                btn.disabled = false;
            });
            
            if (currentButton) {
                currentButton.innerHTML = '<i class="fas fa-check"></i> Définir par défaut';
            }
        });
    }
    
    // Fonction pour tester un modèle avec retour d'information amélioré
    function testModel() {
        const model = testModelSelect.value;
        const prompt = testPromptInput.value.trim();
        const temperature = temperatureSlider.value;
        
        if (!model || model === 'loading' || model === 'none') {
            showErrorToast('Erreur: Aucun modèle sélectionné');
            return;
        }
        
        if (!prompt) {
            showErrorToast('Erreur: Le prompt est vide');
            return;
        }
        
        // Afficher le chargement
        testResult.style.display = 'block';
        testResultContent.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
                Génération en cours avec le modèle "${model}"...
                <div style="font-size: 12px; margin-top: 10px;">
                    Cette opération peut prendre plusieurs secondes selon la complexité du prompt.
                </div>
            </div>
        `;
        
        // Désactiver le bouton
        testModelBtn.disabled = true;
        testModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Test en cours...';
        
        // Faire défiler jusqu'au résultat
        testResult.scrollIntoView({ behavior: 'smooth' });
        
        // Envoyer la requête de test
        fetch('/api/test-model', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                prompt,
                temperature: parseFloat(temperature),
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
            testModelBtn.disabled = false;
            testModelBtn.innerHTML = '<i class="fas fa-vial"></i> Tester le modèle';
            
            if (data.error) {
                // Vérifier si l'erreur est liée à Ollama
                if (data.error.includes('localhost:11434') || data.error.includes('connection refused')) {
                    testResultContent.innerHTML = `
                        <div class="error">
                            <strong>Erreur:</strong> Le service Ollama n'est pas en cours d'exécution.<br>
                            Exécutez <code>ollama serve</code> dans un terminal, puis essayez à nouveau.
                            <div style="margin-top: 15px;">
                                <button id="refreshAfterStart" class="btn">
                                    <i class="fas fa-sync-alt"></i> Rafraîchir après démarrage
                                </button>
                            </div>
                        </div>
                    `;
                    
                    // Ajouter un écouteur d'événement pour le bouton de rafraîchissement
                    const refreshButton = document.getElementById('refreshAfterStart');
                    if (refreshButton) {
                        refreshButton.addEventListener('click', function() {
                            location.reload();
                        });
                    }
                } else if (data.error.includes('not found') && data.error.includes(model)) {
                    testResultContent.innerHTML = `
                        <div class="error">
                            <strong>Erreur:</strong> Le modèle "${model}" n'est pas disponible.<br>
                            Téléchargez-le d'abord à l'aide du formulaire en haut de la page.
                        </div>
                    `;
                } else {
                    testResultContent.innerHTML = `<div class="error">Erreur: ${data.error}</div>`;
                }
                return;
            }
            
            if (data.success) {
                // Afficher le résultat
                testResultContent.innerHTML = `
                    <div style="white-space: pre-wrap; color: var(--text-color);">${data.response}</div>
                    <div style="margin-top: 15px; font-size: 12px; color: var(--text-secondary); display: flex; justify-content: space-between;">
                        <span>Tokens générés: ~${data.tokens || 'N/A'}</span>
                        <button class="btn" style="padding: 5px 10px; font-size: 12px;" onclick="copyToClipboard('${escapeHtml(data.response)}')">
                            <i class="fas fa-copy"></i> Copier
                        </button>
                    </div>
                `;
                
                // Mettre à jour les statistiques
                loadInferenceStats();
                
                // Définir ce modèle comme modèle par défaut si ce n'est pas déjà le cas
                const currentModelElement = document.getElementById('currentModel');
                if (currentModelElement && !currentModelElement.textContent.includes(model)) {
                    // Mettre à jour le modèle par défaut
                    fetch('/api/set-default-model', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ model })
                    })
                    .then(response => response.json())
                    .then(updateData => {
                        if (updateData.success) {
                            // Mettre à jour l'affichage
                            currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: ${model}`;
                            
                            // Recharger la liste des modèles pour mettre à jour l'interface
                            loadModelsList('testModelSelect', loadModelsGrid);
                        }
                    })
                    .catch(error => {
                        console.error('Erreur lors de la mise à jour du modèle par défaut:', error);
                    });
                }
            } else {
                testResultContent.innerHTML = `<div class="error">Erreur: ${data.error || 'Erreur inconnue'}</div>`;
            }
        })
        .catch(error => {
            console.error('Erreur lors du test:', error);
            testModelBtn.disabled = false;
            testModelBtn.innerHTML = '<i class="fas fa-vial"></i> Tester le modèle';
            testResultContent.innerHTML = `<div class="error">Erreur de connexion: ${error.message}</div>`;
        });
    }
    
    // Fonction pour charger les statistiques d'inférence
    function loadInferenceStats() {
        // Afficher un indicateur de chargement dans les éléments statistiques
        totalInferences.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        avgTime.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        avgTokens.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        memoryUsage.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        fetch('/api/stats/inference-history')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Erreur lors du chargement des statistiques:', data.error);
                    totalInferences.textContent = 'Erreur';
                    avgTime.textContent = 'Erreur';
                    avgTokens.textContent = 'Erreur';
                    memoryUsage.textContent = 'Erreur';
                    return;
                }
                
                if (!data.history || data.history.length === 0) {
                    totalInferences.textContent = '0';
                    avgTime.textContent = '0';
                    avgTokens.textContent = '0';
                    memoryUsage.textContent = '0';
                    return;
                }
                
                // Filtrer par modèle si nécessaire
                const selectedModel = statsModelSelect.value;
                let filteredHistory = data.history;
                
                if (selectedModel !== 'all') {
                    filteredHistory = data.history.filter(entry => entry.model === selectedModel);
                }
                
                // Calculer les statistiques
                const totalCount = filteredHistory.length;
                const totalTokens = filteredHistory.reduce((sum, entry) => sum + (entry.output_length || 0), 0);
                const totalTime = filteredHistory.reduce((sum, entry) => sum + (entry.execution_time || 0), 0);
                
                // Mettre à jour l'affichage
                totalInferences.textContent = formatNumber(totalCount);
                avgTime.textContent = (totalCount > 0 ? (totalTime / totalCount).toFixed(2) : '0');
                avgTokens.textContent = (totalCount > 0 ? Math.round(totalTokens / totalCount) : '0');
                
                // Estimation de la mémoire utilisée (valeur fictive)
                const estimatedMemory = (totalCount > 0 ? Math.round((totalTokens / totalCount) * 1.5) : '0');
                memoryUsage.textContent = formatNumber(estimatedMemory);
                
                // Mettre à jour les graphiques (à implémenter)
                updateCharts(filteredHistory);
            })
            .catch(error => {
                console.error('Erreur lors du chargement des statistiques:', error);
                totalInferences.textContent = 'Erreur';
                avgTime.textContent = 'Erreur';
                avgTokens.textContent = 'Erreur';
                memoryUsage.textContent = 'Erreur';
            });
    }
    
    // Fonction pour mettre à jour le select des statistiques
    function updateStatsModelSelect(models) {
        if (!statsModelSelect) return;
        
        // Conserver l'option "Tous les modèles"
        const currentValue = statsModelSelect.value;
        statsModelSelect.innerHTML = '<option value="all">Tous les modèles</option>';
        
        // Ajouter les modèles
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            statsModelSelect.appendChild(option);
        });
        
        // Restaurer la sélection précédente si possible
        if (currentValue && models.includes(currentValue)) {
            statsModelSelect.value = currentValue;
        }
        
        // Charger les statistiques
        loadInferenceStats();
    }
    
    // Fonction pour afficher le modal de confirmation
    function showConfirmModal(title, text, callback) {
        confirmTitle.textContent = title;
        confirmText.textContent = text;
        confirmCallback = callback;
        confirmModal.style.display = 'block';
    }
    
    // Fonction pour mettre à jour les graphiques (à implémenter)
    function updateCharts(history) {
        // Cette fonction pourrait être implémentée ultérieurement pour ajouter des graphiques
        // avec une bibliothèque comme Chart.js
        console.log('Mise à jour des graphiques avec', history.length, 'entrées d\'historique');
    }
    
    // Suggérer des modèles populaires dans le champ de texte
    function suggestModels() {
        if (!modelInput) return;
        
        const popularModels = ['llama3', 'mistral', 'phi3:mini', 'gemma:2b', 'codegemma'];
        
        // Ajouter des suggestions lorsque le champ est vide
        modelInput.addEventListener('focus', function() {
            if (!this.value) {
                const datalist = document.createElement('datalist');
                datalist.id = 'modelSuggestions';
                
                popularModels.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    datalist.appendChild(option);
                });
                
                // Ajouter la datalist au document s'il n'existe pas déjà
                if (!document.getElementById('modelSuggestions')) {
                    document.body.appendChild(datalist);
                    this.setAttribute('list', 'modelSuggestions');
                }
            }
        });
    }
    
    // Fonction pour ajouter un message d'aide sous le formulaire de test
    function addTestHelpMessage() {
        const testFormGroup = testModelBtn.parentElement;
        if (!testFormGroup) return;
        
        const helpMessage = document.createElement('div');
        helpMessage.className = 'help-message';
        helpMessage.style.marginTop = '10px';
        helpMessage.style.fontSize = '12px';
        helpMessage.style.color = 'var(--text-color)';
        helpMessage.style.opacity = '0.7';
        helpMessage.innerHTML = `
            <i class="fas fa-info-circle"></i> Astuce: Après un test réussi, le modèle sera automatiquement défini comme modèle par défaut.
        `;
        
        testFormGroup.appendChild(helpMessage);
    }
    
    // Événements pour les boutons
    downloadModelBtn.addEventListener('click', function() {
        downloadModel(modelInput.value.trim());
    });
    
    testModelBtn.addEventListener('click', testModel);
    
    // Permettre d'appuyer sur Entrée dans le champ de test pour lancer le test
    testPromptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            testModel();
        }
    });
    
    // Ajouter une indication pour le raccourci
    testPromptInput.title = 'Appuyez sur Ctrl+Entrée pour tester rapidement';
    
    // Gestion du slider de température
    temperatureSlider.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Gestion des modals de confirmation
    confirmYesBtn.addEventListener('click', function() {
        if (confirmCallback) {
            confirmCallback();
        }
        confirmModal.style.display = 'none';
    });
    
    confirmNoBtn.addEventListener('click', function() {
        confirmModal.style.display = 'none';
    });
    
    closeConfirmModal.addEventListener('click', function() {
        confirmModal.style.display = 'none';
    });
    
    // Fermer le modal si on clique à l'extérieur
    window.addEventListener('click', function(e) {
        if (e.target === confirmModal) {
            confirmModal.style.display = 'none';
        }
    });
    
    // Événement pour le select des statistiques
    statsModelSelect.addEventListener('change', loadInferenceStats);
    
    // Charger les statistiques initiales
    loadInferenceStats();
    
    // Activer les suggestions de modèles
    suggestModels();
    
    // Ajouter le message d'aide au formulaire de test
    addTestHelpMessage();
    
    // Ajouter la possibilité de presser Entrée dans le champ de modèle pour démarrer le téléchargement
    modelInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && this.value.trim()) {
            downloadModel(this.value.trim());
        }
    });
});