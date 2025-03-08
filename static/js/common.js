/**
 * Fonctions JavaScript partagées pour l'Assistant IA
 * Version 2.0
 */

// Namespace pour éviter les conflits globaux
const AssistantIA = {
    // Constantes
    API_ENDPOINTS: {
        MODELS: '/api/models',
        CURRENT_MODEL: '/api/current-model',
        SET_DEFAULT_MODEL: '/api/set-default-model',
        DOWNLOAD_MODEL: '/api/download-model',
        DELETE_MODEL: '/api/delete-model',
        TEST_MODEL: '/api/test-model',
        GPU_INFO: '/api/gpu-info',
        STATS_INFERENCE: '/api/stats/inference-history',
        STATS_MODEL_USAGE: '/api/stats/model-usage',
        STATS_PERFORMANCE: '/api/stats/performance'
    },
    
    // Configuration
    config: {
        currentModelName: '',
        toastDuration: 3000,
        autoRefreshGpu: true,
        refreshInterval: 30000 // 30 secondes
    },
    
    // Cache des données
    cache: {
        models: null,
        lastModelsFetch: 0,
        cacheDuration: 60000 // 1 minute
    },
    
    // États
    state: {
        isDarkTheme: true,
        isOllamaRunning: null,
        refreshTimers: []
    },
    
    /**
     * Initialisation du module commun
     */
    init: function() {
        console.log('Initialisation de AssistantIA...');
        
        // Récupérer le thème
        this.initTheme();
        
        // Initialiser les tooltips
        this.initTooltips();
        
        // Charger les infos du modèle courant
        this.loadCurrentModel();
        
        // Charger les informations GPU
        this.loadGpuInfo();
        
        // Configurer les rafraîchissements automatiques
        if (this.config.autoRefreshGpu) {
            const timer = setInterval(() => this.loadGpuInfo(), this.config.refreshInterval);
            this.state.refreshTimers.push(timer);
        }
        
        console.log('AssistantIA initialisé');
    },
    
    /**
     * Initialisation du thème
     */
    initTheme: function() {
        // Récupérer le thème sauvegardé ou utiliser le thème sombre par défaut
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.state.isDarkTheme = (savedTheme === 'dark');
        
        // Appliquer le thème
        document.body.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
        
        // Ajouter l'écouteur pour le bouton de changement de thème
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    },
    
    /**
     * Bascule entre les thèmes clair et sombre
     */
    toggleTheme: function() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Mettre à jour l'état
        this.state.isDarkTheme = (newTheme === 'dark');
        
        // Appliquer le nouveau thème
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
        
        // Afficher un toast
        this.showToast(`Thème ${newTheme === 'dark' ? 'sombre' : 'clair'} activé`);
    },
    
    /**
     * Met à jour l'icône du bouton de thème
     * @param {string} theme - Le thème actuel ('dark' ou 'light')
     */
    updateThemeIcon: function(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' 
                ? '<i class="fas fa-sun"></i>' 
                : '<i class="fas fa-moon"></i>';
            
            // Mettre à jour l'attribut title pour l'accessibilité
            themeToggle.setAttribute('title', 
                theme === 'dark' ? 'Passer au thème clair' : 'Passer au thème sombre'
            );
            
            // Mettre à jour ARIA pour l'accessibilité
            themeToggle.setAttribute('aria-label', 
                theme === 'dark' ? 'Passer au thème clair' : 'Passer au thème sombre'
            );
        }
    },
    
    /**
     * Initialise les tooltips
     */
    initTooltips: function() {
        document.querySelectorAll('[title]').forEach(element => {
            const title = element.getAttribute('title');
            if (!title) return;
            
            // Ajouter l'attribut ARIA pour l'accessibilité
            element.setAttribute('aria-label', title);
            
            // Créer une fonction de gestion au survol
            const showTooltip = function(e) {
                // Vérifier si un tooltip existe déjà
                const existingTooltip = document.querySelector('.tooltip');
                if (existingTooltip) {
                    existingTooltip.remove();
                }
                
                // Créer le nouveau tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = title;
                
                // Styler le tooltip
                tooltip.style.position = 'absolute';
                tooltip.style.backgroundColor = 'var(--container-bg)';
                tooltip.style.color = 'var(--text-color)';
                tooltip.style.padding = '8px 12px';
                tooltip.style.borderRadius = '6px';
                tooltip.style.boxShadow = '0 4px 10px rgba(0,0,0,0.3)';
                tooltip.style.fontSize = '14px';
                tooltip.style.zIndex = '1000';
                tooltip.style.border = '1px solid var(--border-color)';
                tooltip.style.maxWidth = '300px';
                tooltip.style.whiteSpace = 'normal';
                
                // Ajouter le tooltip au DOM
                document.body.appendChild(tooltip);
                
                // Positionner le tooltip
                const rect = element.getBoundingClientRect();
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
                
                // Si le tooltip dépasse l'écran en haut, le placer en dessous
                if (rect.top - tooltip.offsetHeight < 10) {
                    tooltip.style.top = (rect.bottom + 5) + 'px';
                }
                
                // Si le tooltip dépasse l'écran à droite, l'aligner à droite
                if (rect.left + tooltip.offsetWidth > window.innerWidth) {
                    tooltip.style.left = 'auto';
                    tooltip.style.right = '10px';
                }
                
                // Supprimer le tooltip quand on quitte l'élément
                const removeTooltip = function() {
                    document.body.removeChild(tooltip);
                    element.removeEventListener('mouseleave', removeTooltip);
                    element.removeEventListener('click', removeTooltip);
                };
                
                element.addEventListener('mouseleave', removeTooltip);
                element.addEventListener('click', removeTooltip);
            };
            
            // Ajouter les écouteurs d'événements
            element.addEventListener('mouseenter', showTooltip);
        });
    },
    
    /**
     * Affiche un toast de notification
     * @param {string} message - Message à afficher
     * @param {number} [duration] - Durée d'affichage en ms
     * @param {string} [type] - Type de toast ('success', 'error', 'warning', 'info')
     */
    showToast: function(message, duration, type = 'success') {
        // Récupérer ou créer le conteneur de toast
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        
        // Nettoyer les classes existantes et ajouter le type
        toast.className = 'toast';
        toast.classList.add(`toast-${type}`);
        
        // Mettre à jour le contenu
        toast.textContent = message;
        toast.setAttribute('role', 'alert');
        
        // Afficher le toast
        toast.classList.add('show');
        
        // Définir le timeout pour masquer le toast
        const actualDuration = duration || this.config.toastDuration;
        clearTimeout(this.toastTimeout);
        this.toastTimeout = setTimeout(function() {
            toast.classList.remove('show');
        }, actualDuration);
    },
    
    /**
     * Charge les informations GPU
     */
    loadGpuInfo: function() {
        const gpuInfoElement = document.getElementById('gpuInfo');
        if (!gpuInfoElement) return;
        
        fetch(this.API_ENDPOINTS.GPU_INFO)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    // Vérifier si l'erreur est une commande non trouvée (nvidia-smi)
                    if (data.error.includes('not found') || data.error.includes('command not found')) {
                        gpuInfoElement.innerHTML = '<i class="fas fa-microchip"></i> GPU: Non détecté';
                        gpuInfoElement.setAttribute('title', 'Aucun GPU compatible NVIDIA détecté');
                    } else {
                        gpuInfoElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erreur GPU';
                        gpuInfoElement.setAttribute('title', this.truncateText(data.error, 50));
                    }
                    return;
                }
                
                if (data.gpus && data.gpus.length > 0) {
                    const gpu = data.gpus[0]; // Prendre le premier GPU
                    gpuInfoElement.innerHTML = `
                        <i class="fas fa-microchip"></i> ${gpu.name} 
                        <span class="gpu-stats">
                            <span class="gpu-util" title="Utilisation GPU">${gpu.utilization}%</span> | 
                            <span class="gpu-mem" title="Mémoire GPU">${gpu.memory_used}/${gpu.memory_total} MB</span>
                        </span>
                    `;
                    
                    // Ajouter une classe selon l'utilisation
                    gpuInfoElement.classList.remove('gpu-low', 'gpu-medium', 'gpu-high');
                    
                    const utilization = parseInt(gpu.utilization);
                    if (utilization > 80) {
                        gpuInfoElement.classList.add('gpu-high');
                    } else if (utilization > 40) {
                        gpuInfoElement.classList.add('gpu-medium');
                    } else {
                        gpuInfoElement.classList.add('gpu-low');
                    }
                } else {
                    gpuInfoElement.innerHTML = '<i class="fas fa-microchip"></i> Aucun GPU détecté';
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des informations GPU:', error);
                gpuInfoElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erreur de chargement GPU';
                gpuInfoElement.setAttribute('title', `Erreur: ${error.message}`);
            });
    },
    
    /**
     * Charge le modèle actuel
     * @param {Function} [callback] - Fonction à exécuter après le chargement
     */
    loadCurrentModel: function(callback) {
        const currentModelElement = document.getElementById('currentModel');
        if (!currentModelElement) {
            if (callback) callback(null);
            return;
        }
        
        // Afficher "Chargement..." pendant la requête
        currentModelElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Modèle: chargement...';
        
        fetch(this.API_ENDPOINTS.CURRENT_MODEL)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    // Vérifier si l'erreur est liée à Ollama
                    if (this.isOllamaConnectionError(data.error)) {
                        this.state.isOllamaRunning = false;
                        currentModelElement.innerHTML = '<span class="error-text"><i class="fas fa-exclamation-circle"></i> Modèle: Ollama non disponible</span>';
                        console.error('Erreur: Ollama n\'est pas disponible');
                    } else {
                        currentModelElement.innerHTML = '<span class="error-text"><i class="fas fa-exclamation-circle"></i> Modèle: Erreur de chargement</span>';
                    }
                    
                    if (callback) callback(null);
                    return;
                }
                
                // Vérifier si le modèle est "none" (aucun modèle disponible)
                if (data.current === 'none' || data.current === 'aucun_modele_disponible') {
                    currentModelElement.innerHTML = '<span class="warning-text"><i class="fas fa-exclamation-triangle"></i> Aucun modèle disponible</span>';
                    this.config.currentModelName = '';
                    
                    if (callback) callback('none');
                    return;
                }
                
                // Stocker le modèle actuel dans la variable globale
                this.config.currentModelName = data.current;
                this.state.isOllamaRunning = true;
                
                // Mettre à jour l'affichage
                currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: <span class="model-name">${this.config.currentModelName}</span>`;
                
                // Mettre à jour le sélecteur de modèle si disponible
                this.updateModelSelectors(this.config.currentModelName);
                
                if (callback) callback(this.config.currentModelName);
            })
            .catch(error => {
                console.error('Erreur lors du chargement du modèle actuel:', error);
                currentModelElement.innerHTML = '<span class="error-text"><i class="fas fa-exclamation-circle"></i> Modèle: Erreur de connexion</span>';
                
                if (callback) callback(null);
            });
    },
    
    /**
     * Met à jour tous les sélecteurs de modèle dans la page
     * @param {string} selectedModel - Le modèle à sélectionner
     */
    updateModelSelectors: function(selectedModel) {
        const selectors = document.querySelectorAll('select[data-model-selector]');
        if (selectors.length === 0) return;
        
        selectors.forEach(selector => {
            // Trouver l'option qui correspond au modèle
            for (let i = 0; i < selector.options.length; i++) {
                if (selector.options[i].value === selectedModel) {
                    selector.selectedIndex = i;
                    break;
                }
            }
            
            // Déclencher l'événement change
            const event = new Event('change');
            selector.dispatchEvent(event);
        });
    },
    
    /**
     * Charge la liste des modèles
     * @param {string} selectElementId - ID de l'élément select
     * @param {Function} [callback] - Fonction à exécuter après le chargement
     * @param {boolean} [forceRefresh] - Forcer le rafraîchissement du cache
     */
    loadModelsList: function(selectElementId, callback, forceRefresh = false) {
        const selectElement = document.getElementById(selectElementId);
        if (!selectElement) {
            if (callback) callback(null);
            return;
        }
        
        // Vérifier le cache si on ne force pas le rafraîchissement
        const now = Date.now();
        if (!forceRefresh && this.cache.models && (now - this.cache.lastModelsFetch < this.cache.cacheDuration)) {
            this.updateModelSelectElement(selectElement, this.cache.models, callback);
            return;
        }
        
        // Réinitialiser le select
        selectElement.innerHTML = '<option value="loading">Chargement des modèles...</option>';
        selectElement.disabled = true;
        
        fetch(this.API_ENDPOINTS.MODELS)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Mettre à jour le cache
                this.cache.models = data;
                this.cache.lastModelsFetch = now;
                
                // Mettre à jour le select
                this.updateModelSelectElement(selectElement, data, callback);
            })
            .catch(error => {
                console.error('Erreur lors du chargement des modèles:', error);
                
                // Vider le select
                selectElement.innerHTML = '<option value="none">Erreur de connexion</option>';
                selectElement.disabled = false;
                
                // Exécuter le callback si présent
                if (callback) {
                    callback({ error: error.message, models: [] });
                }
            });
    },
    
    /**
     * Met à jour un élément select avec les modèles
     * @param {Element} selectElement - Élément select à mettre à jour
     * @param {Object} data - Données contenant les modèles
     * @param {Function} [callback] - Fonction à exécuter après la mise à jour
     */
    updateModelSelectElement: function(selectElement, data, callback) {
        // Vider le select
        selectElement.innerHTML = '';
        selectElement.disabled = false;
        
        if (data.error) {
            // Vérifier si l'erreur est liée à Ollama
            if (this.isOllamaConnectionError(data.error)) {
                selectElement.innerHTML = '<option value="none">Ollama non disponible</option>';
                console.error('Erreur: Ollama n\'est pas disponible');
                this.state.isOllamaRunning = false;
            } else {
                selectElement.innerHTML = '<option value="none">Erreur de chargement</option>';
            }
            
            // Exécuter le callback si présent
            if (callback) {
                callback({ error: data.error, models: [] });
            }
            return;
        }
        
        if (!data.models || data.models.length === 0) {
            selectElement.innerHTML = '<option value="none">Aucun modèle disponible</option>';
            this.state.isOllamaRunning = true;
            
            // Exécuter le callback si présent
            if (callback) {
                callback({ models: [] });
            }
            return;
        }
        
        // Marquer Ollama comme fonctionnel
        this.state.isOllamaRunning = true;
        
        // Ajouter les modèles au select
        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            
            // Formater le nom du modèle
            let displayName = model.name;
            
            // Marquer le modèle par défaut
            if (model.name === data.default) {
                displayName += ' (défaut)';
                option.setAttribute('data-is-default', 'true');
            }
            
            option.textContent = displayName;
            
            // Ajouter des attributs data supplémentaires
            if (model.size) {
                const sizeMB = Math.round(model.size / (1024 * 1024));
                option.setAttribute('data-size', sizeMB + ' MB');
            }
            
            if (model.modified) {
                option.setAttribute('data-modified', model.modified);
            }
            
            // Si ce modèle est le même que currentModelName, le sélectionner
            if (model.name === this.config.currentModelName) {
                option.selected = true;
            }
            
            selectElement.appendChild(option);
        });
        
        // Si aucun modèle n'est sélectionné, sélectionner le modèle par défaut
        if (selectElement.selectedIndex < 0 && data.default) {
            for (let i = 0; i < selectElement.options.length; i++) {
                if (selectElement.options[i].value === data.default) {
                    selectElement.selectedIndex = i;
                    break;
                }
            }
        }
        
        // Marquer le select comme modifié pour les frameworks JS
        selectElement.setAttribute('data-model-selector', 'loaded');
        selectElement.dispatchEvent(new Event('change'));
        
        // Exécuter le callback si présent
        if (callback) {
            callback(data);
        }
    },
    
    /**
     * Vérifie si une erreur est liée à la connexion Ollama
     * @param {string} errorMessage - Message d'erreur
     * @returns {boolean} - True si l'erreur est liée à Ollama
     */
    isOllamaConnectionError: function(errorMessage) {
        if (!errorMessage) return false;
        
        const errorStr = String(errorMessage).toLowerCase();
        return (
            errorStr.includes('localhost:11434') || 
            errorStr.includes('connection refused') ||
            errorStr.includes('ollama n\'est pas') ||
            errorStr.includes('ollama n\'est pas disponible')
        );
    },
    
    /**
     * Fonction pour mettre à jour le modèle actuel via l'API
     * @param {string} modelName - Le nom du modèle à définir comme défaut
     * @returns {Promise} - Promesse résolue avec le résultat
     */
    updateCurrentModel: function(modelName) {
        if (!modelName || modelName === 'none' || modelName === 'loading') {
            return Promise.reject(new Error('Nom de modèle invalide'));
        }
        
        return fetch(this.API_ENDPOINTS.SET_DEFAULT_MODEL, {
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
            if (data.success) {
                // Mettre à jour la variable globale
                this.config.currentModelName = modelName;
                
                // Mettre à jour l'affichage
                const currentModelElement = document.getElementById('currentModel');
                if (currentModelElement) {
                    currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: <span class="model-name">${this.config.currentModelName}</span>`;
                }
                
                // Mettre à jour le sélecteur de modèle
                this.updateModelSelectors(modelName);
                
                return true;
            } else {
                console.error("Erreur lors de la mise à jour du modèle par défaut:", data.error);
                throw new Error(data.error || 'Erreur inconnue');
            }
        });
    },
    
    /**
     * Vérifie si Ollama est en cours d'exécution
     * @returns {Promise<boolean>} - Promesse résolue avec true si Ollama est en cours d'exécution
     */
    isOllamaRunning: function() {
        // Si on a déjà vérifié, utiliser la valeur en cache
        if (this.state.isOllamaRunning !== null) {
            return Promise.resolve(this.state.isOllamaRunning);
        }
        
        return fetch(this.API_ENDPOINTS.MODELS)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Vérifier s'il y a une erreur liée à la connexion Ollama
                if (data.error && this.isOllamaConnectionError(data.error)) {
                    this.state.isOllamaRunning = false;
                    return false;
                }
                
                // Vérifier s'il y a des modèles disponibles
                this.state.isOllamaRunning = !!(data.models && data.models.length > 0);
                return this.state.isOllamaRunning;
            })
            .catch(error => {
                console.error('Erreur lors de la vérification d\'Ollama:', error);
                this.state.isOllamaRunning = false;
                return false;
            });
    },
    
    /**
     * Formatage des nombres
     * @param {number} number - Nombre à formater
     * @returns {string} - Nombre formaté
     */
    formatNumber: function(number) {
        return new Intl.NumberFormat().format(number);
    },
    
    /**
     * Raccourcit un texte à une longueur maximale
     * @param {string} text - Texte à raccourcir
     * @param {number} [maxLength=100] - Longueur maximale
     * @returns {string} - Texte raccourci
     */
    truncateText: function(text, maxLength = 100) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    /**
     * Copie le texte dans le presse-papier
     * @param {string} text - Texte à copier
     * @returns {boolean} - True si la copie a réussi
     */
    copyToClipboard: function(text) {
        // Utiliser l'API Clipboard si disponible
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    this.showToast('Texte copié dans le presse-papier');
                    return true;
                })
                .catch(err => {
                    console.error('Erreur lors de la copie:', err);
                    this.showToast('Erreur lors de la copie', null, 'error');
                    return false;
                });
            return true;
        }
        
        // Méthode de secours pour les navigateurs qui ne supportent pas l'API Clipboard
        try {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = 0;
            document.body.appendChild(textarea);
            textarea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textarea);
            
            if (successful) {
                this.showToast('Texte copié dans le presse-papier');
                return true;
            } else {
                this.showToast('Erreur lors de la copie', null, 'error');
                return false;
            }
        } catch (err) {
            console.error('Erreur lors de la copie:', err);
            this.showToast('Erreur lors de la copie', null, 'error');
            return false;
        }
    },
    
    /**
     * Échappe les caractères HTML
     * @param {string} html - Texte HTML à échapper
     * @returns {string} - Texte échappé
     */
    escapeHtml: function(html) {
        if (!html) return '';
        
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    },
    
    /**
     * Formate le timestamp en date lisible
     * @param {number} timestamp - Timestamp Unix
     * @returns {string} - Date formatée
     */
    formatTimestamp: function(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    },
    
    /**
     * Formate une date ISO en date lisible
     * @param {string} isoDate - Date au format ISO
     * @returns {string} - Date formatée
     */
    formatDate: function(isoDate) {
        if (!isoDate) return '';
        
        try {
            const date = new Date(isoDate);
            return date.toLocaleString();
        } catch (e) {
            return isoDate;
        }
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
    AssistantIA.init();
});

// S'assurer que les ressources sont nettoyées quand la page est déchargée
window.addEventListener('beforeunload', function() {
    AssistantIA.cleanup();
});
