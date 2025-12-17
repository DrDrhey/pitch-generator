"""
Module de gestion des projets (sauvegarde/chargement)
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import streamlit as st


class ProjectManager:
    """Gère la sauvegarde et le chargement des projets"""
    
    def __init__(self, storage_dir: str = None):
        """
        Initialise le gestionnaire de projets
        
        Pour Streamlit Cloud, utilise st.session_state ou un stockage cloud.
        Pour une utilisation locale, utilise un dossier local.
        """
        self.storage_dir = storage_dir or self._get_storage_dir()
        self._ensure_storage_exists()
    
    def _get_storage_dir(self) -> str:
        """Détermine le répertoire de stockage"""
        # En local
        if os.path.exists('/tmp'):
            return '/tmp/pitch_generator_projects'
        else:
            return os.path.join(os.path.expanduser('~'), '.pitch_generator', 'projects')
    
    def _ensure_storage_exists(self):
        """S'assure que le répertoire de stockage existe"""
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_session_projects(self) -> Dict:
        """Récupère les projets depuis la session Streamlit"""
        if 'saved_projects' not in st.session_state:
            st.session_state.saved_projects = {}
        return st.session_state.saved_projects
    
    def save_project(self, name: str, data: Dict) -> str:
        """
        Sauvegarde un projet
        
        Args:
            name: Nom du projet
            data: Données du projet (pitch, sequencer, decoupage, etc.)
        
        Returns:
            ID du projet sauvegardé
        """
        project_id = str(uuid.uuid4())[:8]
        
        project = {
            'id': project_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'data': self._serialize_data(data)
        }
        
        # Sauvegarder en session
        projects = self._get_session_projects()
        projects[project_id] = project
        
        # Sauvegarder sur disque si possible
        try:
            file_path = os.path.join(self.storage_dir, f"{project_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Impossible de sauvegarder sur disque: {e}")
        
        return project_id
    
    def _serialize_data(self, data: Dict) -> Dict:
        """Sérialise les données pour la sauvegarde"""
        serialized = {}
        
        for key, value in data.items():
            if key == 'images_data':
                # Ne pas sauvegarder les données binaires des images
                serialized[key] = [
                    {k: v for k, v in img.items() if k not in ['data', 'base64']}
                    for img in (value or [])
                ]
            elif key == 'analysis_results':
                # Convertir l'analyse en dict si nécessaire
                if hasattr(value, 'to_dict'):
                    serialized[key] = value.to_dict()
                else:
                    serialized[key] = value
            else:
                serialized[key] = value
        
        return serialized
    
    def load_project(self, project_id: str) -> Optional[Dict]:
        """
        Charge un projet
        
        Args:
            project_id: ID du projet
        
        Returns:
            Données du projet ou None si non trouvé
        """
        # Chercher en session d'abord
        projects = self._get_session_projects()
        if project_id in projects:
            return projects[project_id]['data']
        
        # Chercher sur disque
        try:
            file_path = os.path.join(self.storage_dir, f"{project_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    project = json.load(f)
                    return project.get('data')
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
        
        return None
    
    def list_projects(self) -> List[Dict]:
        """
        Liste tous les projets sauvegardés
        
        Returns:
            Liste des projets avec métadonnées
        """
        projects = []
        
        # Projets en session
        session_projects = self._get_session_projects()
        for pid, project in session_projects.items():
            projects.append({
                'id': project['id'],
                'name': project['name'],
                'created_at': project.get('created_at'),
                'updated_at': project.get('updated_at'),
                'source': 'session'
            })
        
        # Projets sur disque
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    pid = filename[:-5]
                    if pid not in session_projects:
                        file_path = os.path.join(self.storage_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            project = json.load(f)
                            projects.append({
                                'id': project['id'],
                                'name': project['name'],
                                'created_at': project.get('created_at'),
                                'updated_at': project.get('updated_at'),
                                'source': 'disk'
                            })
        except Exception as e:
            print(f"Erreur lors du listing: {e}")
        
        # Trier par date de mise à jour
        projects.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return projects
    
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet
        
        Args:
            project_id: ID du projet
        
        Returns:
            True si supprimé, False sinon
        """
        deleted = False
        
        # Supprimer de la session
        projects = self._get_session_projects()
        if project_id in projects:
            del projects[project_id]
            deleted = True
        
        # Supprimer du disque
        try:
            file_path = os.path.join(self.storage_dir, f"{project_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")
        
        return deleted
    
    def update_project(self, project_id: str, data: Dict) -> bool:
        """
        Met à jour un projet existant
        
        Args:
            project_id: ID du projet
            data: Nouvelles données
        
        Returns:
            True si mis à jour, False sinon
        """
        projects = self._get_session_projects()
        
        if project_id in projects:
            projects[project_id]['data'] = self._serialize_data(data)
            projects[project_id]['updated_at'] = datetime.now().isoformat()
            
            # Mettre à jour sur disque aussi
            try:
                file_path = os.path.join(self.storage_dir, f"{project_id}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(projects[project_id], f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            
            return True
        
        return False
    
    def export_project(self, project_id: str, export_format: str = 'json') -> Optional[str]:
        """
        Exporte un projet dans un format spécifique
        
        Args:
            project_id: ID du projet
            export_format: Format d'export ('json', 'md')
        
        Returns:
            Contenu exporté ou None
        """
        project_data = self.load_project(project_id)
        
        if not project_data:
            return None
        
        if export_format == 'json':
            return json.dumps(project_data, ensure_ascii=False, indent=2)
        
        elif export_format == 'md':
            md_content = f"""# {project_data.get('name', 'Projet sans titre')}

## Pitch

{project_data.get('pitch', '')}

---

## Séquencier

{project_data.get('sequencer', '')}

---

## Découpage technique

{project_data.get('decoupage', '')}

---

## Images de référence

"""
            images = project_data.get('images_data', [])
            for img in images:
                md_content += f"- {img.get('name', 'Sans nom')}\n"
            
            return md_content
        
        return None


class CloudProjectManager(ProjectManager):
    """
    Version cloud du gestionnaire utilisant Firebase/Firestore
    (À implémenter si stockage persistant cloud nécessaire)
    """
    
    def __init__(self, firebase_config: Dict = None):
        self.firebase_config = firebase_config
        # Initialiser Firebase si config fournie
        if firebase_config:
            self._init_firebase()
        else:
            # Fallback sur le stockage local
            super().__init__()
    
    def _init_firebase(self):
        """Initialise la connexion Firebase"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            cred = credentials.Certificate(self.firebase_config)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except ImportError:
            print("firebase-admin non installé, utilisation du stockage local")
            super().__init__()
        except Exception as e:
            print(f"Erreur Firebase: {e}")
            super().__init__()
