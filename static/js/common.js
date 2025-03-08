/**
 * Fonctions JavaScript partagées pour l'Assistant IA
 * Version améliorée avec meilleure gestion des erreurs
 */

// Variable globale pour stocker le modèle actuel
let currentModelName = '';

// Compteur de tentatives pour les opérations critiques
let retryCounter = 0;
const MAX_RETRIES = 3;

// Constantes pour les délais
const TOAST_DURATION = 3000;
const ERROR_TOAST_DURATION = 5000;
const GPU_REFRESH_INTERVAL = 30000;

// Gestion du thème (clair/sombre)
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le thème
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    // Écouteur pour le bouton de changement de thème
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Afficher un toast
            showToast(`Thème ${newTheme === 'dark' ? 'sombre' : 'clair'} activé`);
        });
    }
    
    // Initialiser les tooltips
    initTooltips();
    
    // Charger les informations GPU
    loadGpuInfo();
    
    // Nouvelle fonction: vérifier l'état de la connexion à Ollama
    checkOllamaConnection();
});

// Met à jour l'icône du bouton de thème
function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' 
            ? '<i class="fas fa-sun"></i>' 
            : '<i class="fas fa-moon"></i>';
    }
}

// Initialise les tooltips
function initTooltips() {
    document.querySelectorAll('[title]').forEach(element => {
        const title = element.getAttribute('title');
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = title;
            
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
            
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            
            element.addEventListener('mouseleave', function() {
                document.body.removeChild(tooltip);
            });
        });
    });
}

// Affiche un toast de notification avec durée personnalisable
function showToast(message, duration = TOAST_DURATION, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    // Réinitialiser les classes et styles
    toast.className = 'toast';
    if (isError) {
        toast.classList.add('toast-error');
    }
    
    toast.textContent = message;
    toast.classList.add('show');
    
    // Effacer tout timer existant
    if (toast.timeoutId) {
        clearTimeout(toast.timeoutId);
    }
    
    // Définir un nouveau timer
    toast.timeoutId = setTimeout(function() {
        toast.classList.remove('show');
    }, duration);
}

// Affiche un toast d'erreur (style différent et durée plus longue)
function showErrorToast(message, duration = ERROR_TOAST_DURATION) {
    showToast(message, duration, true);
}

// Charge les informations GPU avec gestion améliorée des erreurs
function loadGpuInfo() {
    const gpuInfoElement = document.getElementById('gpuInfo');
    if (!gpuInfoElement) return;
    
    fetch('/api/gpu-info')
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
                } else {
                    gpuInfoElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erreur GPU: ' + truncateText(data.error, 30);
                }
                return;
            }
            
            if (data.gpus && data.gpus.length > 0) {
                const gpu = data.gpus[0]; // Prendre le premier GPU
                gpuInfoElement.innerHTML = `<i class="fas fa-microchip"></i> ${gpu.name} | Utilisation: ${gpu.utilization}% | Mémoire: ${gpu.memory_used}/${gpu.memory_total} MB`;
            } else {
                gpuInfoElement.innerHTML = '<i class="fas fa-microchip"></i> Aucun GPU détecté';
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des informations GPU:', error);
            gpuInfoElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erreur de chargement GPU';
        });
}

// Nouvelle fonction: vérifie si Ollama est accessible
function checkOllamaConnection() {
    fetch('/api/models')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                if (data.error.includes('localhost:11434') || data.error.includes('connection refused')) {
                    console.warn('Ollama n\'est pas disponible: Service non démarré');
                    showStatusBanner('Ollama n\'est pas en cours d\'exécution. Certaines fonctionnalités ne seront pas disponibles.', 'warning');
                } else {
                    console.error('Erreur Ollama:', data.error);
                }
                return;
            }
            
            // Si nous avons des modèles, Ollama fonctionne correctement
            if (data.models && data.models.length > 0) {
                console.info(`Ollama est disponible: ${data.models.length} modèles trouvés`);
            } else {
                console.warn('Ollama est disponible mais aucun modèle n\'est installé');
                showStatusBanner('Aucun modèle Ollama n\'est installé. Allez dans "Gestion Ollama" pour en télécharger un.', 'info');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la vérification d\'Ollama:', error);
        });
}

