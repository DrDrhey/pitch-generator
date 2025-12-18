"""
Module d'analyse d'images avec Google Gemini
Optimisé pour analyser de grandes quantités d'images (100+)
Utilise le batching pour minimiser les requêtes API
"""

import os
import time
import base64
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from collections import Counter
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


@dataclass
class ImageAnalysis:
    """Résultat d'analyse d'une image"""
    image_id: str = ""
    image_name: str = ""
    description: str = ""
    subjects: List[str] = field(default_factory=list)
    setting: str = ""
    mood: str = ""
    colors: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    narrative_potential: str = ""
    technical_notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'image_id': self.image_id,
            'image_name': self.image_name,
            'description': self.description,
            'subjects': self.subjects,
            'setting': self.setting,
            'mood': self.mood,
            'colors': self.colors,
            'actions': self.actions,
            'objects': self.objects
        }


@dataclass
class GlobalAnalysis:
    """Analyse globale d'un ensemble d'images"""
    individual_analyses: List[ImageAnalysis] = field(default_factory=list)
    recurring_subjects: List[Dict] = field(default_factory=list)
    recurring_settings: List[str] = field(default_factory=list)
    dominant_moods: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    thematic_clusters: List[Dict] = field(default_factory=list)
    narrative_threads: List[str] = field(default_factory=list)
    visual_style: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'individual_analyses': [a.to_dict() for a in self.individual_analyses],
            'recurring_subjects': self.recurring_subjects,
            'recurring_settings': self.recurring_settings,
            'dominant_moods': self.dominant_moods,
            'color_palette': self.color_palette,
            'thematic_clusters': self.thematic_clusters,
            'narrative_threads': self.narrative_threads,
            'visual_style': self.visual_style
        }


class ImageAnalyzer:
    """
    Analyseur d'images optimisé pour gros volumes
    
    Utilise le batching : plusieurs images analysées par requête
    Modèle : gemini-2.5-flash (dernière version, plus rapide et performante)
    
    Inclut des safety_settings permissifs pour les projets créatifs
    """
    
    # Configuration des filtres de sécurité - PERMISSIF pour projets créatifs
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-2.5-flash'):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API Gemini non trouvée")
        
        genai.configure(api_key=self.api_key)
        
        # Utiliser gemini-2.5-flash (dernière version)
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name,
            safety_settings=self.SAFETY_SETTINGS
        )
        
        # Configuration du batching - optimisé pour compte payant
        self.batch_size = 10  # Images par requête
        self.min_delay = 0.5  # Délai minimal entre requêtes
        self.last_request_time = 0
        self.total_requests = 0
        self.blocked_count = 0
    
    def _wait_for_rate_limit(self):
        """Respecte le rate limit entre les requêtes"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request_with_retry(self, content, max_retries=3):
        """Fait une requête avec retry automatique et gestion des blocages"""
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                response = self.model.generate_content(content)
                self.total_requests += 1
                
                # Vérifier si la réponse contient du texte
                if response.parts:
                    return response.text
                
                # Vérifier le feedback de blocage
                if hasattr(response, 'prompt_feedback'):
                    feedback = response.prompt_feedback
                    if hasattr(feedback, 'block_reason') and feedback.block_reason:
                        print(f"⚠️ Contenu bloqué par Gemini: {feedback.block_reason}")
                        self.blocked_count += 1
                        return None
                
                return None
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Gestion du contenu bloqué
                if 'blocked' in error_str or 'prohibited' in error_str or 'safety' in error_str:
                    print(f"⚠️ Contenu bloqué par les filtres de sécurité Gemini")
                    self.blocked_count += 1
                    return None  # Continuer sans cette image
                
                # Rate limit
                if '429' in str(e) or 'quota' in error_str or 'rate' in error_str:
                    wait_time = 5 + (attempt * 5)
                    print(f"Rate limit - attente {wait_time}s (tentative {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                # Modèle non disponible
                if 'not found' in error_str or 'not supported' in error_str:
                    if self.model_name != 'gemini-2.0-flash':
                        print(f"Modèle {self.model_name} non disponible, utilisation de gemini-2.0-flash")
                        self.model_name = 'gemini-2.0-flash'
                        self.model = genai.GenerativeModel(
                            'gemini-2.0-flash',
                            safety_settings=self.SAFETY_SETTINGS
                        )
                        continue
                    raise
                
                # Autres erreurs
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        return None
    
    def analyze_batch(
        self, 
        images: List[Dict],
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> GlobalAnalysis:
        """
        Point d'entrée principal - Analyse un ensemble d'images
        
        Gère les blocages de sécurité en essayant d'analyser les images
        individuellement si un batch est bloqué.
        """
        total = len(images)
        all_analyses = []
        self.blocked_count = 0
        
        if progress_callback:
            progress_callback(0, f"Démarrage de l'analyse de {total} images...")
        
        num_batches = (total + self.batch_size - 1) // self.batch_size
        
        for batch_idx, batch_start in enumerate(range(0, total, self.batch_size)):
            batch_end = min(batch_start + self.batch_size, total)
            batch = images[batch_start:batch_end]
            
            if progress_callback:
                progress = (batch_idx / num_batches) * 0.8
                progress_callback(progress, f"Lot {batch_idx+1}/{num_batches} ({batch_start+1}-{batch_end}/{total})")
            
            # Essayer d'analyser le lot entier
            batch_analyses = self._analyze_batch(batch, batch_start)
            
            # Si le batch a échoué (toutes les analyses vides), essayer image par image
            if all(not a.description for a in batch_analyses):
                if progress_callback:
                    progress_callback(progress, f"Lot {batch_idx+1} bloqué - analyse individuelle...")
                
                batch_analyses = []
                for i, img in enumerate(batch):
                    single_analysis = self._analyze_single_image(img, batch_start + i)
                    batch_analyses.append(single_analysis)
            
            all_analyses.extend(batch_analyses)
        
        # Rapport sur les blocages
        successful = sum(1 for a in all_analyses if a.description)
        if progress_callback:
            if self.blocked_count > 0:
                progress_callback(0.85, f"Synthèse... ({successful}/{total} images analysées, {self.blocked_count} bloquées)")
            else:
                progress_callback(0.85, f"Synthèse de {successful} images...")
        
        # Générer la synthèse si on a des analyses
        if successful > 0:
            global_analysis = self._generate_global_synthesis(all_analyses)
        else:
            # Synthèse vide si tout est bloqué
            global_analysis = GlobalAnalysis(
                visual_style="Analyse non disponible",
                narrative_threads=["Les images n'ont pas pu être analysées"]
            )
        
        global_analysis.individual_analyses = all_analyses
        
        if progress_callback:
            progress_callback(1.0, f"✓ {successful}/{total} images analysées ({self.total_requests} requêtes)")
        
        return global_analysis
    
    def _analyze_single_image(self, img: Dict, idx: int) -> ImageAnalysis:
        """Analyse une seule image (fallback si le batch est bloqué)"""
        
        prompt = """Analyse cette image pour un projet audiovisuel.

