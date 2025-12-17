"""
Module de génération de prompts vidéo pour IA génératives
Compatible avec : Veo 3, Kling 2.6, Runway Gen-4
"""

import os
from typing import Dict, List, Optional
import google.generativeai as genai


class VideoPromptGenerator:
    """Génère des prompts vidéo optimisés pour différentes plateformes"""
    
    # Templates de prompts par plateforme
    PLATFORM_TEMPLATES = {
        'veo3': {
            'name': 'Google Veo 3',
            'max_length': 2000,
            'style': 'descriptif_cinematographique',
            'supports_camera': True,
            'supports_style': True,
            'supports_duration': True,
            'format': """[SCENE]: {scene_description}
[CAMERA]: {camera_movement}
[STYLE]: {visual_style}
[LIGHTING]: {lighting}
[DURATION]: {duration}s
[MOOD]: {mood}"""
        },
        'kling': {
            'name': 'Kling 2.6',
            'max_length': 1500,
            'style': 'concis_precis',
            'supports_camera': True,
            'supports_style': True,
            'supports_duration': True,
            'format': """{scene_description}. {camera_movement}. {visual_style}. {lighting}. {mood}. --duration {duration}"""
        },
        'runway': {
            'name': 'Runway Gen-4',
            'max_length': 1000,
            'style': 'naturel_fluide',
            'supports_camera': True,
            'supports_style': True,
            'supports_duration': False,
            'format': """{scene_description}, {camera_movement}, {visual_style}, {lighting}, {mood}, cinematic quality, 4K"""
        }
    }
    
    # Mapping des mouvements de caméra
    CAMERA_MOVEMENTS = {
        'Fixe': {
            'veo3': 'static shot, locked camera',
            'kling': 'static camera',
            'runway': 'static shot'
        },
        'Panoramique': {
            'veo3': 'slow pan shot, horizontal camera movement',
            'kling': 'pan left to right',
            'runway': 'smooth panning movement'
        },
        'Travelling': {
            'veo3': 'tracking shot, camera dolly movement',
            'kling': 'tracking shot forward',
            'runway': 'smooth tracking shot'
        },
        'Zoom': {
            'veo3': 'slow zoom in, lens zoom',
            'kling': 'zoom in slowly',
            'runway': 'gradual zoom'
        },
        'Steadicam': {
            'veo3': 'steadicam shot, floating camera movement',
            'kling': 'steadicam smooth',
            'runway': 'smooth floating camera'
        },
        'Épaule': {
            'veo3': 'handheld camera, slight shake, documentary style',
            'kling': 'handheld camera movement',
            'runway': 'handheld documentary style'
        },
        'Drone': {
            'veo3': 'aerial drone shot, bird eye view, flying camera',
            'kling': 'drone aerial shot',
            'runway': 'aerial cinematic drone'
        }
    }
    
    # Mapping des valeurs de plan
    SHOT_VALUES = {
        'TGP': 'extreme close-up, macro detail',
        'GP': 'close-up shot, face detail',
        'PE': 'medium close-up, head and shoulders',
        'PM': 'medium shot, waist up',
        'PA': 'american shot, knee up',
        'PG': 'wide shot, full body with environment',
        'TPG': 'extreme wide shot, establishing shot, landscape'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def generate_prompt_for_shot(
        self,
        shot_description: str,
        shot_value: str,
        camera_movement: str,
        image_ref: str,
        mood: str,
        platform: str = 'veo3',
        duration: int = 5,
        style_context: str = ""
    ) -> Dict:
        """
        Génère un prompt vidéo pour un plan spécifique
        
        Args:
            shot_description: Description du plan
            shot_value: Valeur de plan (GP, PM, PG, etc.)
            camera_movement: Mouvement de caméra
            image_ref: Nom de l'image de référence
            mood: Ambiance/atmosphère
            platform: Plateforme cible (veo3, kling, runway)
            duration: Durée en secondes
            style_context: Contexte stylistique global
        
        Returns:
            Dict avec le prompt et les métadonnées
        """
        template = self.PLATFORM_TEMPLATES.get(platform, self.PLATFORM_TEMPLATES['veo3'])
        
        # Récupérer le mouvement de caméra traduit
        camera_translated = self.CAMERA_MOVEMENTS.get(
            camera_movement, 
            {'veo3': camera_movement, 'kling': camera_movement, 'runway': camera_movement}
        ).get(platform, camera_movement)
        
        # Récupérer la valeur de plan
        shot_value_translated = self.SHOT_VALUES.get(shot_value, shot_value)
        
        # Construire le prompt
        prompt_data = {
            'scene_description': f"{shot_value_translated}, {shot_description}",
            'camera_movement': camera_translated,
            'visual_style': style_context or "cinematic, natural lighting, film grain",
            'lighting': "natural ambient lighting",
            'mood': mood,
            'duration': duration
        }
        
        # Formater selon le template de la plateforme
        formatted_prompt = template['format'].format(**prompt_data)
        
        # Tronquer si nécessaire
        if len(formatted_prompt) > template['max_length']:
            formatted_prompt = formatted_prompt[:template['max_length']-3] + "..."
        
        return {
            'platform': platform,
            'platform_name': template['name'],
            'prompt': formatted_prompt,
            'image_ref': image_ref,
            'duration': duration,
            'shot_value': shot_value,
            'camera_movement': camera_movement
        }
    
    def generate_prompts_from_decoupage(
        self,
        decoupage_text: str,
        platform: str = 'veo3',
        style_context: str = "",
        default_duration: int = 5
    ) -> List[Dict]:
        """
        Parse le découpage et génère des prompts pour chaque plan
        
        Args:
            decoupage_text: Texte du découpage technique
            platform: Plateforme cible
            style_context: Style visuel global
            default_duration: Durée par défaut des plans
        
        Returns:
            Liste de prompts générés
        """
        if not self.model:
            raise ValueError("Clé API Gemini requise pour parser le découpage")
        
        prompt = f"""Analyse ce découpage technique et extrais chaque plan sous forme de JSON.

DÉCOUPAGE:
{decoupage_text}

Pour chaque plan, extrais:
- sequence_number: numéro de la séquence
- sequence_title: titre de la séquence
- shot_number: numéro du plan dans la séquence
- shot_value: valeur de plan (TGP, GP, PE, PM, PA, PG, TPG)
- camera_movement: mouvement de caméra (Fixe, Panoramique, Travelling, Zoom, Steadicam, Épaule, Drone)
- description: description du plan
- image_ref: nom du fichier image de référence (si mentionné)
- mood: ambiance/atmosphère
- duration: durée en secondes (ou 5 par défaut)

Réponds UNIQUEMENT avec un JSON valide, format:
[
    {{
        "sequence_number": 1,
        "sequence_title": "...",
        "shot_number": 1,
        "shot_value": "PM",
        "camera_movement": "Fixe",
        "description": "...",
        "image_ref": "...",
        "mood": "...",
        "duration": 5
    }}
]"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Nettoyer le JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            import json
            shots = json.loads(text.strip())
            
            # Générer les prompts pour chaque plan
            prompts = []
            for shot in shots:
                prompt_data = self.generate_prompt_for_shot(
                    shot_description=shot.get('description', ''),
                    shot_value=shot.get('shot_value', 'PM'),
                    camera_movement=shot.get('camera_movement', 'Fixe'),
                    image_ref=shot.get('image_ref', ''),
                    mood=shot.get('mood', ''),
                    platform=platform,
                    duration=shot.get('duration', default_duration),
                    style_context=style_context
                )
                prompt_data['sequence_number'] = shot.get('sequence_number', 0)
                prompt_data['sequence_title'] = shot.get('sequence_title', '')
                prompt_data['shot_number'] = shot.get('shot_number', 0)
                prompts.append(prompt_data)
            
            return prompts
            
        except Exception as e:
            print(f"Erreur lors du parsing: {e}")
            return []
    
    def generate_all_platforms(
        self,
        decoupage_text: str,
        style_context: str = ""
    ) -> Dict[str, List[Dict]]:
        """
        Génère les prompts pour toutes les plateformes
        
        Returns:
            Dict avec les prompts par plateforme
        """
        results = {}
        
        for platform in ['veo3', 'kling', 'runway']:
            results[platform] = self.generate_prompts_from_decoupage(
                decoupage_text=decoupage_text,
                platform=platform,
                style_context=style_context
            )
        
        return results
    
    def format_prompts_for_export(
        self,
        prompts: List[Dict],
        include_metadata: bool = True
    ) -> str:
        """
        Formate les prompts pour l'export
        """
        output = []
        current_sequence = None
        
        for p in prompts:
            # Nouvelle séquence
            if p.get('sequence_number') != current_sequence:
                current_sequence = p.get('sequence_number')
                output.append(f"\n{'='*60}")
                output.append(f"SÉQUENCE {current_sequence} - {p.get('sequence_title', '')}")
                output.append(f"{'='*60}\n")
            
            # Plan
            output.append(f"--- Plan {p.get('shot_number', '?')} ---")
            
            if include_metadata:
                output.append(f"Valeur: {p.get('shot_value', 'N/A')} | Mouvement: {p.get('camera_movement', 'N/A')} | Durée: {p.get('duration', 5)}s")
                if p.get('image_ref'):
                    output.append(f"Image ref: {p.get('image_ref')}")
            
            output.append(f"\nPROMPT ({p.get('platform_name', 'N/A')}):")
            output.append(p.get('prompt', ''))
            output.append("")
        
        return "\n".join(output)


class ImageToVideoPrompt:
    """Génère des prompts vidéo directement depuis une image analysée"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_from_image(
        self,
        image_data: Dict,
        action_hint: str = "",
        platform: str = 'veo3',
        duration: int = 5
    ) -> Dict:
        """
        Génère un prompt vidéo directement depuis une image
        
        Args:
            image_data: Dict avec 'base64' et 'name'
            action_hint: Indication de l'action souhaitée
            platform: Plateforme cible
            duration: Durée souhaitée
        
        Returns:
            Prompt vidéo optimisé
        """
        import base64
        
        prompt = f"""Analyse cette image et génère un prompt pour créer une vidéo de {duration} secondes.

{f"Action souhaitée: {action_hint}" if action_hint else ""}

Le prompt doit décrire:
1. La scène principale (sujet, environnement)
2. Un mouvement suggéré pour le sujet ou la caméra
3. L'atmosphère et l'éclairage
4. Le style visuel

Génère un prompt optimisé pour {platform.upper()}, en anglais, de maximum 500 caractères.
Réponds UNIQUEMENT avec le prompt, sans explication."""

        try:
            image_part = {
                'mime_type': image_data.get('mime_type', 'image/jpeg'),
                'data': base64.b64decode(image_data['base64'])
            }
            
            response = self.model.generate_content([prompt, image_part])
            video_prompt = response.text.strip()
            
            # Adapter au format de la plateforme
            generator = VideoPromptGenerator()
            template = generator.PLATFORM_TEMPLATES.get(platform, {})
            
            if len(video_prompt) > template.get('max_length', 1000):
                video_prompt = video_prompt[:template.get('max_length', 1000)-3] + "..."
            
            return {
                'platform': platform,
                'platform_name': template.get('name', platform),
                'prompt': video_prompt,
                'image_ref': image_data.get('name', ''),
                'duration': duration,
                'source': 'image_analysis'
            }
            
        except Exception as e:
            return {
                'platform': platform,
                'prompt': f"Error generating prompt: {str(e)}",
                'image_ref': image_data.get('name', ''),
                'error': True
            }