// Nouvelle fonction: affiche une bannière d'état en haut de la page
function showStatusBanner(message, type = 'info') {
    // Vérifier si une bannière existe déjà
    let banner = document.getElementById('statusBanner');
    
    if (!banner) {
        // Créer une nouvelle bannière
        banner = document.createElement('div');
        banner.id = 'statusBanner';
        banner.style.width = '100%';
        banner.style.padding = '10px 20px';
        banner.style.position = 'fixed';
        banner.style.top = '0';
        banner.style.left = '0';
        banner.style.zIndex = '9999';
        banner.style.textAlign = 'center';
        banner.style.fontWeight = 'bold';
        banner.style.display = 'flex';
        banner.style.justifyContent = 'space-between';
        banner.style.alignItems = 'center';
        
        // Ajouter un bouton de fermeture
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.marginLeft = '20px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.fontSize = '20px';
        closeBtn.onclick = function() {
            document.body.removeChild(banner);
        };
        
        document.body.insertBefore(banner, document.body.firstChild);
        banner.appendChild(closeBtn);
    }
    
    // Définir le type de bannière
    banner.className = '';
    switch (type) {
        case 'error':
            banner.style.backgroundColor = 'var(--error-color)';
            banner.style.color = 'white';
            break;
        case 'warning':
            banner.style.backgroundColor = '#f59e0b';
            banner.style.color = 'white';
            break;
        case 'success':
            banner.style.backgroundColor = 'var(--success-color)';
            banner.style.color = 'white';
            break;
        default: // info
            banner.style.backgroundColor = 'var(--primary-color)';
            banner.style.color = 'white';
    }
    
    // Mettre à jour le message
    banner.innerHTML = message + banner.innerHTML.substring(banner.innerHTML.indexOf('<span'));
}

