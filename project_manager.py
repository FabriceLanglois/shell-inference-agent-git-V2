import os
import json
import shutil
import time
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectManager:
    """
    Gestionnaire de projets pour l'Assistant IA.
    Gère la création, modification et suppression des projets et documents.
    """
    
    def __init__(self, projects_dir="projects"):
        """
        Initialise le gestionnaire de projets.
        
        Args:
            projects_dir (str): Chemin vers le répertoire des projets
        """
        self.projects_dir = projects_dir
        self.ensure_projects_dir()
    
    def ensure_projects_dir(self):
        """Crée le répertoire de projets s'il n'existe pas"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
            logger.info(f"Répertoire de projets créé: {self.projects_dir}")
    
    def get_projects(self):
        """
        Récupère la liste de tous les projets.
        
        Returns:
            list: Liste de dictionnaires contenant les informations des projets
        """
        projects = []
        self.ensure_projects_dir()
        
        for project_id in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_id)
            
            # Ignorer .gitkeep ou autres fichiers
            if not os.path.isdir(project_path):
                continue
            
            # Charger les métadonnées du projet
            metadata_path = os.path.join(project_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # S'assurer que les champs obligatoires sont présents
                    if not all(key in metadata for key in ['name', 'created_at']):
                        logger.warning(f"Métadonnées incomplètes pour le projet {project_id}")
                        continue
                    
                    # Ajouter le chemin et l'ID
                    metadata['id'] = project_id
                    metadata['path'] = project_path
                    
                    # Mettre à jour la date de dernière modification si elle n'existe pas
                    if 'updated_at' not in metadata:
                        metadata['updated_at'] = metadata['created_at']
                    
                    projects.append(metadata)
                except Exception as e:
                    logger.error(f"Erreur lors du chargement des métadonnées pour {project_id}: {e}")
            else:
                logger.warning(f"Pas de métadonnées pour le projet {project_id}, ignoré")
        
        # Trier par date de mise à jour (plus récent d'abord)
        projects.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return projects
    
    def get_project(self, project_id):
        """
        Récupère les informations d'un projet spécifique.
        
        Args:
            project_id (str): ID du projet
            
        Returns:
            dict: Informations du projet ou None si non trouvé
        """
        if not self._project_exists(project_id):
            return None
        
        metadata_path = os.path.join(self.projects_dir, project_id, "metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Ajouter l'ID et le chemin
            metadata['id'] = project_id
            metadata['path'] = os.path.join(self.projects_dir, project_id)
            
            return metadata
        except Exception as e:
            logger.error(f"Erreur lors du chargement du projet {project_id}: {e}")
            return None
    
    def create_project(self, name, description=""):
        """
        Crée un nouveau projet.
        
        Args:
            name (str): Nom du projet
            description (str): Description du projet
            
        Returns:
            dict: Informations du projet créé ou None en cas d'erreur
        """
        try:
            # Créer un ID unique basé sur le nom et le timestamp
            timestamp = int(time.time())
            project_id = f"{self._clean_name(name)}_{timestamp}"
            project_path = os.path.join(self.projects_dir, project_id)
            
            # Vérifier si le répertoire existe déjà
            if os.path.exists(project_path):
                logger.error(f"Le projet {project_id} existe déjà")
                return None
            
            # Créer le répertoire du projet
            os.makedirs(project_path)
            
            # Créer les métadonnées
            now = datetime.now().isoformat()
            metadata = {
                "name": name,
                "description": description,
                "created_at": now,
                "updated_at": now,
                "github_repo": None
            }
            
            # Sauvegarder les métadonnées
            metadata_path = os.path.join(project_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Ajouter l'ID et le chemin
            metadata['id'] = project_id
            metadata['path'] = project_path
            
            logger.info(f"Projet créé: {name} ({project_id})")
            return metadata
        except Exception as e:
            logger.error(f"Erreur lors de la création du projet {name}: {e}")
            # Nettoyer en cas d'erreur
            if 'project_path' in locals() and os.path.exists(project_path):
                shutil.rmtree(project_path)
            return None
    
    def update_project(self, project_id, update_data):
        """
        Met à jour les informations d'un projet.
        
        Args:
            project_id (str): ID du projet
            update_data (dict): Données à mettre à jour
            
        Returns:
            dict: Informations du projet mis à jour ou None en cas d'erreur
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            metadata_path = os.path.join(self.projects_dir, project_id, "metadata.json")
            
            # Lire les métadonnées existantes
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Mettre à jour les champs autorisés
            allowed_fields = ['name', 'description', 'github_repo']
            for field in allowed_fields:
                if field in update_data:
                    metadata[field] = update_data[field]
            
            # Mettre à jour la date de modification
            metadata['updated_at'] = datetime.now().isoformat()
            
            # Sauvegarder les métadonnées
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Ajouter l'ID et le chemin
            metadata['id'] = project_id
            metadata['path'] = os.path.join(self.projects_dir, project_id)
            
            logger.info(f"Projet mis à jour: {project_id}")
            return metadata
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du projet {project_id}: {e}")
            return None
    
    def delete_project(self, project_id):
        """
        Supprime un projet.
        
        Args:
            project_id (str): ID du projet
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        if not self._project_exists(project_id):
            return False
        
        try:
            project_path = os.path.join(self.projects_dir, project_id)
            shutil.rmtree(project_path)
            logger.info(f"Projet supprimé: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet {project_id}: {e}")
            return False
    
    def get_project_files(self, project_id):
        """
        Récupère la liste des fichiers d'un projet.
        
        Args:
            project_id (str): ID du projet
            
        Returns:
            list: Liste de dictionnaires contenant les informations des fichiers
        """
        if not self._project_exists(project_id):
            return []
        
        files = []
        project_path = os.path.join(self.projects_dir, project_id)
        
        try:
            # Parcourir récursivement le répertoire du projet
            for root, dirs, filenames in os.walk(project_path):
                # Ignorer les fichiers cachés et les métadonnées
                for filename in filenames:
                    if filename.startswith('.') or filename == 'metadata.json':
                        continue
                    
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, project_path)
                    
                    # Déterminer le type de fichier
                    extension = os.path.splitext(filename)[1].lower()
                    file_type = self._get_file_type(extension)
                    
                    # Obtenir la taille du fichier
                    size = os.path.getsize(file_path)
                    size_formatted = self._format_size(size)
                    
                    # Obtenir les dates
                    created = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                    updated = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "type": file_type,
                        "extension": extension,
                        "size": size,
                        "size_formatted": size_formatted,
                        "created_at": created,
                        "updated_at": updated
                    })
            
            # Trier par nom
            files.sort(key=lambda x: x['name'])
            return files
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fichiers pour {project_id}: {e}")
            return []
    
    def get_document(self, project_id, document_path):
        """
        Récupère les informations d'un document spécifique.
        
        Args:
            project_id (str): ID du projet
            document_path (str): Chemin relatif du document
            
        Returns:
            dict: Informations du document ou None si non trouvé
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            full_path = os.path.join(self.projects_dir, project_id, document_path)
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return None
            
            # Obtenir les informations de base
            filename = os.path.basename(full_path)
            extension = os.path.splitext(filename)[1].lower()
            file_type = self._get_file_type(extension)
            
            # Obtenir la taille
            size = os.path.getsize(full_path)
            size_formatted = self._format_size(size)
            
            # Obtenir les dates
            created = datetime.fromtimestamp(os.path.getctime(full_path)).isoformat()
            updated = datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            
            return {
                "name": filename,
                "path": document_path,
                "type": file_type,
                "extension": extension,
                "size": size,
                "size_formatted": size_formatted,
                "created_at": created,
                "updated_at": updated
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du document {document_path} pour {project_id}: {e}")
            return None
    
    def get_document_content(self, project_id, document_path):
        """
        Récupère le contenu d'un document.
        
        Args:
            project_id (str): ID du projet
            document_path (str): Chemin relatif du document
            
        Returns:
            str: Contenu du document ou None si non trouvé
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            full_path = os.path.join(self.projects_dir, project_id, document_path)
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return None
            
            # Lire le contenu
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du document {document_path} pour {project_id}: {e}")
            return None
    
    def create_document(self, project_id, name, content="", document_type="text"):
        """
        Crée un nouveau document dans un projet.
        
        Args:
            project_id (str): ID du projet
            name (str): Nom du document
            content (str): Contenu du document
            document_type (str): Type du document (code, text, markdown)
            
        Returns:
            dict: Informations du document créé ou None en cas d'erreur
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            # Nettoyer le chemin pour éviter tout problème
            document_path = self._clean_path(name)
            full_path = os.path.join(self.projects_dir, project_id, document_path)
            
            # Créer les répertoires intermédiaires si nécessaire
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(full_path):
                logger.warning(f"Le document {document_path} existe déjà pour {project_id}")
                return None
            
            # Écrire le contenu
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Mettre à jour la date de modification du projet
            self._update_project_timestamp(project_id)
            
            # Obtenir les informations du document
            document = self.get_document(project_id, document_path)
            
            logger.info(f"Document créé: {document_path} pour {project_id}")
            return document
        except Exception as e:
            logger.error(f"Erreur lors de la création du document {name} pour {project_id}: {e}")
            return None
    
    def update_document(self, project_id, document_path, content):
        """
        Met à jour le contenu d'un document.
        
        Args:
            project_id (str): ID du projet
            document_path (str): Chemin relatif du document
            content (str): Nouveau contenu
            
        Returns:
            dict: Informations du document mis à jour ou None en cas d'erreur
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            full_path = os.path.join(self.projects_dir, project_id, document_path)
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return None
            
            # Écrire le nouveau contenu
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Mettre à jour la date de modification du projet
            self._update_project_timestamp(project_id)
            
            # Obtenir les informations du document
            document = self.get_document(project_id, document_path)
            
            logger.info(f"Document mis à jour: {document_path} pour {project_id}")
            return document
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du document {document_path} pour {project_id}: {e}")
            return None
    
    def delete_document(self, project_id, document_path):
        """
        Supprime un document.
        
        Args:
            project_id (str): ID du projet
            document_path (str): Chemin relatif du document
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        if not self._project_exists(project_id):
            return False
        
        try:
            full_path = os.path.join(self.projects_dir, project_id, document_path)
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return False
            
            # Supprimer le fichier
            os.remove(full_path)
            
            # Mettre à jour la date de modification du projet
            self._update_project_timestamp(project_id)
            
            logger.info(f"Document supprimé: {document_path} pour {project_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {document_path} pour {project_id}: {e}")
            return False
    
    def import_folder(self, source_path, name, description=""):
        """
        Importe un dossier en tant que nouveau projet.
        
        Args:
            source_path (str): Chemin du dossier à importer
            name (str): Nom du projet
            description (str): Description du projet
            
        Returns:
            dict: Informations du projet créé ou None en cas d'erreur
        """
        try:
            # Vérifier si le dossier source existe
            if not os.path.exists(source_path) or not os.path.isdir(source_path):
                logger.error(f"Le dossier source {source_path} n'existe pas")
                return None
            
            # Créer un nouveau projet
            project = self.create_project(name, description)
            if not project:
                return None
            
            project_id = project['id']
            project_path = os.path.join(self.projects_dir, project_id)
            
            # Copier les fichiers (en excluant les fichiers cachés et répertoires git)
            for root, dirs, files in os.walk(source_path):
                # Exclure les répertoires cachés et .git
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.') or file == 'metadata.json':
                        continue
                    
                    src_file = os.path.join(root, file)
                    # Calculer le chemin relatif
                    rel_path = os.path.relpath(src_file, source_path)
                    dst_file = os.path.join(project_path, rel_path)
                    
                    # Créer les répertoires intermédiaires
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    
                    # Copier le fichier
                    shutil.copy2(src_file, dst_file)
            
            logger.info(f"Dossier importé en tant que projet: {name} ({project_id})")
            return project
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du dossier {source_path}: {e}")
            # Nettoyer en cas d'erreur
            if 'project' in locals() and project:
                self.delete_project(project['id'])
            return None
    
    def import_file(self, project_id, source_path, target_path=None):
        """
        Importe un fichier dans un projet.
        
        Args:
            project_id (str): ID du projet
            source_path (str): Chemin du fichier à importer
            target_path (str): Chemin cible relatif au projet (optionnel)
            
        Returns:
            dict: Informations du document importé ou None en cas d'erreur
        """
        if not self._project_exists(project_id):
            return None
        
        try:
            # Vérifier si le fichier source existe
            if not os.path.exists(source_path) or not os.path.isfile(source_path):
                logger.error(f"Le fichier source {source_path} n'existe pas")
                return None
            
            # Déterminer le chemin cible
            if not target_path:
                target_path = os.path.basename(source_path)
            
            # Nettoyer le chemin cible
            target_path = self._clean_path(target_path)
            full_target_path = os.path.join(self.projects_dir, project_id, target_path)
            
            # Créer les répertoires intermédiaires
            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(source_path, full_target_path)
            
            # Mettre à jour la date de modification du projet
            self._update_project_timestamp(project_id)
            
            # Obtenir les informations du document
            document = self.get_document(project_id, target_path)
            
            logger.info(f"Fichier importé: {source_path} vers {target_path} pour {project_id}")
            return document
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier {source_path} pour {project_id}: {e}")
            return None
    
    def analyze_document(self, project_id, document_path, model=""):
        """
        Analyse un document avec l'IA.
        
        Args:
            project_id (str): ID du projet
            document_path (str): Chemin relatif du document
            model (str): Modèle à utiliser (optionnel)
            
        Returns:
            dict: Résultat de l'analyse ou None en cas d'erreur
        """
        document = self.get_document(project_id, document_path)
        if not document:
            return None
        
        content = self.get_document_content(project_id, document_path)
        if content is None:
            return None
        
        # Ici, vous pourriez intégrer un appel à l'API Ollama
        # Pour le moment, nous simulons une analyse simple
        analysis = f"Analyse du document {document['name']} (type: {document['type']}):\n\n"
        
        if document['type'] == 'code':
            analysis += "1. Structure du code:\n"
            analysis += "   - Le code est bien structuré.\n"
            analysis += "   - Plusieurs fonctions sont définies.\n\n"
            analysis += "2. Points d'amélioration:\n"
            analysis += "   - La documentation pourrait être améliorée.\n"
            analysis += "   - Certaines fonctions sont trop longues.\n\n"
            analysis += "3. Bonnes pratiques:\n"
            analysis += "   - Nommage cohérent des variables.\n"
            analysis += "   - Structure modulaire appropriée.\n"
        elif document['type'] == 'markdown' or document['type'] == 'text':
            analysis += "1. Structure du document:\n"
            analysis += "   - Document bien organisé.\n"
            analysis += "   - Plusieurs sections identifiées.\n\n"
            analysis += "2. Points d'amélioration:\n"
            analysis += "   - Certaines phrases sont trop longues.\n"
            analysis += "   - Des exemples supplémentaires seraient utiles.\n\n"
            analysis += "3. Points forts:\n"
            analysis += "   - Explications claires.\n"
            analysis += "   - Bonne progression logique."
        
        return {
            "document": document,
            "model": model or "default_model",
            "analysis": analysis
        }
    
    def _project_exists(self, project_id):
        """
        Vérifie si un projet existe.
        
        Args:
            project_id (str): ID du projet
            
        Returns:
            bool: True si le projet existe, False sinon
        """
        project_path = os.path.join(self.projects_dir, project_id)
        return os.path.exists(project_path) and os.path.isdir(project_path)
    
    def _update_project_timestamp(self, project_id):
        """
        Met à jour la date de modification d'un projet.
        
        Args:
            project_id (str): ID du projet
        """
        try:
            metadata_path = os.path.join(self.projects_dir, project_id, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metadata['updated_at'] = datetime.now().isoformat()
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du timestamp pour {project_id}: {e}")
    
    def _clean_name(self, name):
        """
        Nettoie un nom pour qu'il soit utilisable en tant que répertoire.
        
        Args:
            name (str): Nom à nettoyer
            
        Returns:
            str: Nom nettoyé
        """
        # Remplacer les espaces par des underscores et supprimer les caractères spéciaux
        import re
        name = re.sub(r'[^\w\-]', '_', name)
        # Limiter la longueur
        return name[:50]
    
    def _clean_path(self, path):
        """
        Nettoie un chemin pour éviter les problèmes de sécurité.
        
        Args:
            path (str): Chemin à nettoyer
            
        Returns:
            str: Chemin nettoyé
        """
        # Supprimer les éventuels ../
        import posixpath
        path = posixpath.normpath(path)
        # S'assurer que le chemin ne commence pas par /
        if path.startswith('/'):
            path = path[1:]
        return path
    
    def _get_file_type(self, extension):
        """
        Détermine le type de fichier en fonction de son extension.
        
        Args:
            extension (str): Extension du fichier
            
        Returns:
            str: Type de fichier (code, markdown, text, image, document)
        """
        code_extensions = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.sh', '.ts', '.jsx', '.tsx', '.php']
        markdown_extensions = ['.md', '.markdown']
        text_extensions = ['.txt', '.rst', '.log', '.ini', '.csv', '.json', '.yml', '.yaml', '.xml']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt']
        
        if extension in code_extensions:
            return 'code'
        elif extension in markdown_extensions:
            return 'markdown'
        elif extension in text_extensions:
            return 'text'
        elif extension in image_extensions:
            return 'image'
        elif extension in document_extensions:
            return 'document'
        else:
            return 'text'  # Par défaut
    
    def _format_size(self, size_bytes):
        """
        Formate une taille en bytes en une chaîne lisible.
        
        Args:
            size_bytes (int): Taille en bytes
            
        Returns:
            str: Taille formatée
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"