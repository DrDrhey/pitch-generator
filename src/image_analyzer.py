"""
Module d'analyse d'images via Google Gemini
"""

import os
import time
import base64
from typing import List, Dict, Optional, Callable
import google.generativeai as genai
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ImageAnalysis:
    """Structure pour stocker l'analyse d'une image"""
    image_id: str
    image_name: str
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
            'objects': self.objects,
            'narrative_potential': self.narrative_potential,
            'technical_notes': self.technical_notes
        }


@dataclass
class GlobalAnalysis:
    """Structure pour l'analyse globale de toutes les images"""
    individual_analyses: List[ImageAnalysis]
    recurring_subjects: List[Dict]
    recurring_settings: List[str]
    dominant_moods: List[str]
    color_palette: List[str]
    thematic_clusters: List[Dict]
    narrative_threads: List[str]
    visual_style: str
    
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
    """Analyseur d'images utilisant Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API Gemini non trouvée. Définissez GEMINI_API_KEY.")
        
        genai.configure(api_key=self.api_key)
        # Utiliser Gemini 2.5 Flash (modèle le plus récent)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.model_pro = genai.GenerativeModel('gemini-2.5-flash')
        
        # Configuration des limites de rate
        self.requests_per_minute = 60
        self.last_request_time = 0
        self.request_count = 0
    
    def _rate_limit(self):
        """Gère le rate limiting"""
        current_time = time.time()
        
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = time.time()
        
        self.request_count += 1
    
    def _prepare_image(self, image_data: Dict) -> Dict:
        """Prépare une image pour l'API Gemini"""
        if 'base64' in image_data:
            return {
                'mime_type': image_data.get('mime_type', 'image/jpeg'),
                'data': image_data['base64']
            }
        elif 'data' in image_data:
            b64 = base64.b64encode(image_data['data']).decode('utf-8')
            return {
                'mime_type': image_data.get('mime_type', 'image/jpeg'),
                'data': b64
            }
        else:
            raise ValueError(f"Format d'image non supporté pour {image_data.get('name', 'unknown')}")
    
    def analyze_single_image(self, image_data: Dict) -> ImageAnalysis:
        """Analyse une seule image"""
        self._rate_limit()
        
        prompt = """Analyse cette image pour un projet de film/clip musical.

Réponds en JSON avec cette structure exacte :
{
    "description": "Description détaillée de la scène (2-3 phrases)",
    "subjects": ["liste des personnages/sujets présents"],
    "setting": "description du lieu/décor",
    "mood": "atmosphère/ambiance dominante",
    "colors": ["couleurs dominantes"],
    "actions": ["actions/gestes visibles"],
    "objects": ["objets significatifs"],
    "narrative_potential": "potentiel narratif de cette image (1-2 phrases)",
    "technical_notes": "notes techniques : cadrage, lumière, composition"
}

Sois précis et cinématographique dans tes descriptions."""

        try:
            image_part = self._prepare_image(image_data)
            
            response = self.model.generate_content([
                prompt,
                {'mime_type': image_part['mime_type'], 'data': base64.b64decode(image_part['data'])}
            ])
            
            # Parser la réponse JSON
            text = response.text
            
            # Nettoyer le JSON si nécessaire
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            import json
            data = json.loads(text.strip())
            
            return ImageAnalysis(
                image_id=image_data.get('id', ''),
                image_name=image_data.get('name', ''),
                description=data.get('description', ''),
                subjects=data.get('subjects', []),
                setting=data.get('setting', ''),
                mood=data.get('mood', ''),
                colors=data.get('colors', []),
                actions=data.get('actions', []),
                objects=data.get('objects', []),
                narrative_potential=data.get('narrative_potential', ''),
                technical_notes=data.get('technical_notes', '')
            )
            
        except Exception as e:
            print(f"Erreur lors de l'analyse de {image_data.get('name', 'unknown')}: {e}")
            return ImageAnalysis(
                image_id=image_data.get('id', ''),
                image_name=image_data.get('name', ''),
                description=f"Erreur d'analyse: {str(e)}"
            )
    
    def analyze_batch(
        self, 
        images: List[Dict],
        batch_size: int = 10,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> GlobalAnalysis:
        """
        Analyse un lot d'images et produit une analyse globale
        
        Args:
            images: Liste des images à analyser
            batch_size: Nombre d'images par lot pour l'analyse groupée
            progress_callback: Callback pour la progression (0-1, message)
        """
        total_images = len(images)
        individual_analyses = []
        
        # Phase 1: Analyse individuelle de chaque image
        for idx, image in enumerate(images):
            if progress_callback:
                progress = idx / total_images
                progress_callback(progress, f"Analyse de {image.get('name', f'image {idx+1}')}")
            
            analysis = self.analyze_single_image(image)
            individual_analyses.append(analysis)
        
        if progress_callback:
            progress_callback(0.8, "Synthèse des analyses...")
        
        # Phase 2: Analyse globale et synthèse
        global_analysis = self._synthesize_analyses(individual_analyses)
        
        if progress_callback:
            progress_callback(1.0, "Analyse complète")
        
        return global_analysis
    
    def _synthesize_analyses(self, analyses: List[ImageAnalysis]) -> GlobalAnalysis:
        """Synthétise les analyses individuelles en une analyse globale"""
        
        # Collecter toutes les données
        all_subjects = []
        all_settings = []
        all_moods = []
        all_colors = []
        
        for analysis in analyses:
            all_subjects.extend(analysis.subjects)
            all_settings.append(analysis.setting)
            all_moods.append(analysis.mood)
            all_colors.extend(analysis.colors)
        
        # Compter les occurrences
        from collections import Counter
        
        subject_counts = Counter(all_subjects)
        setting_counts = Counter(all_settings)
        mood_counts = Counter(all_moods)
        color_counts = Counter(all_colors)
        
        # Identifier les éléments récurrents
        recurring_subjects = [
            {'name': s, 'count': c} 
            for s, c in subject_counts.most_common(10) 
            if c > 1
        ]
        
        recurring_settings = [s for s, c in setting_counts.most_common(5) if c > 1]
        dominant_moods = [m for m, c in mood_counts.most_common(5)]
        color_palette = [c for c, _ in color_counts.most_common(8)]
        
        # Générer l'analyse thématique avec Gemini
        thematic_analysis = self._generate_thematic_analysis(analyses)
        
        return GlobalAnalysis(
            individual_analyses=analyses,
            recurring_subjects=recurring_subjects,
            recurring_settings=recurring_settings,
            dominant_moods=dominant_moods,
            color_palette=color_palette,
            thematic_clusters=thematic_analysis.get('clusters', []),
            narrative_threads=thematic_analysis.get('threads', []),
            visual_style=thematic_analysis.get('style', '')
        )
    
    def _generate_thematic_analysis(self, analyses: List[ImageAnalysis]) -> Dict:
        """Génère une analyse thématique approfondie"""
        
        # Préparer le résumé des analyses pour le prompt
        summaries = []
        for a in analyses[:50]:  # Limiter pour le contexte
            summaries.append(f"- {a.image_name}: {a.description} | Mood: {a.mood} | Setting: {a.setting}")
        
        summaries_text = "\n".join(summaries)
        
        prompt = f"""En tant qu'analyste cinématographique, analyse cet ensemble d'images pour un projet audiovisuel.

RÉSUMÉ DES IMAGES ANALYSÉES:
{summaries_text}

Réponds en JSON avec cette structure :
{{
    "clusters": [
        {{"theme": "nom du cluster thématique", "images": ["noms des images"], "description": "description du cluster"}}
    ],
    "threads": ["fil narratif potentiel 1", "fil narratif potentiel 2", ...],
    "style": "description du style visuel global (esthétique, influences, références cinématographiques)"
}}

Identifie 3-5 clusters thématiques et 3-5 fils narratifs potentiels."""

        try:
            self._rate_limit()
            response = self.model_pro.generate_content(prompt)
            
            text = response.text
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            import json
            return json.loads(text.strip())
            
        except Exception as e:
            print(f"Erreur lors de l'analyse thématique: {e}")
            return {
                'clusters': [],
                'threads': [],
                'style': 'Analyse non disponible'
            }
    
    def analyze_batch_concurrent(
        self,
        images: List[Dict],
        max_workers: int = 5,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> GlobalAnalysis:
        """
        Analyse les images en parallèle (plus rapide mais attention au rate limiting)
        """
        total = len(images)
        completed = 0
        individual_analyses = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.analyze_single_image, img): img 
                for img in images
            }
            
            for future in as_completed(futures):
                completed += 1
                if progress_callback:
                    progress_callback(
                        completed / total,
                        f"Analysé {completed}/{total} images"
                    )
                
                try:
                    analysis = future.result()
                    individual_analyses.append(analysis)
                except Exception as e:
                    img = futures[future]
                    print(f"Erreur pour {img.get('name', 'unknown')}: {e}")
        
        return self._synthesize_analyses(individual_analyses)
