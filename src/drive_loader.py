"""
Module de chargement des images depuis Google Drive
Version utilisant l'API Google Drive
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
    Charge les images depuis Google Drive en utilisant l'API officielle
    Nécessite une clé API Google (GOOGLE_API_KEY)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_DRIVE_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_folder_id(self, url: str) -> str:
        """Extrait l'ID du dossier depuis une URL Google Drive"""
        patterns = [
            r'folders/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{20,})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Impossible d'extraire l'ID du dossier depuis l'URL fournie")
    
    def list_images(self, folder_id: str) -> List[Dict]:
        """Liste les images d'un dossier via l'API Google Drive"""
        
        if not self.api_key:
            raise ValueError(
                "Clé API Google non configurée.\n\n"
                "Ajoutez GOOGLE_API_KEY dans les secrets Streamlit :\n"
                "1. Settings → Secrets\n"
                "2. Ajoutez : GOOGLE_API_KEY = \"votre_clé\"\n\n"
                "Ou utilisez le mode 'Upload direct' qui ne nécessite pas de clé."
            )
        
        # Types MIME des images
        image_mimes = [
            'image/jpeg',
            'image/png', 
            'image/gif',
            'image/webp',
            'image/bmp'
        ]
        
        # Construire la requête
        query = f"'{folder_id}' in parents and trashed=false"
        mime_filter = " or ".join([f"mimeType='{m}'" for m in image_mimes])
        query += f" and ({mime_filter})"
        
        url = "https://www.googleapis.com/drive/v3/files"
        
        all_files = []
        page_token = None
        
        while True:
            params = {
                'q': query,
                'key': self.api_key,
                'fields': 'nextPageToken, files(id, name, mimeType, thumbnailLink)',
                'pageSize': 100,
                'orderBy': 'name'
            }
            
            if page_token:
                params['pageToken'] = page_token
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 403:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Accès refusé')
                raise ValueError(
                    f"Erreur d'accès à l'API Google Drive : {error_msg}\n\n"
                    "Vérifiez que :\n"
                    "1. L'API Google Drive est activée dans Google Cloud Console\n"
                    "2. La clé API est correcte\n"
                    "3. Le dossier est partagé publiquement"
                )
            
            if response.status_code == 404:
                raise ValueError(
                    "Dossier non trouvé.\n\n"
                    "Vérifiez que :\n"
                    "1. Le lien du dossier est correct\n"
                    "2. Le dossier est partagé avec 'Tous ceux qui ont le lien'"
                )
            
            if response.status_code != 200:
                raise ValueError(f"Erreur API Google Drive : {response.status_code}")
            
            data = response.json()
            files = data.get('files', [])
            all_files.extend(files)
            
            page_token = data.get('nextPageToken')
            if not page_token:
                break
        
        return all_files
    
    def download_image(self, file_id: str, size: int = 1024) -> bytes:
        """Télécharge une image via le thumbnail haute résolution"""
        
        # Utiliser le service de thumbnail de Google Drive
        thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"
        
        try:
            response = self.session.get(thumb_url, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 100:
                return response.content
            
            # Fallback : téléchargement direct
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = self.session.get(direct_url, timeout=30)
            
            if response.status_code == 200:
                # Redimensionner si nécessaire
                img = Image.open(io.BytesIO(response.content))
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(buffer, format='JPEG', quality=85)
                return buffer.getvalue()
            
            raise Exception(f"Impossible de télécharger l'image")
            
        except Exception as e:
            raise Exception(f"Erreur téléchargement : {str(e)}")
    
    def load_from_url(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """
        Charge toutes les images d'un dossier Drive
        """
        # Extraire l'ID du dossier
        folder_id = self.extract_folder_id(url)
        
        if progress_callback:
            progress_callback(0.05, "Connexion à Google Drive...")
        
        # Lister les fichiers
        files = self.list_images(folder_id)
        total = len(files)
        
        if total == 0:
            raise ValueError(
                "Aucune image trouvée dans ce dossier.\n\n"
                "Vérifiez que :\n"
                "1. Le dossier contient des images (jpg, png, gif, webp)\n"
                "2. Le dossier est partagé avec 'Tous ceux qui ont le lien'\n"
                "3. Le lien est correct"
            )
        
        if progress_callback:
            progress_callback(0.1, f"{total} images trouvées, téléchargement...")
        
        images = []
        errors = 0
        
        for idx, file_info in enumerate(files):
            if progress_callback:
                progress = 0.1 + (0.9 * (idx + 1) / total)
                progress_callback(progress, f"Image {idx + 1}/{total} : {file_info['name'][:30]}")
            
            try:
                image_data = self.download_image(file_info['id'])
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                images.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'data': image_data,
                    'base64': image_b64,
                    'thumbnail': f"https://drive.google.com/thumbnail?id={file_info['id']}&sz=w200",
                    'mime_type': file_info.get('mimeType', 'image/jpeg')
                })
                
            except Exception as e:
                errors += 1
                print(f"Erreur pour {file_info['name']}: {e}")
                # Continuer avec les autres images
                continue
        
        if len(images) == 0:
            raise ValueError(
                f"Impossible de télécharger les images ({errors} erreurs).\n"
                "Les fichiers sont peut-être trop volumineux ou le partage incorrect."
            )
        
        if progress_callback:
            progress_callback(1.0, f"{len(images)} images chargées ({errors} erreurs)")
        
        return images


# Alias pour compatibilité
DriveLoaderLite = DriveLoader


class DriveLoaderManual:
    """
    Loader pour charger des images depuis des liens individuels
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_file_id(self, url: str) -> Optional[str]:
        """Extrait l'ID d'un fichier depuis un lien Google Drive"""
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
            r'/d/([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{20,})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_ids_from_links(self, links_text: str) -> List[str]:
        """Extrait les IDs depuis une liste de liens"""
        ids = []
        
        for line in links_text.strip().split('\n'):
            line = line.strip()
            if line:
                file_id = self.extract_file_id(line)
                if file_id:
                    ids.append(file_id)
        
        return list(set(ids))  # Dédupliquer
    
    def load_from_ids(
        self, 
        file_ids: List[str],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict]:
        """Charge des images à partir d'une liste d'IDs"""
        
        images = []
        total = len(file_ids)
        
        for idx, file_id in enumerate(file_ids):
            if progress_callback:
                progress_callback((idx + 1) / total, f"Image {idx + 1}/{total}")
            
            try:
                # Télécharger via thumbnail
                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1024"
                response = self.session.get(thumb_url, timeout=30)
                
                if response.status_code == 200 and len(response.content) > 100:
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
                continue
        
        return images
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
