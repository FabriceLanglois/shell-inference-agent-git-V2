/**
 * Fonctions JavaScript pour la console de l'Assistant IA
 * Version 2.0
 */

// Namespace pour éviter les conflits globaux
const ConsoleManager = {
    // Configuration
    config: {
        maxHistorySize: 100,
        maxOutputLines: 1000,
        executeTimeout: 30000,  // 30 secondes
        shortcuts: {
            execute: 'Enter',
            prevCommand: 'ArrowUp',
            nextCommand: 'ArrowDown',
            lastOutputToPrompt: 'Alt+l'
        }
    },
    
    // États
    state: {
        commandHistory: [],
        currentHistoryIndex: -1,
        lastOutput: '',
        interactiveMode: false,
        currentInteractiveCommand: '',
        isRecording: false,
        isExecuting: false,
        isMicActive: false,
        visualizationInterval: null
    },
    
    // Éléments DOM
    elements: {
        terminal: null,
        commandInput: null,
        executeBtn: null,
        clearBtn: null,
        copyAllBtn: null,
        copyLastOutputBtn: null,
        lastOutputToPromptBtn: null,
        checkOllamaBtn: null,
        inferenceBtn: null,
        browserBtn: null,
        micBtn: null,
        statusText: null,
        execTimeInfo: null,
        inferenceModal: null,
        closeInferenceModal: null,
        modelSelect: null,
        promptInput: null,
        temperatureSlider: null,
        temperatureValue: null,
        maxTokensSlider: null,
        maxTokensValue: null,
        runInferenceBtn: null,
        cancelInferenceBtn: null,
        fileExplorerModal: null,
        closeFileExplorerModal: null,
        currentDirInput: null,
        navigateBtn: null,
        fileListContainer: null,
        closeFileExplorerBtn: null,
        micVisualization: null
    },
    
    /**
     * Initialisation du module de console
     */
    init: function() {
        console.log('Initialisation du ConsoleManager...');
        
        // Récupérer les éléments DOM
        this.cacheElements();
        
        // Initialiser les écouteurs d'événements
        this.initEventListeners();
        
        // Charger l'historique des commandes depuis le localStorage
        this.loadCommandHistory();
        
        // Charger les modèles pour l'inférence
        this.loadModels();
        
        // Focus sur l'input au chargement
        if (this.elements.commandInput) {
            this.elements.commandInput.focus();
        }
        
        // Message de bienvenue
        if (this.elements.statusText) {
            this.elements.statusText.textContent = 'Prêt';
        }
        
        console.log('ConsoleManager initialisé');
    },
    
    /**
     * Met en cache les éléments DOM
     */
    cacheElements: function() {
        this.elements.terminal = document.getElementById('terminal');
        this.elements.commandInput = document.getElementById('commandInput');
        this.elements.executeBtn = document.getElementById('executeBtn');
        this.elements.clearBtn = document.getElementById('clearBtn');
        this.elements.copyAllBtn = document.getElementById('copyAllBtn');
        this.elements.copyLastOutputBtn = document.getElementById('copyLastOutputBtn');
        this.elements.lastOutputToPromptBtn = document.getElementById('lastOutputToPromptBtn');
        this.elements.checkOllamaBtn = document.getElementById('checkOllamaBtn');
        this.elements.inferenceBtn = document.getElementById('inferenceBtn');
        this.elements.browserBtn = document.getElementById('browserBtn');
        this.elements.micBtn = document.getElementById('micBtn');
        this.elements.statusText = document.getElementById('statusText');
        this.elements.execTimeInfo = document.getElementById('execTimeInfo');
        this.elements.inferenceModal = document.getElementById('inferenceModal');
        this.elements.closeInferenceModal = document.getElementById('closeInferenceModal');
        this.elements.modelSelect = document.getElementById('modelSelect');
        this.elements.promptInput = document.getElementById('promptInput');
        this.elements.temperatureSlider = document.getElementById('temperatureSlider');
        this.elements.temperatureValue = document.getElementById('temperatureValue');
        this.elements.maxTokensSlider = document.getElementById('maxTokensSlider');
        this.elements.maxTokensValue = document.getElementById('maxTokensValue');
        this.elements.runInferenceBtn = document.getElementById('runInferenceBtn');
        this.elements.cancelInferenceBtn = document.getElementById('cancelInferenceBtn');
        this.elements.fileExplorerModal = document.getElementById('fileExplorerModal');
        this.elements.closeFileExplorerModal = document.getElementById('closeFileExplorerModal');
        this.elements.currentDirInput = document.getElementById('currentDirInput');
        this.elements.navigateBtn = document.getElementById('navigateBtn');
        this.elements.fileListContainer = document.getElementById('fileListContainer');
        this.elements.closeFileExplorerBtn = document.getElementById('closeFileExplorerBtn');
        this.elements.micVisualization = document.getElementById('micVisualization');
    },
    
    /**
     * Initialise les écouteurs d'événements
     */
    initEventListeners: function() {
        // Bouton d'exécution
        if (this.elements.executeBtn) {
            this.elements.executeBtn.addEventListener('click', () => {
                this.executeCommand(this.elements.commandInput.value);
            });
        }
        
        // Bouton d'effacement
        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => {
                this.clearTerminal();
            });
        }
        
        // Boutons de copie
        if (this.elements.copyAllBtn) {
            this.elements.copyAllBtn.addEventListener('click', () => {
                this.copyTerminalContent();
            });
        }
        
        if (this.elements.copyLastOutputBtn) {
            this.elements.copyLastOutputBtn.addEventListener('click', () => {
                this.copyLastOutput();
            });
        }
        
        if (this.elements.lastOutputToPromptBtn) {
            this.elements.lastOutputToPromptBtn.addEventListener('click', () => {
                this.lastOutputToPrompt();
            });
        }
        
        // Bouton de vérification Ollama
        if (this.elements.checkOllamaBtn) {
            this.elements.checkOllamaBtn.addEventListener('click', () => {
                this.checkOllama();
            });
        }
        
        // Bouton d'inférence directe
        if (this.elements.inferenceBtn) {
            this.elements.inferenceBtn.addEventListener('click', () => {
                this.showInferenceModal();
            });
        }
        
        // Bouton d'explorateur de fichiers
        if (this.elements.browserBtn) {
            this.elements.browserBtn.addEventListener('click', () => {
                this.showFileExplorerModal();
            });
        }
        
        // Bouton du microphone
        if (this.elements.micBtn) {
            this.elements.micBtn.addEventListener('click', () => {
                this.toggleSpeechRecognition();
            });
        }
        
        // Modal d'inférence
        if (this.elements.closeInferenceModal) {
            this.elements.closeInferenceModal.addEventListener('click', () => {
                this.elements.inferenceModal.style.display = 'none';
            });
        }
        
        if (this.elements.runInferenceBtn) {
            this.elements.runInferenceBtn.addEventListener('click', () => {
                this.runInference();
            });
        }
        
        if (this.elements.cancelInferenceBtn) {
            this.elements.cancelInferenceBtn.addEventListener('click', () => {
                this.elements.inferenceModal.style.display = 'none';
            });
        }
        
        // Sliders
        if (this.elements.temperatureSlider) {
            this.elements.temperatureSlider.addEventListener('input', () => {
                this.elements.temperatureValue.textContent = this.elements.temperatureSlider.value;
            });
        }
        
        if (this.elements.maxTokensSlider) {
            this.elements.maxTokensSlider.addEventListener('input', () => {
                this.elements.maxTokensValue.textContent = this.elements.maxTokensSlider.value;
            });
        }
        
        // Modal d'explorateur de fichiers
        if (this.elements.closeFileExplorerModal) {
            this.elements.closeFileExplorerModal.addEventListener('click', () => {
                this.elements.fileExplorerModal.style.display = 'none';
            });
        }
        
        if (this.elements.closeFileExplorerBtn) {
            this.elements.closeFileExplorerBtn.addEventListener('click', () => {
                this.elements.fileExplorerModal.style.display = 'none';
            });
        }
        
        if (this.elements.navigateBtn) {
            this.elements.navigateBtn.addEventListener('click', () => {
                this.exploreFiles(this.elements.currentDirInput.value);
            });
        }
        
        // Input de commande
        if (this.elements.commandInput) {
            this.elements.commandInput.addEventListener('keydown', (e) => {
                this.handleCommandInputKeydown(e);
            });
        }
        
        // Input de répertoire courant
        if (this.elements.currentDirInput) {
            this.elements.currentDirInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.exploreFiles(this.elements.currentDirInput.value);
                }
            });
        }
        
        // Fermer les modals quand on clique à l'extérieur
        window.addEventListener('click', (e) => {
            if (e.target === this.elements.inferenceModal) {
                this.elements.inferenceModal.style.display = 'none';
            }
            
            if (e.target === this.elements.fileExplorerModal) {
                this.elements.fileExplorerModal.style.display = 'none';
            }
        });
    },
    
    /**
     * Gère les événements clavier de l'input de commande
     * @param {KeyboardEvent} e - Événement clavier
     */
    handleCommandInputKeydown: function(e) {
        // Touche Entrée pour exécuter la commande
        if (e.key === this.config.shortcuts.execute) {
            e.preventDefault();
            this.executeCommand(this.elements.commandInput.value);
        }
        
        // Touches Haut/Bas pour naviguer dans l'historique
        if (e.key === this.config.shortcuts.prevCommand) {
            e.preventDefault();
            this.navigateHistory(1);
        } else if (e.key === this.config.shortcuts.nextCommand) {
            e.preventDefault();
            this.navigateHistory(-1);
        }
        
        // Alt+L pour copier la dernière sortie dans le prompt
        if (e.key === 'l' && e.altKey) {
            e.preventDefault();
            this.lastOutputToPrompt();
        }
    },
    
    /**
     * Charge les modèles pour l'inférence
     */
    loadModels: function() {
        if (!this.elements.modelSelect) return;
        
        AssistantIA.loadModelsList('modelSelect', (data) => {
            // Une fois les modèles chargés, vérifier s'il y en a
            if (data && data.models && data.models.length > 0) {
                // Activer le bouton d'inférence directe
                if (this.elements.inferenceBtn) {
                    this.elements.inferenceBtn.disabled = false;
                }
                
                // Afficher un toast avec le nombre de modèles disponibles
                AssistantIA.showToast(`${data.models.length} modèles disponibles`);
            } else {
                // Pas de modèles disponibles, désactiver le bouton d'inférence
                if (this.elements.inferenceBtn) {
                    this.elements.inferenceBtn.disabled = true;
                }
                
                // Afficher un toast d'avertissement
                AssistantIA.showToast("Aucun modèle disponible. Installez Ollama et téléchargez un modèle.", 5000, 'warning');
                
                // Ajouter un message dans le terminal
                this.addTerminalLine("Aucun modèle d'IA n'est disponible. Allez dans 'Gestion Ollama' pour en télécharger un.", "error");
            }
        });
    },
    
    /**
     * Ajoute une ligne au terminal
     * @param {string} text - Texte à ajouter
     * @param {string} [className=''] - Classe CSS à ajouter
     * @returns {HTMLElement} - L'élément créé
     */
    addTerminalLine: function(text, className = '') {
        if (!this.elements.terminal) return null;
        
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        if (className) {
            line.classList.add(className);
        }
        
        // Création du bouton de copie
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.setAttribute('aria-label', 'Copier');
        copyButton.setAttribute('title', 'Copier ce texte');
        copyButton.addEventListener('click', () => {
            AssistantIA.copyToClipboard(text);
        });
        
        // Formater le texte
        if (text.startsWith('assistant-ia $')) {
            // Commande
            const promptText = document.createElement('span');
            promptText.className = 'prompt';
            promptText.textContent = text.split(' ')[0] + ' ' + text.split(' ')[1];
            
            line.appendChild(promptText);
            line.appendChild(document.createTextNode(' ' + text.substring(text.indexOf('$') + 2)));
        } else {
            // Sortie
            const textPara = document.createElement('pre');
            textPara.className = 'terminal-output';
            textPara.textContent = text;
            line.appendChild(textPara);
        }
        
        line.appendChild(copyButton);
        this.elements.terminal.appendChild(line);
        
        // Limiter le nombre de lignes dans le terminal
        while (this.elements.terminal.childElementCount > this.config.maxOutputLines) {
            this.elements.terminal.removeChild(this.elements.terminal.firstChild);
        }
        
        // Scroll vers le bas
        this.elements.terminal.scrollTop = this.elements.terminal.scrollHeight;
        
        return line;
    },
    
    /**
     * Exécute une commande
     * @param {string} command - Commande à exécuter
     * @param {boolean} [isInteractive=false] - Indique si c'est une entrée interactive
     */
    executeCommand: function(command, isInteractive = false) {
        command = command.trim();
        if (!command) return;
        
        // Éviter les exécutions multiples simultanées
        if (this.state.isExecuting && !isInteractive) {
            AssistantIA.showToast('Une commande est déjà en cours d\'exécution', null, 'warning');
            return;
        }
        
        this.state.isExecuting = true;
        
        // Ajouter à l'historique des commandes
        if (!isInteractive && !this.state.interactiveMode) {
            this.addToHistory(command);
        }
        
        // Afficher la commande dans le terminal (sauf en mode interactif pour les entrées)
        if (!isInteractive || !this.state.interactiveMode) {
            this.addTerminalLine(`assistant-ia $ ${command}`);
        }
        
        // Mettre à jour le statut
        if (this.elements.statusText) {
            this.elements.statusText.textContent = 'Exécution en cours...';
            this.elements.statusText.className = 'status-running';
        }
        
        // Désactiver le bouton d'exécution
        if (this.elements.executeBtn) {
            this.elements.executeBtn.disabled = true;
        }
        
        // Mesurer le temps d'exécution
        const startTime = performance.now();
        
        // Déterminer l'API à utiliser en fonction du mode
        const apiEndpoint = this.state.interactiveMode ? '/execute_interactive' : '/execute';
        
        // Si nous sommes en mode interactif, envoyer la commande interactive
        const requestData = this.state.interactiveMode 
            ? { command: this.state.currentInteractiveCommand, input_text: command }
            : { command };
        
        // Créer un contrôleur d'abandon pour pouvoir annuler la requête
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, this.config.executeTimeout);
        
        // Envoyer la requête
        fetch(apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData),
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const endTime = performance.now();
            const execTime = ((endTime - startTime) / 1000).toFixed(2);
            
            // Mettre à jour l'info de temps d'exécution
            if (this.elements.execTimeInfo) {
                this.elements.execTimeInfo.textContent = `Temps d'exécution: ${execTime}s`;
            }
            
            if (data.error) {
                // Vérifier si l'erreur est liée à Ollama
                if (AssistantIA.isOllamaConnectionError(data.error)) {
                    this.addTerminalLine("Erreur: Le service Ollama n'est pas en cours d'exécution.", "error");
                    this.addTerminalLine("Exécutez 'ollama serve' dans un terminal séparé pour démarrer le service.", "error");
                    
                    if (this.elements.statusText) {
                        this.elements.statusText.textContent = 'Erreur: Ollama non disponible';
                        this.elements.statusText.className = 'status-error';
                    }
                } else {
                    // Afficher l'erreur générique
                    this.addTerminalLine(data.error, 'error');
                    
                    if (this.elements.statusText) {
                        this.elements.statusText.textContent = 'Erreur';
                        this.elements.statusText.className = 'status-error';
                    }
                }
                
                // Si nous étions en mode interactif, sortir de ce mode
                if (this.state.interactiveMode) {
                    this.exitInteractiveMode();
                }
                
                this.state.isExecuting = false;
                if (this.elements.executeBtn) {
                    this.elements.executeBtn.disabled = false;
                }
                return;
            }
            
            // Afficher la sortie standard si présente
            if (data.stdout) {
                const lines = data.stdout.trim().split('\n');
                lines.forEach(line => {
                    this.addTerminalLine(line);
                });
                this.state.lastOutput = data.stdout;
            }
            
            // Afficher la sortie d'erreur si présente
            if (data.stderr) {
                const lines = data.stderr.trim().split('\n');
                lines.forEach(line => {
                    this.addTerminalLine(line, 'error');
                });
                
                // Si nous avons une erreur en mode interactif, désactiver ce mode
                if (this.state.interactiveMode && data.stderr.includes('error')) {
                    this.exitInteractiveMode();
                }
            }
            
            // Vérifier si nous devons entrer en mode interactif
            if (!this.state.interactiveMode && command.startsWith('ssh ')) {
                this.enterInteractiveMode(command);
            }
            
            // Si le mode interactif est actif mais que la commande est 'exit', terminer le mode
            if (this.state.interactiveMode && command === 'exit') {
                this.exitInteractiveMode();
            }
            
            // Mise à jour du statut
            if (this.elements.statusText) {
                if (data.returncode === 0) {
                    this.elements.statusText.textContent = this.state.interactiveMode ? 'Mode interactif' : 'Succès';
                    this.elements.statusText.className = this.state.interactiveMode ? 'status-interactive' : 'status-success';
                } else {
                    this.elements.statusText.textContent = `Erreur (code ${data.returncode})`;
                    this.elements.statusText.className = 'status-error';
                }
            }
            
            this.state.isExecuting = false;
            if (this.elements.executeBtn) {
                this.elements.executeBtn.disabled = false;
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            
            console.error('Erreur lors de l\'exécution de la commande:', error);
            
            if (error.name === 'AbortError') {
                this.addTerminalLine(`Erreur: La commande a dépassé le délai d'exécution (${this.config.executeTimeout / 1000}s)`, 'error');
            } else {
                this.addTerminalLine(`Erreur de connexion: ${error.message}`, 'error');
            }
            
            if (this.elements.statusText) {
                this.elements.statusText.textContent = 'Erreur de connexion';
                this.elements.statusText.className = 'status-error';
            }
            
            // Désactiver le mode interactif en cas d'erreur
            if (this.state.interactiveMode) {
                this.exitInteractiveMode();
            }
            
            this.state.isExecuting = false;
            if (this.elements.executeBtn) {
                this.elements.executeBtn.disabled = false;
            }
        });
        
        // Vider l'input si ce n'est pas interactif
        if (!isInteractive && this.elements.commandInput) {
            this.elements.commandInput.value = '';
        }
    },
    
    /**
     * Entre en mode interactif
     * @param {string} command - Commande interactive
     */
    enterInteractiveMode: function(command) {
        this.state.interactiveMode = true;
        this.state.currentInteractiveCommand = command;
        
        if (this.elements.terminal) {
            this.elements.terminal.classList.add('interactive-mode');
        }
        
        if (this.elements.statusText) {
            this.elements.statusText.textContent = 'Mode interactif';
            this.elements.statusText.className = 'status-interactive';
        }
        
        if (this.elements.commandInput) {
            this.elements.commandInput.placeholder = 'Entrez une commande interactive...';
        }
    },
    
    /**
     * Quitte le mode interactif
     */
    exitInteractiveMode: function() {
        this.state.interactiveMode = false;
        this.state.currentInteractiveCommand = '';
        
        if (this.elements.terminal) {
            this.elements.terminal.classList.remove('interactive-mode');
        }
        
        if (this.elements.statusText) {
            this.elements.statusText.textContent = 'Mode normal';
            this.elements.statusText.className = 'status-normal';
        }
        
        if (this.elements.commandInput) {
            this.elements.commandInput.placeholder = 'Entrez une commande...';
        }
    },
    
    /**
     * Navigue dans l'historique des commandes
     * @param {number} direction - Direction (1: plus ancien, -1: plus récent)
     */
    navigateHistory: function(direction) {
        if (!this.elements.commandInput) return;
        if (this.state.commandHistory.length === 0) return;
        
        if (direction > 0) {
            // Remonter dans l'historique
            this.state.currentHistoryIndex = Math.min(
                this.state.currentHistoryIndex + 1, 
                this.state.commandHistory.length - 1
            );
        } else {
            // Descendre dans l'historique
            this.state.currentHistoryIndex = Math.max(this.state.currentHistoryIndex - 1, -1);
        }
        
        if (this.state.currentHistoryIndex >= 0) {
            this.elements.commandInput.value = this.state.commandHistory[this.state.currentHistoryIndex];
        } else {
            this.elements.commandInput.value = '';
        }
        
        // Placer le curseur à la fin
        setTimeout(() => {
            this.elements.commandInput.selectionStart = 
            this.elements.commandInput.selectionEnd = 
            this.elements.commandInput.value.length;
        }, 0);
    },
    
    /**
     * Ajoute une commande à l'historique
     * @param {string} command - Commande à ajouter
     */
    addToHistory: function(command) {
        // Éviter les doublons consécutifs
        if (this.state.commandHistory.length > 0 && this.state.commandHistory[0] === command) {
            return;
        }
        
        this.state.commandHistory.unshift(command);
        this.state.currentHistoryIndex = -1;
        
        // Limiter la taille de l'historique
        if (this.state.commandHistory.length > this.config.maxHistorySize) {
            this.state.commandHistory.pop();
        }
        
        // Sauvegarder l'historique dans le localStorage
        this.saveCommandHistory();
    },
    
    /**
     * Sauvegarde l'historique des commandes dans le localStorage
     */
    saveCommandHistory: function() {
        try {
            localStorage.setItem('commandHistory', JSON.stringify(this.state.commandHistory));
        } catch (e) {
            console.error('Erreur lors de la sauvegarde de l\'historique:', e);
        }
    },
    
    /**
     * Charge l'historique des commandes depuis le localStorage
     */
    loadCommandHistory: function() {
        try {
            const savedHistory = localStorage.getItem('commandHistory');
            if (savedHistory) {
                this.state.commandHistory = JSON.parse(savedHistory);
                
                // Valider l'historique
                if (!Array.isArray(this.state.commandHistory)) {
                    this.state.commandHistory = [];
                }
                
                // Limiter la taille
                if (this.state.commandHistory.length > this.config.maxHistorySize) {
                    this.state.commandHistory = this.state.commandHistory.slice(0, this.config.maxHistorySize);
                }
            }
        } catch (e) {
            console.error('Erreur lors du chargement de l\'historique:', e);
            this.state.commandHistory = [];
        }
    },
    
    /**
     * Efface le terminal
     */
    clearTerminal: function() {
        if (!this.elements.terminal) return;
        
        this.elements.terminal.innerHTML = '';
        this.addTerminalLine('assistant-ia $ Terminal effacé');
        
        if (this.elements.statusText) {
            this.elements.statusText.textContent = 'Prêt';
            this.elements.statusText.className = 'status-normal';
        }
        
        if (this.elements.execTimeInfo) {
            this.elements.execTimeInfo.textContent = 'Temps d\'exécution: 0.00s';
        }
    },
    
    /**
     * Copie tout le contenu du terminal
     */
    copyTerminalContent: function() {
        if (!this.elements.terminal) return;
        
        const terminalText = Array.from(this.elements.terminal.querySelectorAll('.terminal-line'))
            .map(line => {
                // Exclure le bouton de copie du texte
                const clone = line.cloneNode(true);
                const copyButton = clone.querySelector('.copy-button');
                if (copyButton) {
                    copyButton.remove();
                }
                return clone.textContent.trim();
            })
            .join('\n');
        
        AssistantIA.copyToClipboard(terminalText);
    },
    
    /**
     * Copie la dernière sortie
     */
    copyLastOutput: function() {
        if (!this.state.lastOutput) {
            AssistantIA.showToast('Aucune sortie à copier', null, 'warning');
            return;
        }
        
        AssistantIA.copyToClipboard(this.state.lastOutput);
    },
    
    /**
     * Place la dernière sortie dans l'input de commande
     */
    lastOutputToPrompt: function() {
        if (!this.elements.commandInput) return;
        if (!this.state.lastOutput) {
            AssistantIA.showToast('Aucune sortie à utiliser', null, 'warning');
            return;
        }
        
        this.elements.commandInput.value = this.state.lastOutput.trim();
        this.elements.commandInput.focus();
        
        // Placer le curseur à la fin
        this.elements.commandInput.selectionStart = 
        this.elements.commandInput.selectionEnd = 
        this.elements.commandInput.value.length;
    },
    
    /**
     * Vérifie si Ollama est en cours d'exécution
     */
    checkOllama: function() {
        this.addTerminalLine("Vérification du service Ollama...", "info");
        
        // Exécuter la commande
        this.executeCommand("python manage-models.py ping");
        
        // Afficher un message de conseil
        setTimeout(() => {
            this.addTerminalLine("Conseil: Si Ollama n'est pas disponible, exécutez 'ollama serve' dans un terminal séparé.", "info");
        }, 2000);
    },
    
    /**
     * Affiche le modal d'inférence
     */
    showInferenceModal: function() {
        if (!this.elements.inferenceModal) return;
        if (!this.elements.modelSelect) return;
        
        // Vérifier si Ollama est en cours d'exécution
        AssistantIA.isOllamaRunning().then(isRunning => {
            if (!isRunning) {
                AssistantIA.showToast("Ollama n'est pas en cours d'exécution. Exécutez 'ollama serve' dans un terminal séparé.", 5000, 'error');
                
                this.addTerminalLine("Erreur: Le service Ollama n'est pas en cours d'exécution.", "error");
                this.addTerminalLine("Exécutez 'ollama serve' dans un terminal séparé pour démarrer le service.", "error");
                return;
            }
            
            // Charger les modèles si nécessaire
            if (this.elements.modelSelect.options.length <= 1 || 
                this.elements.modelSelect.options[0].value === 'loading' || 
                this.elements.modelSelect.options[0].value === 'none') {
                AssistantIA.loadModelsList('modelSelect', data => {
                    if (!data || !data.models || data.models.length === 0) {
                        AssistantIA.showToast("Aucun modèle disponible. Allez dans 'Gestion Ollama' pour en télécharger un.", 5000, 'warning');
                        return;
                    }
                    
                    // Afficher le modal
                    this.elements.inferenceModal.style.display = 'block';
                });
            } else {
                // Afficher le modal
                this.elements.inferenceModal.style.display = 'block';
            }
        });
    },
    
    /**
     * Exécute une inférence avec le modèle sélectionné
     */
