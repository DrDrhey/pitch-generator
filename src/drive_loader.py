"""
Module de chargement des images depuis Google Drive
Version adaptée pour Streamlit Cloud (sans OAuth)
"""

import os
import re
import io
import base64
import requests
from typing import List, Dict, Optional, Callable
from PIL import Image


class DriveLoader:
    """
    Gère le chargement des images depuis Google Drive
    Fonctionne avec les dossiers partagés publiquement (sans OAuth)
    """
    
    def __init__(self):
        self.session = requests.Session()
        # Headers pour simuler un navigateur
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_folder_id(self, url: str) -> str:
        """Extrait l'ID du dossier depuis une URL Google Drive"""
        patterns = [
            r'folders/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{25,})$'  # ID direct
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Impossible d'extraire l'ID du dossier depuis : {url}")
    
    def list_images_from_public_folder(self, folder_id: str) -> List[Dict]:
        """
        Liste les images d'un dossier Drive partagé publiquement
        Utilise le scraping de la page HTML du dossier
        """
        # URL de visualisation du dossier
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        
        try:
            response = self.session.get(folder_url)
            response.raise_for_status()
            
            # Extraire les IDs des fichiers depuis le HTML
            # Pattern pour trouver les IDs de fichiers dans le HTML de Google Drive
            file_pattern = r'\["([a-zA-Z0-9_-]{25,50})","([^"]+\.(jpg|jpeg|png|gif|webp|bmp))"'
            matches = re.findall(file_pattern, response.text, re.IGNORECASE)
            
            images = []
            seen_ids = set()
            
            for match in matches:
                file_id = match[0]
                file_name = match[1]
                
                if file_id not in seen_ids:
                    seen_ids.add(file_id)
                    images.append({
                        'id': file_id,
                        'name': file_name,
                        'mime_type': self._get_mime_type(file_name)
                    })
            
            # Si le parsing HTML ne fonctionne pas, essayer une approche alternative
            if not images:
                images = self._list_via_export(folder_id)
            
            return images
            
        except Exception as e:
            print(f"Erreur lors du listing: {e}")
            # Fallback: retourner une liste vide
            return []
    
    def _get_mime_type(self, filename: str) -> str:
        """Détermine le type MIME depuis l'extension"""
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _list_via_export(self, folder_id: str) -> List[Dict]:
        """Méthode alternative pour lister les fichiers"""
        # Cette méthode utilise l'API publique de téléchargement
        return []
    
    def download_image(self, file_id: str, max_size: int = 1024) -> bytes:
        """Télécharge une image depuis Google Drive (fichier partagé publiquement)"""
        
        # URL de téléchargement direct
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        try:
            response = self.session.get(download_url, stream=True)
            
            # Gérer la page de confirmation pour les gros fichiers
            if 'text/html' in response.headers.get('Content-Type', ''):
                # Chercher le lien de confirmation
                confirm_token = None
                for key, value in response.cookies.items():
                    if key.startswith('download_warning'):
                        confirm_token = value
                        break
                
                if confirm_token:
                    download_url = f"{download_url}&confirm={confirm_token}"
                    response = self.session.get(download_url, stream=True)
            
            response.raise_for_status()
            
            # Lire le contenu
            image_data = response.content
            
            # Redimensionner pour optimiser la mémoire
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img_format = 'JPEG'
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(output, format=img_format, quality=85)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Erreur téléchargement {file_id}: {e}")
            raise
    
    def download_image_via_thumbnail(self, file_id: str, size: int = 1024) -> bytes:
        """Télécharge via l'URL de thumbnail (plus fiable pour les images)"""
        
        # URL du thumbnail haute résolution
        thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"
        
        try:
            response = self.session.get(thumb_url)
            response.raise_for_status()
            return response.content
        except:
            # Fallback sur le téléchargement direct
            return self.download_image(file_id)
    
    def get_thumbnail_url(self, file_id: str, size: int = 200) -> str:
        """Génère l'URL de la vignette"""
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"
    
    def load_from_url(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """
        Charge toutes les images d'un dossier Drive partagé publiquement
        
        Returns:
            Liste de dictionnaires contenant:
            - id: ID du fichier
            - name: Nom du fichier
            - data: Données de l'image en bytes
            - thumbnail: URL de la vignette
            - base64: Image encodée en base64
        """
        folder_id = self.extract_folder_id(url)
        
        if progress_callback:
            progress_callback(0, "Récupération de la liste des images...")
        
        files = self.list_images_from_public_folder(folder_id)
        total = len(files)
        
        if total == 0:
            raise ValueError(
                "Aucune image trouvée. Vérifiez que :\n"
                "1. Le dossier contient des images (jpg, png, gif, webp)\n"
                "2. Le dossier est partagé avec 'Tous ceux qui ont le lien'\n"
                "3. Le lien est correct"
            )
        
        images = []
        
        for idx, file_info in enumerate(files):
            if progress_callback:
                progress = (idx + 1) / total
                progress_callback(progress, f"Chargement : {file_info['name']}")
            
            try:
                # Utiliser le thumbnail haute résolution (plus fiable)
                image_data = self.download_image_via_thumbnail(file_info['id'], size=1024)
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                images.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'data': image_data,
                    'base64': image_b64,
                    'thumbnail': self.get_thumbnail_url(file_info['id']),
                    'mime_type': file_info.get('mime_type', 'image/jpeg')
                })
            except Exception as e:
                print(f"Erreur lors du chargement de {file_info['name']}: {e}")
                # Ajouter quand même avec les métadonnées
                images.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'thumbnail': self.get_thumbnail_url(file_info['id']),
                    'mime_type': file_info.get('mime_type', 'image/jpeg'),
                    'error': str(e)
                })
                continue
        
        if progress_callback:
            progress_callback(1.0, f"{len(images)} images chargées")
        
        return images