Fournis une analyse JSON:
{
    "description": "description détaillée de la scène",
    "subjects": ["sujets visibles"],
    "setting": "lieu/environnement",
    "mood": "ambiance",
    "colors": ["couleurs principales"],
    "actions": ["actions visibles"],
    "objects": ["objets notables"]
}

Réponds UNIQUEMENT avec le JSON."""

        content_parts = [prompt]
        
        if img.get('base64'):
            try:
                image_part = {
                    'mime_type': img.get('mime_type', 'image/jpeg'),
                    'data': base64.b64decode(img['base64'])
                }
                content_parts.append(image_part)
            except:
                pass
        
        try:
            response_text = self._make_request_with_retry(content_parts)
            
            if response_text:
                json_text = self._extract_json(response_text)
                data = json.loads(json_text)
                
                return ImageAnalysis(
                    image_id=img.get('id', f'img_{idx}'),
                    image_name=img.get('name', f'image_{idx}'),
                    description=data.get('description', ''),
                    subjects=data.get('subjects', []),
                    setting=data.get('setting', ''),
                    mood=data.get('mood', ''),
                    colors=data.get('colors', []),
                    actions=data.get('actions', []),
                    objects=data.get('objects', [])
                )
        except:
            pass
        
        return ImageAnalysis(
            image_id=img.get('id', f'img_{idx}'),
            image_name=img.get('name', f'image_{idx}'),
            description="[Image non analysée - filtre de sécurité]"
        )
    
    def _analyze_batch(self, batch: List[Dict], start_idx: int) -> List[ImageAnalysis]:
        """Analyse un lot d'images en une seule requête"""
        
        # Construire le prompt multi-images
        prompt = f"""Analyse ces {len(batch)} images pour un projet audiovisuel.

Pour CHAQUE image (dans l'ordre), fournis une analyse JSON:
[
  {{
    "index": 0,
    "description": "description détaillée de la scène (2-3 phrases)",
    "subjects": ["sujet principal", "autres sujets"],
    "setting": "lieu/environnement",
    "mood": "ambiance/émotion dominante",
    "colors": ["couleurs principales"],
    "actions": ["actions visibles"],
    "objects": ["objets notables"]
  }},
  ...
]

IMPORTANT: Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
Analyse les {len(batch)} images dans l'ordre où elles apparaissent."""

        # Construire le contenu multimodal
        content_parts = [prompt]
        
        for img in batch:
            if img.get('base64'):
                try:
                    image_part = {
                        'mime_type': img.get('mime_type', 'image/jpeg'),
                        'data': base64.b64decode(img['base64'])
                    }
                    content_parts.append(image_part)
                except Exception as e:
                    print(f"Erreur décodage image: {e}")
        
        # Faire la requête
        try:
            response_text = self._make_request_with_retry(content_parts)
            
            if not response_text:
                return self._create_empty_analyses(batch, start_idx)
            
            # Parser le JSON
            json_text = self._extract_json(response_text)
            analyses_data = json.loads(json_text)
            
            # S'assurer que c'est une liste
            if not isinstance(analyses_data, list):
                analyses_data = [analyses_data]
            
            # Créer les objets ImageAnalysis
            results = []
            for i, img in enumerate(batch):
                analysis_data = analyses_data[i] if i < len(analyses_data) else {}
                
                results.append(ImageAnalysis(
                    image_id=img.get('id', f'img_{start_idx + i}'),
                    image_name=img.get('name', f'image_{start_idx + i}'),
                    description=analysis_data.get('description', ''),
                    subjects=analysis_data.get('subjects', []),
                    setting=analysis_data.get('setting', ''),
                    mood=analysis_data.get('mood', ''),
                    colors=analysis_data.get('colors', []),
                    actions=analysis_data.get('actions', []),
                    objects=analysis_data.get('objects', [])
                ))
            
            return results
            
        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON: {e}")
            return self._create_empty_analyses(batch, start_idx)
        except Exception as e:
            print(f"Erreur analyse batch: {e}")
            return self._create_empty_analyses(batch, start_idx)
    
    def _extract_json(self, text: str) -> str:
        """Extrait le JSON d'une réponse"""
        if '```json' in text:
            return text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            return text.split('```')[1].split('```')[0].strip()
        
        # Chercher le début du JSON
        start = text.find('[')
        if start == -1:
            start = text.find('{')
        
        if start != -1:
            return text[start:].strip()
        
        return text.strip()
    
    def _create_empty_analyses(self, batch: List[Dict], start_idx: int) -> List[ImageAnalysis]:
        """Crée des analyses vides en cas d'erreur"""
        return [
            ImageAnalysis(
                image_id=img.get('id', f'img_{start_idx + i}'),
                image_name=img.get('name', f'image_{start_idx + i}')
            )
            for i, img in enumerate(batch)
        ]
    
    def _generate_global_synthesis(self, analyses: List[ImageAnalysis]) -> GlobalAnalysis:
        """Génère une synthèse globale de toutes les analyses"""
        
        # Agréger les données
        all_subjects = []
        all_settings = []
        all_moods = []
        all_colors = []
        descriptions_sample = []
        
        for a in analyses:
            all_subjects.extend(a.subjects)
            if a.setting:
                all_settings.append(a.setting)
            if a.mood:
                all_moods.append(a.mood)
            all_colors.extend(a.colors)
            if a.description:
                descriptions_sample.append(f"[{a.image_name}] {a.description}")
        
        # Compter les occurrences
        subject_counts = Counter(all_subjects)
        recurring_subjects = [{'name': s, 'count': c} for s, c in subject_counts.most_common(15)]
        
        setting_counts = Counter(all_settings)
        recurring_settings = [s for s, _ in setting_counts.most_common(5)]
        
        mood_counts = Counter(all_moods)
        dominant_moods = [m for m, _ in mood_counts.most_common(5)]
        
        color_counts = Counter(all_colors)
        color_palette = [c for c, _ in color_counts.most_common(10)]
        
        # Demander une synthèse narrative à Gemini
        synthesis_prompt = f"""Analyse ces données pour créer une synthèse narrative:

ÉCHANTILLON D'IMAGES ({len(analyses)} total):
{chr(10).join(descriptions_sample[:25])}

SUJETS RÉCURRENTS: {', '.join([s['name'] for s in recurring_subjects[:10]])}
LIEUX: {', '.join(recurring_settings[:5])}
AMBIANCES: {', '.join(dominant_moods[:5])}
PALETTE: {', '.join(color_palette[:8])}

Génère un JSON:
{{
    "visual_style": "description du style visuel global (1-2 phrases)",
    "narrative_threads": ["potentiel narratif 1", "potentiel 2", "potentiel 3"],
    "thematic_clusters": [
        {{"theme": "thème identifié", "description": "explication courte"}}
    ]
}}

Réponds UNIQUEMENT avec le JSON."""

        try:
            response = self._make_request_with_retry(synthesis_prompt)
            
            if response:
                json_text = self._extract_json(response)
                synthesis = json.loads(json_text)
                
                return GlobalAnalysis(
                    recurring_subjects=recurring_subjects,
                    recurring_settings=recurring_settings,
                    dominant_moods=dominant_moods,
                    color_palette=color_palette,
                    visual_style=synthesis.get('visual_style', ''),
                    narrative_threads=synthesis.get('narrative_threads', []),
                    thematic_clusters=synthesis.get('thematic_clusters', [])
                )
        except Exception as e:
            print(f"Erreur synthèse: {e}")
        
        # Retour par défaut sans synthèse IA
        return GlobalAnalysis(
            recurring_subjects=recurring_subjects,
            recurring_settings=recurring_settings,
            dominant_moods=dominant_moods,
            color_palette=color_palette,
            visual_style="Style varié à déterminer",
            narrative_threads=["Narration à développer"],
            thematic_clusters=[]
        )