// Charge le modèle actuel avec gestion améliorée des erreurs
function loadCurrentModel() {
    const currentModelElement = document.getElementById('currentModel');
    if (!currentModelElement) return;
    
    // Afficher "Chargement..." pendant la requête
    currentModelElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Modèle: chargement...';
    
    fetch('/api/current-model')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                // Vérifier si l'erreur est liée à Ollama
                if (data.error.includes('localhost:11434') || data.error.includes('connection refused')) {
                    currentModelElement.innerHTML = '<span style="color: var(--error-color);"><i class="fas fa-exclamation-circle"></i> Modèle: Ollama non disponible</span>';
                    console.error('Erreur: Ollama n\'est pas disponible');
                    return;
                }
                
                currentModelElement.textContent = 'Modèle: Erreur de chargement';
                return;
            }
            
            // Vérifier si le modèle est "none" (aucun modèle disponible)
            if (data.current === 'none' || data.current === 'aucun_modele_disponible') {
                currentModelElement.innerHTML = '<span style="color: var(--error-color);"><i class="fas fa-exclamation-triangle"></i> Aucun modèle disponible</span>';
                return;
            }
            
            // Stocker le modèle actuel dans la variable globale
            currentModelName = data.current;
            
            // Mettre à jour l'affichage
            currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: ${currentModelName}`;
            
            // Mettre à jour le sélecteur de modèle si disponible
            updateModelSelect(currentModelName);
        })
        .catch(error => {
            console.error('Erreur lors du chargement du modèle actuel:', error);
            currentModelElement.innerHTML = '<span style="color: var(--error-color);"><i class="fas fa-exclamation-circle"></i> Modèle: Erreur de connexion</span>';
            
            // Si c'est la première tentative, réessayer après un délai
            if (retryCounter < MAX_RETRIES) {
                retryCounter++;
                setTimeout(loadCurrentModel, 2000 * retryCounter);
            }
        });
}

// Met à jour les sélecteurs de modèle si disponibles
function updateModelSelect(modelName) {
    // Rechercher tous les sélecteurs de modèle dans la page
    document.querySelectorAll('select[id$="ModelSelect"]').forEach(selectElement => {
        if (selectElement && selectElement.options.length > 0) {
            // Trouver l'option qui correspond au modèle
            for (let i = 0; i < selectElement.options.length; i++) {
                if (selectElement.options[i].value === modelName) {
                    selectElement.selectedIndex = i;
                    break;
                }
            }
        }
    });
}

// Charge la liste des modèles avec gestion améliorée des erreurs
function loadModelsList(selectElementId, callback = null) {
    const selectElement = document.getElementById(selectElementId);
    if (!selectElement) return;
    
    // Réinitialiser le select
    selectElement.innerHTML = '<option value="loading"><i class="fas fa-spinner fa-spin"></i> Chargement des modèles...</option>';
    
    fetch('/api/models')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Vider le select
            selectElement.innerHTML = '';
            
            if (data.error) {
                // Vérifier si l'erreur est liée à Ollama
                if (data.error.includes('localhost:11434') || data.error.includes('connection refused')) {
                    selectElement.innerHTML = '<option value="none">Ollama non disponible</option>';
                    console.error('Erreur: Ollama n\'est pas disponible');
                    showErrorToast('Erreur: Ollama n\'est pas disponible. Exécutez "ollama serve" dans un terminal.');
                } else {
                    selectElement.innerHTML = '<option value="none">Erreur de chargement</option>';
                    showErrorToast(`Erreur: ${data.error}`);
                }
                
                // Exécuter le callback si présent
                if (callback && typeof callback === 'function') {
                    callback({ error: data.error, models: [] });
                }
                return;
            }
            
            if (!data.models || data.models.length === 0) {
                selectElement.innerHTML = '<option value="none">Aucun modèle disponible</option>';
                
                // Exécuter le callback si présent
                if (callback && typeof callback === 'function') {
                    callback({ models: [] });
                }
                return;
            }
            
            // Ajouter les modèles au select
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                
                // Marquer le modèle par défaut
                if (model.name === data.default) {
                    option.textContent += ' (défaut)';
                    option.selected = true;
                }
                
                // Si ce modèle est le même que currentModelName, le sélectionner
                if (model.name === currentModelName) {
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
            
            // Exécuter le callback si présent
            if (callback && typeof callback === 'function') {
                callback(data);
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des modèles:', error);
            selectElement.innerHTML = '<option value="none">Erreur de connexion</option>';
            
            // Exécuter le callback si présent
            if (callback && typeof callback === 'function') {
                callback({ error: error.message, models: [] });
            }
            
            // Afficher un toast d'erreur
            showErrorToast(`Erreur lors du chargement des modèles: ${error.message}`);
        });
}

// Formatage des nombres
function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

// Raccourcit un texte à une longueur maximale
function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Copie le texte dans le presse-papier
function copyToClipboard(text) {
    // Utiliser l'API moderne si disponible
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast('Texte copié dans le presse-papier');
            })
            .catch(err => {
                console.error('Erreur lors de la copie:', err);
                showErrorToast('Erreur lors de la copie');
                fallbackCopyToClipboard(text);
            });
    } else {
        // Méthode de secours pour les navigateurs plus anciens
        fallbackCopyToClipboard(text);
    }
}

// Méthode de secours pour copier dans le presse-papier
function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Texte copié dans le presse-papier');
        } else {
            showErrorToast('Erreur lors de la copie');
        }
    } catch (err) {
        console.error('Erreur lors de la copie:', err);
        showErrorToast('Erreur lors de la copie');
    }
    
    document.body.removeChild(textarea);
}

// Échappe les caractères HTML
function escapeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

// Formate le timestamp en date lisible
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
}

// Fonction améliorée pour mettre à jour le modèle actuel via l'API
function updateCurrentModel(modelName) {
    if (!modelName) return Promise.reject(new Error('Nom de modèle non spécifié'));
    
    // Afficher un toast de chargement
    showToast(`Définition de ${modelName} comme modèle par défaut...`);
    
    return fetch('/api/set-default-model', {
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
            currentModelName = modelName;
            
            // Mettre à jour l'affichage
            const currentModelElement = document.getElementById('currentModel');
            if (currentModelElement) {
                currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: ${currentModelName}`;
            }
            
            // Afficher un toast de succès
            showToast(`Modèle ${modelName} défini comme modèle par défaut`, 3000);
            
            return true;
        } else {
            console.error("Erreur lors de la mise à jour du modèle par défaut:", data.error);
            showErrorToast(`Erreur: ${data.error || 'Impossible de définir le modèle par défaut'}`);
            return false;
        }
    })
    .catch(error => {
        console.error("Erreur de connexion lors de la mise à jour du modèle:", error);
        showErrorToast(`Erreur: ${error.message}`);
        return false;
    });
}

// Fonction améliorée pour vérifier si Ollama est en cours d'exécution
function isOllamaRunning() {
    return fetch('/api/models')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Vérifier s'il y a une erreur liée à la connexion Ollama
            if (data.error && (data.error.includes('localhost:11434') || data.error.includes('connection refused'))) {
                return false;
            }
            
            // Vérifier s'il y a des modèles disponibles
            return data.models && data.models.length > 0;
        })
        .catch(error => {
            console.error('Erreur lors de la vérification d\'Ollama:', error);
            return false;
        });
}

// Nouvelle fonction: obtenir des informations de diagnostic
function getDiagnosticInfo() {
    return fetch('/api/diagnostic')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des informations de diagnostic:', error);
            return { error: error.message };
        });
}

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger le modèle actuel
    loadCurrentModel();
    
    // Rafraîchir les infos GPU toutes les 30 secondes
    setInterval(loadGpuInfo, GPU_REFRESH_INTERVAL);
});