class DriveLoaderLite:
    """
    Version utilisant l'API Google Drive avec une clé API
    Plus fiable que le scraping HTML
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_DRIVE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.session = requests.Session()
    
    def extract_folder_id(self, url: str) -> str:
        """Extrait l'ID du dossier depuis une URL Google Drive"""
        patterns = [
            r'folders/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{25,})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Impossible d'extraire l'ID du dossier depuis : {url}")
    
    def list_images_with_api(self, folder_id: str) -> List[Dict]:
        """Liste les images via l'API Google Drive (nécessite une clé API)"""
        if not self.api_key:
            return []
        
        image_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        
        query = f"'{folder_id}' in parents and trashed=false and ("
        query += " or ".join([f"mimeType='{mime}'" for mime in image_mimes])
        query += ")"
        
        url = "https://www.googleapis.com/drive/v3/files"
        params = {
            'q': query,
            'key': self.api_key,
            'fields': 'files(id,name,mimeType,thumbnailLink)',
            'pageSize': 1000
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('files', [])
        except Exception as e:
            print(f"Erreur API Drive: {e}")
            return []
    
    def load_from_url(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """Charge les images d'un dossier public"""
        folder_id = self.extract_folder_id(url)
        
        if progress_callback:
            progress_callback(0, "Récupération de la liste des images...")
        
        files = self.list_images_with_api(folder_id)
        
        if not files:
            raise ValueError(
                "Aucune image trouvée. Vérifiez que :\n"
                "1. Le dossier contient des images\n"
                "2. Le dossier est partagé avec 'Tous ceux qui ont le lien'\n"
                "3. La clé API Google est configurée"
            )
        
        images = []
        total = len(files)
        
        for idx, file_info in enumerate(files):
            if progress_callback:
                progress_callback((idx + 1) / total, f"Chargement : {file_info['name']}")
            
            file_id = file_info['id']
            
            try:
                # Télécharger via thumbnail haute résolution
                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1024"
                response = self.session.get(thumb_url)
                response.raise_for_status()
                image_data = response.content
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                images.append({
                    'id': file_id,
                    'name': file_info['name'],
                    'data': image_data,
                    'base64': image_b64,
                    'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w200",
                    'mime_type': file_info.get('mimeType', 'image/jpeg')
                })
            except Exception as e:
                print(f"Erreur: {file_info['name']}: {e}")
                images.append({
                    'id': file_id,
                    'name': file_info['name'],
                    'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w200",
                    'mime_type': file_info.get('mimeType', 'image/jpeg')
                })
        
        return images


class DriveLoaderManual:
    """
    Loader manuel : l'utilisateur fournit les IDs des images directement
    Solution de repli la plus simple
    """
    
    def __init__(self):
        self.session = requests.Session()
    
    def load_from_ids(
        self, 
        file_ids: List[str],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """Charge des images à partir d'une liste d'IDs Google Drive"""
        images = []
        total = len(file_ids)
        
        for idx, file_id in enumerate(file_ids):
            file_id = file_id.strip()
            if not file_id:
                continue
                
            if progress_callback:
                progress_callback((idx + 1) / total, f"Chargement image {idx + 1}/{total}")
            
            try:
                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1024"
                response = self.session.get(thumb_url)
                response.raise_for_status()
                image_data = response.content
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                images.append({
                    'id': file_id,
                    'name': f"image_{idx + 1}.jpg",
                    'data': image_data,
                    'base64': image_b64,
                    'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w200",
                    'mime_type': 'image/jpeg'
                })
            except Exception as e:
                print(f"Erreur image {file_id}: {e}")
        
        return images
    
    def extract_ids_from_links(self, links_text: str) -> List[str]:
        """Extrait les IDs depuis une liste de liens Google Drive"""
        pattern = r'(?:id=|/d/|/file/d/)([a-zA-Z0-9_-]{25,})'
        ids = re.findall(pattern, links_text)
        return list(set(ids))  # Dédupliquer
    """
    Version allégée du loader pour Streamlit Cloud
    Utilise uniquement les liens publics sans authentification OAuth
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            self.service = build('drive', 'v3', developerKey=self.api_key)
        else:
            self.service = None
    
    def extract_folder_id(self, url: str) -> str:
        """Extrait l'ID du dossier depuis une URL Google Drive"""
        patterns = [
            r'folders/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{25,})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Impossible d'extraire l'ID du dossier depuis : {url}")
    
    def list_images_public(self, folder_id: str) -> List[Dict]:
        """Liste les images d'un dossier public"""
        if not self.service:
            raise ValueError("Clé API Google non configurée")
        
        image_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        
        query = f"'{folder_id}' in parents and trashed=false and ("
        query += " or ".join([f"mimeType='{mime}'" for mime in image_mimes])
        query += ")"
        
        images = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query,
                fields='nextPageToken, files(id, name, mimeType, thumbnailLink)',
                pageToken=page_token,
                pageSize=100
            ).execute()
            
            images.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
        
        return images
    
    def load_from_url(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """Charge les métadonnées des images d'un dossier public"""
        folder_id = self.extract_folder_id(url)
        files = self.list_images_public(folder_id)
        
        images = []
        for idx, file_info in enumerate(files):
            if progress_callback:
                progress_callback((idx + 1) / len(files), f"Indexation : {file_info['name']}")
            
            # Pour les dossiers publics, on utilise les liens directs
            images.append({
                'id': file_info['id'],
                'name': file_info['name'],
                'thumbnail': file_info.get('thumbnailLink'),
                'mime_type': file_info.get('mimeType', 'image/jpeg'),
                'public_url': f"https://drive.google.com/uc?id={file_info['id']}"
            })
        
        return images