/**
 * Exécute une inférence avec le modèle sélectionné
 */
runInference: function() {
    const model = modelSelect.value;
    const prompt = promptInput.value.trim();
    const temperature = temperatureSlider.value;
    const maxTokens = maxTokensSlider.value;
    
    if (!model || model === 'loading' || model === 'none') {
        // Vérifier s'il n'y a aucun modèle disponible
        if (modelSelect.options.length <= 1 || modelSelect.options[0].value === 'none') {
            showToast('Erreur: Aucun modèle disponible. Allez dans "Gestion Ollama" pour en télécharger un.', 5000, true);
            inferenceModal.style.display = 'none';
            return;
        }
        
        showToast('Erreur: Veuillez sélectionner un modèle', 3000, true);
        return;
    }
    
    if (!prompt) {
        showToast('Erreur: Le prompt est vide', 3000, true);
        return;
    }
    
    // Fermer le modal
    inferenceModal.style.display = 'none';
    
    // Mettre à jour l'affichage du modèle actuel
    const currentModelElement = document.getElementById('currentModel');
    if (currentModelElement) {
        currentModelElement.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Modèle: ${model} (en cours d'utilisation...)`;
    }
    
    // Construire la commande d'inférence avec des options explicites
    const command = `python run-inference.py --model ${model} --temperature ${temperature} --max-tokens ${maxTokens} "${prompt}"`;
    
    // Afficher une notification de chargement
    addTerminalLine(`Inférence en cours avec le modèle ${model}...`, 'info');
    
    // Désactiver le bouton d'inférence pendant l'exécution
    if (inferenceBtn) {
        inferenceBtn.disabled = true;
        inferenceBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Inférence en cours...';
        
        // Réactiver le bouton après un délai plus long (30 secondes max)
        setTimeout(function() {
            if (inferenceBtn.disabled) {
                inferenceBtn.disabled = false;
                inferenceBtn.innerHTML = '<i class="fas fa-brain"></i> Inférence directe';
                showToast('L\'inférence prend plus de temps que prévu. Vérifiez le terminal pour les résultats.', 5000);
            }
        }, 30000);
    }
    
    // Exécuter la commande avec un timeout plus long
    fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Réactiver le bouton d'inférence
        if (inferenceBtn) {
            inferenceBtn.disabled = false;
            inferenceBtn.innerHTML = '<i class="fas fa-brain"></i> Inférence directe';
        }
        
        // Restaurer l'affichage du modèle actuel
        if (currentModelElement) {
            currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: ${model}`;
        }
        
        if (data.error) {
            addTerminalLine(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        if (data.stderr) {
            const lines = data.stderr.trim().split('\n');
            lines.forEach(line => {
                addTerminalLine(line, 'error');
            });
        }
        
        // Traiter la sortie standard
        if (data.stdout) {
            // Capturer uniquement la partie générée
            const output = data.stdout;
            const lines = output.split('\n');
            let resultText = '';
            let isResultSection = false;
            
            for (const line of lines) {
                if (line.includes('Texte généré:')) {
                    isResultSection = true;
                    addTerminalLine('---- Résultat de l\'inférence ----', 'success');
                    continue;
                }
                
                if (isResultSection && 
                    !line.includes('Inférence terminée') && 
                    !line.includes('GPU détecté') && 
                    !line.includes('Utilisation mémoire')) {
                    resultText += line + '\n';
                    addTerminalLine(line);
                }
                
                // Afficher aussi les informations de performance
                if (line.includes('Inférence terminée')) {
                    addTerminalLine(line, 'info');
                }
                
                if (line.includes('GPU détecté') || line.includes('Utilisation mémoire')) {
                    addTerminalLine(line, 'info');
                }
            }
            
            if (resultText.trim()) {
                lastOutput = resultText.trim();
            } else {
                // Si la partie générée n'est pas bien identifiée, utiliser toute la sortie
                lastOutput = output;
                if (!isResultSection) {
                    addTerminalLine('Sortie complète :', 'info');
                    lines.forEach(line => {
                        addTerminalLine(line);
                    });
                }
            }
            
            addTerminalLine('---- Fin du résultat ----', 'success');
            
            // Définir ce modèle comme modèle par défaut
            if (model !== currentModelName) {
                updateCurrentModel(model)
                    .then(success => {
                        if (success) {
                            addTerminalLine(`Modèle ${model} défini comme modèle par défaut`, 'info');
                        }
                    });
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'exécution de la commande:', error);
        
        // Réactiver le bouton d'inférence
        if (inferenceBtn) {
            inferenceBtn.disabled = false;
            inferenceBtn.innerHTML = '<i class="fas fa-brain"></i> Inférence directe';
        }
        
        // Restaurer l'affichage du modèle actuel
        if (currentModelElement) {
            currentModelElement.innerHTML = `<i class="fas fa-brain"></i> Modèle: ${model}`;
        }
        
        addTerminalLine(`Erreur: ${error.message}`, 'error');
        
        if (error.message.includes('timeout')) {
            addTerminalLine("L'opération a pris trop de temps. Essayez avec un prompt plus court ou un modèle plus petit.", 'error');
        }
    });
    }
    
    /**
     * Affiche le modal d'explorateur de fichiers
     */
    showFileExplorerModal: function() {
        if (!this.elements.fileExplorerModal) return;
        
        this.elements.fileExplorerModal.style.display = 'block';
        this.exploreFiles('./');
    },
    
    /**
     * Explore les fichiers d'un répertoire
     * @param {string} directory - Répertoire à explorer
     */
    exploreFiles: function(directory) {
        if (!this.elements.fileListContainer) return;
        
        // Afficher le chargement
        this.elements.fileListContainer.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
                Chargement des fichiers...
            </div>
        `;
        
        // Normaliser le chemin
        directory = directory.trim() || './';
        
        // Mettre à jour l'input
        if (this.elements.currentDirInput) {
            this.elements.currentDirInput.value = directory;
        }
        
        // Exécuter la commande ls
        fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: `ls -la "${directory}"` })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                this.elements.fileListContainer.innerHTML = `
                    <div class="error">
                        <i class="fas fa-exclamation-circle"></i> Erreur: ${data.error}
                    </div>`;
                return;
            }
            
            if (data.stderr) {
                this.elements.fileListContainer.innerHTML = `
                    <div class="error">
                        <i class="fas fa-exclamation-circle"></i> ${data.stderr}
                    </div>`;
                return;
            }
            
            // Traiter la sortie
            const lines = data.stdout.trim().split('\n');
            
            // Filtrer les lignes pertinentes (supprimer total, ., etc.)
            const fileLines = lines.filter(line => !line.trim().startsWith('total'));
            
            if (fileLines.length === 0) {
                this.elements.fileListContainer.innerHTML = `
                    <div class="info">
                        <i class="fas fa-info-circle"></i> Répertoire vide
                    </div>`;
                return;
            }
            
            // Construire l'affichage des fichiers
            let fileListHTML = '';
            
            fileLines.forEach(line => {
                const parts = line.trim().split(/\s+/);
                if (parts.length < 9) return; // Ligne invalide
                
                const permissions = parts[0];
                const owner = parts[2];
                const group = parts[3];
                const size = parts[4];
                const date = `${parts[5]} ${parts[6]} ${parts[7]}`;
                
                // Le nom du fichier est tout ce qui reste
                const nameIndex = line.indexOf(parts[7]) + parts[7].length + 1;
                const name = line.substring(nameIndex);
                
                // Déterminer le type de fichier
                let icon = '<i class="fas fa-file"></i>';
                let itemClass = 'file-item';
                let fileType = '';
                
                if (permissions.startsWith('d')) {
                    icon = '<i class="fas fa-folder"></i>';
                    itemClass = 'dir-item';
                    fileType = 'directory';
                } else if (permissions.includes('x')) {
                    icon = '<i class="fas fa-file-code"></i>';
                    fileType = 'executable';
                } else if (name.endsWith('.py')) {
                    icon = '<i class="fab fa-python"></i>';
                    fileType = 'python';
                } else if (name.endsWith('.js')) {
                    icon = '<i class="fab fa-js"></i>';
                    fileType = 'javascript';
                } else if (name.endsWith('.css')) {
                    icon = '<i class="fab fa-css3"></i>';
                    fileType = 'css';
                } else if (name.endsWith('.html')) {
                    icon = '<i class="fab fa-html5"></i>';
                    fileType = 'html';
                } else if (name.endsWith('.md')) {
                    icon = '<i class="fas fa-file-alt"></i>';
                    fileType = 'markdown';
                } else if (['.jpg', '.jpeg', '.png', '.gif', '.bmp'].some(ext => name.toLowerCase().endsWith(ext))) {
                    icon = '<i class="fas fa-image"></i>';
                    fileType = 'image';
                } else if (['.mp3', '.wav', '.ogg', '.flac'].some(ext => name.toLowerCase().endsWith(ext))) {
                    icon = '<i class="fas fa-music"></i>';
                    fileType = 'audio';
                } else if (['.mp4', '.avi', '.mov', '.mkv'].some(ext => name.toLowerCase().endsWith(ext))) {
                    icon = '<i class="fas fa-video"></i>';
                    fileType = 'video';
                } else if (['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'].some(ext => name.toLowerCase().endsWith(ext))) {
                    icon = '<i class="fas fa-file-pdf"></i>';
                    fileType = 'document';
                } else if (['.zip', '.tar', '.gz', '.rar', '.7z'].some(ext => name.toLowerCase().endsWith(ext))) {
                    icon = '<i class="fas fa-file-archive"></i>';
                    fileType = 'archive';
                }
                
                // Ne pas afficher les fichiers cachés si ce n'est pas demandé
                if (name.startsWith('.') && name !== '..' && name !== '.') {
                    fileType += ' hidden-file';
                }
                
                // Créer l'élément HTML
                fileListHTML += `
                    <div class="${itemClass} ${fileType}" data-name="${name}" data-path="${directory === './' ? name : directory + '/' + name}">
                        ${icon} <span class="file-name">${name}</span>
                        <span class="file-details">
                            <span class="file-size">${size}</span>
                            <span class="file-date">${date}</span>
                            <span class="file-perms">${permissions}</span>
                        </span>
                    </div>
                `;
            });
            
            // Mettre à jour le conteneur
            this.elements.fileListContainer.innerHTML = fileListHTML;
            
            // Ajouter les écouteurs d'événements pour les répertoires
            document.querySelectorAll('.dir-item').forEach(dirItem => {
                dirItem.addEventListener('click', () => {
                    const path = dirItem.getAttribute('data-path');
                    this.exploreFiles(path);
                });
            });
            
            // Ajouter les écouteurs d'événements pour les fichiers
            document.querySelectorAll('.file-item').forEach(fileItem => {
                fileItem.addEventListener('click', () => {
                    const path = fileItem.getAttribute('data-path');
                    const name = fileItem.getAttribute('data-name');
                    
                    // Fermer le modal
                    this.elements.fileExplorerModal.style.display = 'none';
                    
                    // Construire la commande en fonction du type de fichier
                    let command = '';
                    
                    // Vérifier si c'est un fichier binaire
                    if (fileItem.classList.contains('image') || 
                        fileItem.classList.contains('audio') || 
                        fileItem.classList.contains('video') || 
                        fileItem.classList.contains('document') || 
                        fileItem.classList.contains('archive')) {
                        command = `file "${path}"`;
                    } else {
                        command = `cat "${path}"`;
                    }
                    
                    // Exécuter la commande
                    this.executeCommand(command);
                });
            });
        })
        .catch(error => {
            console.error('Erreur lors de l\'exploration des fichiers:', error);
            this.elements.fileListContainer.innerHTML = `
                <div class="error">
                    <i class="fas fa-exclamation-circle"></i> Erreur de connexion: ${error.message}
                </div>`;
        });
    },
    
    /**
     * Active/désactive la reconnaissance vocale
     */
    toggleSpeechRecognition: function() {
        // Vérifier si la reconnaissance vocale est supportée
        if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
            AssistantIA.showToast('La reconnaissance vocale n\'est pas supportée par votre navigateur', null, 'error');
            return;
        }
        
        if (this.state.isRecording) {
            // Arrêter l'enregistrement
            this.stopSpeechRecognition();
        } else {
            // Démarrer l'enregistrement
            this.startSpeechRecognition();
        }
    },
    
    /**
     * Démarre la reconnaissance vocale
     */
    startSpeechRecognition: function() {
        if (this.state.isRecording) return;
        
        // Créer l'objet de reconnaissance vocale
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configurer la reconnaissance
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'fr-FR';
        
        // Ajouter les écouteurs d'événements
        this.recognition.onstart = () => {
            this.state.isRecording = true;
            
            if (this.elements.micBtn) {
                this.elements.micBtn.classList.add('mic-active');
            }
            
            // Simuler une visualisation audio
            this.startVisualization();
            
            AssistantIA.showToast('Reconnaissance vocale activée', null, 'info');
        };
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (finalTranscript) {
                if (this.elements.commandInput) {
                    this.elements.commandInput.value = finalTranscript;
                }
            } else if (interimTranscript) {
                if (this.elements.commandInput) {
                    this.elements.commandInput.value = interimTranscript;
                }
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Erreur de reconnaissance vocale:', event.error);
            this.stopSpeechRecognition();
            AssistantIA.showToast(`Erreur de reconnaissance vocale: ${event.error}`, null, 'error');
        };
        
        this.recognition.onend = () => {
            // Arrêter la visualisation
            this.stopVisualization();
            
            // Exécuter la commande si disponible
            if (this.elements.commandInput && this.elements.commandInput.value.trim()) {
                // Attendre un peu pour permettre de voir la commande
                setTimeout(() => {
                    this.executeCommand(this.elements.commandInput.value);
                }, 500);
            }
            
            this.state.isRecording = false;
            
            if (this.elements.micBtn) {
                this.elements.micBtn.classList.remove('mic-active');
            }
        };
        
        // Démarrer la reconnaissance
        try {
            this.recognition.start();
        } catch (e) {
            console.error('Erreur lors du démarrage de la reconnaissance vocale:', e);
            AssistantIA.showToast('Erreur lors du démarrage de la reconnaissance vocale', null, 'error');
        }
    },
    
    /**
     * Arrête la reconnaissance vocale
     */
    stopSpeechRecognition: function() {
        if (!this.state.isRecording || !this.recognition) return;
        
        try {
            this.recognition.stop();
        } catch (e) {
            console.error('Erreur lors de l\'arrêt de la reconnaissance vocale:', e);
        }
        
        this.state.isRecording = false;
        
        if (this.elements.micBtn) {
            this.elements.micBtn.classList.remove('mic-active');
        }
        
        // Arrêter la visualisation
        this.stopVisualization();
    },
    
    /**
     * Démarre une visualisation audio simulée
     */
    startVisualization: function() {
        if (!this.elements.micVisualization) return;
        
        // Arrêter toute visualisation existante
        this.stopVisualization();
        
        // Démarrer une nouvelle visualisation
        this.state.visualizationInterval = setInterval(() => {
            // Simuler un niveau audio aléatoire
            const level = Math.random() * 100;
            this.elements.micVisualization.style.height = `${level}%`;
        }, 100);
    },
    
    /**
     * Arrête la visualisation audio
     */
    stopVisualization: function() {
        if (this.state.visualizationInterval) {
            clearInterval(this.state.visualizationInterval);
            this.state.visualizationInterval = null;
        }
        
        if (this.elements.micVisualization) {
            this.elements.micVisualization.style.height = '0';
        }
    },
    
    /**
     * Nettoie les ressources utilisées par le module
     */
    cleanup: function() {
        // Arrêter la reconnaissance vocale
        this.stopSpeechRecognition();
        
        // Arrêter la visualisation
        this.stopVisualization();
        
        // Vider l'historique des commandes
        this.state.commandHistory = [];
        this.state.currentHistoryIndex = -1;
    }
};

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    ConsoleManager.init();
});

// S'assurer que les ressources sont nettoyées quand la page est déchargée
window.addEventListener('beforeunload', function() {
    ConsoleManager.cleanup();
});
