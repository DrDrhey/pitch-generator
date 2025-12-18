"""
Module de génération de prompts vidéo professionnels
Optimisé pour Veo 3 et Kling - Image-to-Video

Basé sur les meilleures pratiques officielles:
- Veo 3: Structure [SCENE]/[CAMERA]/[STYLE]/[AUDIO]
- Kling: Subject + Movement + Camera + Lighting + Atmosphere
"""

import os
import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import google.generativeai as genai

# Import safety settings avec fallback
try:
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
except ImportError:
    # Fallback pour anciennes versions
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]


@dataclass
class ShotPrompt:
    """Prompt pour un plan vidéo"""
    sequence_num: int
    sequence_title: str
    shot_num: int
    shot_value: str  # GP, PM, PG, etc.
    duration: int  # en secondes (max 8)
    reference_image: str  # Nom de l'image à uploader
    description_fr: str  # Description originale en français
    veo3_prompt: str  # Prompt optimisé Veo 3
    kling_prompt: str  # Prompt optimisé Kling
    camera_movement: str
    mood: str
    lighting: str


@dataclass
class ProjectStyleGuide:
    """Guide de style pour cohérence artistique du projet"""
    visual_style: str  # Ex: "cinematic, naturalistic, warm tones"
    color_palette: str  # Ex: "warm earth tones, golden hour lighting"
    camera_style: str  # Ex: "steady, contemplative movements"
    lighting_style: str  # Ex: "natural lighting, soft shadows"
    mood_keywords: str  # Ex: "intimate, nostalgic, serene"
    aspect_ratio: str  # Ex: "16:9 cinematic"
    film_reference: str  # Ex: "Terrence Malick, Emmanuel Lubezki"


class VideoPromptGenerator:
    """
    Générateur de prompts vidéo professionnels
    
    Génère des prompts optimisés pour:
    - Google Veo 3 (Image-to-Video)
    - Kling 2.5+ (Image-to-Video)
    
    Avec cohérence artistique sur l'ensemble du projet.
    """
    
    # Mapping des valeurs de plan en anglais (cinématographique)
    SHOT_VALUES_EN = {
        'TGP': 'extreme close-up, macro detail shot',
        'GP': 'close-up shot, face detail',
        'PE': 'medium close-up, head and shoulders',
        'PM': 'medium shot, waist up',
        'PA': 'american shot, knee up, three-quarter shot',
        'PG': 'full shot, full body with environment',
        'TPG': 'extreme wide shot, establishing shot',
        'PDE': 'over-the-shoulder shot',
        'Insert': 'insert shot, detail shot',
        'POV': 'point of view shot, subjective camera'
    }
    
    # Mapping des mouvements de caméra
    CAMERA_MOVEMENTS_EN = {
        'Fixe': 'static shot, locked camera, no movement',
        'Panoramique': 'slow pan shot, horizontal camera movement',
        'Panoramique gauche': 'slow pan left, horizontal movement left to right',
        'Panoramique droite': 'slow pan right, horizontal movement right to left',
        'Travelling avant': 'slow push-in, dolly forward, camera moves toward subject',
        'Travelling arrière': 'slow pull-back, dolly out, camera retreats from subject',
        'Travelling latéral': 'lateral tracking shot, camera moves sideways',
        'Zoom': 'slow zoom in, lens zoom, no camera movement',
        'Zoom arrière': 'slow zoom out, lens pulls back',
        'Steadicam': 'steadicam shot, floating smooth movement',
        'Épaule': 'handheld camera, subtle shake, documentary style',
        'Drone': 'aerial drone shot, bird eye view, flying camera',
        'Grue': 'crane shot, vertical camera movement',
        'Plongée': 'high angle shot, camera looking down',
        'Contre-plongée': 'low angle shot, camera looking up',
        'Arc': 'arc shot, camera orbits around subject',
        'Suivi': 'tracking shot, camera follows subject movement'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash',
                safety_settings=SAFETY_SETTINGS
            )
        else:
            self.model = None
        
        self.style_guide: Optional[ProjectStyleGuide] = None
    
    def generate_style_guide(self, analysis_summary: str, tone: str = "Naturaliste") -> ProjectStyleGuide:
        """
        Génère un guide de style cohérent pour tout le projet
        basé sur l'analyse des images et le ton choisi.
        """
        
        tone_styles = {
            'Naturaliste / Brut': {
                'visual': 'naturalistic, raw, authentic, documentary-style',
                'camera': 'handheld subtle movements, observational',
                'lighting': 'natural available light, realistic shadows',
                'mood': 'intimate, authentic, unfiltered'
            },
            'Poétique / Contemplatif': {
                'visual': 'ethereal, dreamlike, soft focus moments',
                'camera': 'slow graceful movements, contemplative pacing',
                'lighting': 'golden hour, diffused light, soft shadows',
                'mood': 'serene, meditative, nostalgic'
            },
            'Documentaire / Observationnel': {
                'visual': 'realistic, journalistic, candid moments',
                'camera': 'steady observational, occasional handheld',
                'lighting': 'natural lighting, no artificial enhancement',
                'mood': 'authentic, informative, respectful'
            },
            'Cinématique / Dramatique': {
                'visual': 'cinematic, high contrast, dramatic composition',
                'camera': 'precise controlled movements, dramatic angles',
                'lighting': 'chiaroscuro, dramatic shadows, rim lighting',
                'mood': 'intense, powerful, emotionally charged'
            },
            'Onirique / Surréaliste': {
                'visual': 'surreal, dreamlike, fluid reality',
                'camera': 'floating movements, unexpected angles',
                'lighting': 'stylized, colored gels, unnatural sources',
                'mood': 'mysterious, otherworldly, hypnotic'
            }
        }
        
        style = tone_styles.get(tone, tone_styles['Naturaliste / Brut'])
        
        prompt = f"""Based on this visual analysis, create a cohesive style guide for AI video generation.

VISUAL ANALYSIS:
{analysis_summary}

DESIRED TONE: {tone}
BASE STYLE: {style['visual']}

Generate a JSON style guide:
{{
    "visual_style": "specific visual style keywords for consistency",
    "color_palette": "color grading and palette description",
    "camera_style": "camera movement philosophy",
    "lighting_style": "lighting approach",
    "mood_keywords": "emotional keywords",
    "aspect_ratio": "16:9 or 2.39:1 etc",
    "film_reference": "cinematographer or director reference if applicable"
}}

Be specific and cinematic. This will ensure visual consistency across all generated shots."""

        try:
            if self.model:
                response = self.model.generate_content(prompt)
                json_text = response.text
                
                # Extraire JSON
                if '```json' in json_text:
                    json_text = json_text.split('```json')[1].split('```')[0]
                elif '```' in json_text:
                    json_text = json_text.split('```')[1].split('```')[0]
                
                data = json.loads(json_text.strip())
                
                self.style_guide = ProjectStyleGuide(
                    visual_style=data.get('visual_style', style['visual']),
                    color_palette=data.get('color_palette', 'natural tones'),
                    camera_style=data.get('camera_style', style['camera']),
                    lighting_style=data.get('lighting_style', style['lighting']),
                    mood_keywords=data.get('mood_keywords', style['mood']),
                    aspect_ratio=data.get('aspect_ratio', '16:9'),
                    film_reference=data.get('film_reference', '')
                )
                return self.style_guide
        except Exception as e:
            print(f"Error generating style guide: {e}")
        
        # Fallback
        self.style_guide = ProjectStyleGuide(
            visual_style=style['visual'],
            color_palette='natural tones, balanced exposure',
            camera_style=style['camera'],
            lighting_style=style['lighting'],
            mood_keywords=style['mood'],
            aspect_ratio='16:9',
            film_reference=''
        )
        return self.style_guide
    
    def _get_shot_value_en(self, shot_value: str) -> str:
        """Convertit la valeur de plan en anglais"""
        # Nettoyer
        clean = shot_value.strip().upper()
        return self.SHOT_VALUES_EN.get(clean, f'{shot_value} shot')
    
    def _get_camera_movement_en(self, movement: str) -> str:
        """Convertit le mouvement de caméra en anglais"""
        for fr, en in self.CAMERA_MOVEMENTS_EN.items():
            if fr.lower() in movement.lower():
                return en
        return 'subtle camera movement'
    
    def _generate_veo3_prompt(
        self,
        description: str,
        shot_value: str,
        camera_movement: str,
        duration: int,
        mood: str,
        lighting: str
    ) -> str:
        """
        Génère un prompt optimisé pour Veo 3 Image-to-Video
        
        Structure Veo 3:
        - Focus sur l'ACTION à appliquer à l'image
        - Mouvement de caméra explicite
        - Style et ambiance
        - Audio optionnel
        """
        
        shot_en = self._get_shot_value_en(shot_value)
        camera_en = self._get_camera_movement_en(camera_movement)
        
        # Style guide integration
        style_context = ""
        if self.style_guide:
            style_context = f"{self.style_guide.visual_style}, {self.style_guide.color_palette}"
        else:
            style_context = "cinematic, natural lighting"
        
        # Build structured Veo 3 prompt
        prompt_parts = []
        
        # Scene/Action (what happens)
        prompt_parts.append(f"{shot_en}, {description}")
        
        # Camera movement
        prompt_parts.append(f"Camera: {camera_en}")
        
        # Style
        prompt_parts.append(f"Style: {style_context}")
        
        # Lighting
        if lighting:
            prompt_parts.append(f"Lighting: {lighting}")
        elif self.style_guide:
            prompt_parts.append(f"Lighting: {self.style_guide.lighting_style}")
        
        # Mood
        if mood:
            prompt_parts.append(f"Mood: {mood}")
        elif self.style_guide:
            prompt_parts.append(f"Mood: {self.style_guide.mood_keywords}")
        
        # Duration
        prompt_parts.append(f"Duration: {min(duration, 8)} seconds")
        
        # Audio (ambient)
        prompt_parts.append("Audio: subtle ambient sounds matching the scene")
        
        return ". ".join(prompt_parts) + "."
    
    def _generate_kling_prompt(
        self,
        description: str,
        shot_value: str,
        camera_movement: str,
        duration: int,
        mood: str,
        lighting: str
    ) -> str:
        """
        Génère un prompt optimisé pour Kling Image-to-Video
        
        Structure Kling (I2V):
        - Subject movement (pas de description de scène, l'image la fournit)
        - Camera movement explicite
        - Lighting et atmosphere
        """
        
        shot_en = self._get_shot_value_en(shot_value)
        camera_en = self._get_camera_movement_en(camera_movement)
        
        # Style guide integration
        if self.style_guide:
            atmosphere = f"{self.style_guide.mood_keywords}, {self.style_guide.visual_style}"
            light = self.style_guide.lighting_style
        else:
            atmosphere = mood if mood else "natural atmosphere"
            light = lighting if lighting else "natural lighting"
        
        # Kling I2V format: Focus on MOVEMENT, not scene description
        prompt = f"{description}. {camera_en}. {light}. {atmosphere}."
        
        return prompt
    
    def parse_decoupage_and_generate_prompts(
        self,
        decoupage: str,
        images: List[Dict],
        analysis_summary: str = "",
        tone: str = "Naturaliste"
    ) -> List[ShotPrompt]:
        """
        Parse le découpage technique et génère les prompts pour chaque plan.
        
        Utilise Gemini pour extraire les informations structurées du découpage.
        """
        
        # Générer le style guide d'abord
        if not self.style_guide and analysis_summary:
            self.generate_style_guide(analysis_summary, tone)
        
        # Créer un mapping nom d'image -> image
        image_map = {img.get('name', ''): img for img in images}
        image_names = list(image_map.keys())
        
        # Prompt pour parser le découpage
        parse_prompt = f"""Analyze this French technical breakdown (découpage) and extract each shot.

DÉCOUPAGE:
{decoupage}

AVAILABLE REFERENCE IMAGES:
{', '.join(image_names[:50])}

For EACH shot mentioned, extract and return a JSON array:
[
  {{
    "sequence_num": 1,
    "sequence_title": "Title of sequence",
    "shot_num": 1,
    "shot_value": "PM",
    "camera_movement": "Travelling avant",
    "duration": 5,
    "description_fr": "Original French description",
    "description_en": "English translation of the action/scene",
    "mood": "emotional tone",
    "lighting": "lighting description",
    "reference_image": "best matching image name from the list"
  }}
]

Rules:
- shot_value: TGP, GP, PE, PM, PA, PG, TPG (standard French values)
- duration: 3-8 seconds max
- Match each shot to the most relevant reference image
- description_en: Focus on the ACTION, what moves, what happens
- Be specific about camera movements

Return ONLY valid JSON array."""

        shots = []
        
        try:
            if self.model:
                response = self.model.generate_content(parse_prompt)
                json_text = response.text
                
                # Extract JSON
                if '```json' in json_text:
                    json_text = json_text.split('```json')[1].split('```')[0]
                elif '```' in json_text:
                    json_text = json_text.split('```')[1].split('```')[0]
                
                # Find JSON array
                start = json_text.find('[')
                end = json_text.rfind(']') + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
                
                shots_data = json.loads(json_text)
                
                for shot_data in shots_data:
                    # Generate prompts
                    veo3_prompt = self._generate_veo3_prompt(
                        description=shot_data.get('description_en', ''),
                        shot_value=shot_data.get('shot_value', 'PM'),
                        camera_movement=shot_data.get('camera_movement', 'Fixe'),
                        duration=shot_data.get('duration', 5),
                        mood=shot_data.get('mood', ''),
                        lighting=shot_data.get('lighting', '')
                    )
                    
                    kling_prompt = self._generate_kling_prompt(
                        description=shot_data.get('description_en', ''),
                        shot_value=shot_data.get('shot_value', 'PM'),
                        camera_movement=shot_data.get('camera_movement', 'Fixe'),
                        duration=shot_data.get('duration', 5),
                        mood=shot_data.get('mood', ''),
                        lighting=shot_data.get('lighting', '')
                    )
                    
                    shots.append(ShotPrompt(
                        sequence_num=shot_data.get('sequence_num', 1),
                        sequence_title=shot_data.get('sequence_title', ''),
                        shot_num=shot_data.get('shot_num', 1),
                        shot_value=shot_data.get('shot_value', 'PM'),
                        duration=min(shot_data.get('duration', 5), 8),
                        reference_image=shot_data.get('reference_image', ''),
                        description_fr=shot_data.get('description_fr', ''),
                        veo3_prompt=veo3_prompt,
                        kling_prompt=kling_prompt,
                        camera_movement=shot_data.get('camera_movement', 'Fixe'),
                        mood=shot_data.get('mood', ''),
                        lighting=shot_data.get('lighting', '')
                    ))
        
        except Exception as e:
            print(f"Error parsing découpage: {e}")
        
        return shots
    
    def format_for_export(self, shots: List[ShotPrompt]) -> str:
        """
        Formate les prompts pour export - facile à copier-coller
        """
        
        output = []
        
        # Header with style guide
        output.append("=" * 80)
        output.append("VIDEO PROMPTS - READY FOR GENERATION")
        output.append("=" * 80)
        output.append("")
        
        if self.style_guide:
            output.append("GLOBAL STYLE GUIDE (Apply to ALL shots for consistency)")
            output.append("-" * 50)
            output.append(f"Visual Style: {self.style_guide.visual_style}")
            output.append(f"Color Palette: {self.style_guide.color_palette}")
            output.append(f"Camera Style: {self.style_guide.camera_style}")
            output.append(f"Lighting: {self.style_guide.lighting_style}")
            output.append(f"Mood: {self.style_guide.mood_keywords}")
            if self.style_guide.film_reference:
                output.append(f"Reference: {self.style_guide.film_reference}")
            output.append("")
            output.append("=" * 80)
            output.append("")
        
        current_sequence = None
        
        for shot in shots:
            # New sequence header
            if shot.sequence_num != current_sequence:
                current_sequence = shot.sequence_num
                output.append("")
                output.append(f"{'='*80}")
                output.append(f"SEQUENCE {shot.sequence_num}: {shot.sequence_title.upper()}")
                output.append(f"{'='*80}")
                output.append("")
            
            # Shot info
            output.append(f"{'─'*60}")
            output.append(f"SHOT {shot.sequence_num}.{shot.shot_num}")
            output.append(f"{'─'*60}")
            output.append("")
            
            # Reference image (IMPORTANT - highlight this)
            output.append(f"📷 REFERENCE IMAGE TO UPLOAD:")
            output.append(f"   {shot.reference_image}")
            output.append("")
            
            # Technical info
            output.append(f"📋 Shot Info:")
            output.append(f"   • Value: {shot.shot_value}")
            output.append(f"   • Camera: {shot.camera_movement}")
            output.append(f"   • Duration: {shot.duration}s")
            output.append(f"   • Mood: {shot.mood}")
            output.append("")
            
            # Original description
            output.append(f"📝 Description (FR):")
            output.append(f"   {shot.description_fr}")
            output.append("")
            
            # VEO 3 PROMPT
            output.append(f"🎬 VEO 3 PROMPT (copy-paste ready):")
            output.append(f"┌{'─'*58}┐")
            # Word wrap the prompt
            wrapped = self._word_wrap(shot.veo3_prompt, 56)
            for line in wrapped:
                output.append(f"│ {line.ljust(56)} │")
            output.append(f"└{'─'*58}┘")
            output.append("")
            
            # KLING PROMPT
            output.append(f"🎥 KLING PROMPT (copy-paste ready):")
            output.append(f"┌{'─'*58}┐")
            wrapped = self._word_wrap(shot.kling_prompt, 56)
            for line in wrapped:
                output.append(f"│ {line.ljust(56)} │")
            output.append(f"└{'─'*58}┘")
            output.append("")
        
        # Footer
        output.append("")
        output.append("=" * 80)
        output.append("END OF PROMPTS")
        output.append(f"Total: {len(shots)} shots")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def format_for_markdown(self, shots: List[ShotPrompt]) -> str:
        """
        Formate les prompts en Markdown pour meilleure lisibilité
        """
        
        output = []
        
        output.append("# 🎬 Video Generation Prompts")
        output.append("")
        output.append("*Prompts optimisés pour Image-to-Video (Veo 3 & Kling)*")
        output.append("")
        
        # Style Guide
        if self.style_guide:
            output.append("## 🎨 Global Style Guide")
            output.append("")
            output.append("*Appliquer ce style à TOUS les plans pour cohérence artistique*")
            output.append("")
            output.append(f"| Element | Value |")
            output.append(f"|---------|-------|")
            output.append(f"| **Visual Style** | {self.style_guide.visual_style} |")
            output.append(f"| **Color Palette** | {self.style_guide.color_palette} |")
            output.append(f"| **Camera Style** | {self.style_guide.camera_style} |")
            output.append(f"| **Lighting** | {self.style_guide.lighting_style} |")
            output.append(f"| **Mood** | {self.style_guide.mood_keywords} |")
            if self.style_guide.film_reference:
                output.append(f"| **Reference** | {self.style_guide.film_reference} |")
            output.append("")
            output.append("---")
            output.append("")
        
        current_sequence = None
        
        for shot in shots:
            # New sequence
            if shot.sequence_num != current_sequence:
                current_sequence = shot.sequence_num
                output.append(f"## Séquence {shot.sequence_num}: {shot.sequence_title}")
                output.append("")
            
            # Shot
            output.append(f"### Shot {shot.sequence_num}.{shot.shot_num}")
            output.append("")
            
            # Reference image
            output.append(f"**📷 Image de référence à uploader:** `{shot.reference_image}`")
            output.append("")
            
            # Info table
            output.append(f"| Paramètre | Valeur |")
            output.append(f"|-----------|--------|")
            output.append(f"| Valeur | {shot.shot_value} |")
            output.append(f"| Caméra | {shot.camera_movement} |")
            output.append(f"| Durée | {shot.duration}s |")
            output.append(f"| Ambiance | {shot.mood} |")
            output.append("")
            
            # Description
            output.append(f"**Description:** {shot.description_fr}")
            output.append("")
            
            # Veo 3
            output.append(f"**🎬 Prompt Veo 3:**")
            output.append("```")
            output.append(shot.veo3_prompt)
            output.append("```")
            output.append("")
            
            # Kling
            output.append(f"**🎥 Prompt Kling:**")
            output.append("```")
            output.append(shot.kling_prompt)
            output.append("```")
            output.append("")
            output.append("---")
            output.append("")
        
        return "\n".join(output)
    
    def _word_wrap(self, text: str, width: int) -> List[str]:
        """Word wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else ['']


def generate_video_prompts_from_decoupage(
    decoupage: str,
    images: List[Dict],
    analysis_summary: str,
    tone: str,
    api_key: str
) -> Dict:
    """
    Fonction utilitaire pour générer les prompts vidéo
    
    Returns:
        Dict avec 'shots', 'export_txt', 'export_md', 'style_guide'
    """
    
    generator = VideoPromptGenerator(api_key)
    
    # Generate style guide
    style_guide = generator.generate_style_guide(analysis_summary, tone)
    
    # Parse and generate prompts
    shots = generator.parse_decoupage_and_generate_prompts(
        decoupage=decoupage,
        images=images,
        analysis_summary=analysis_summary,
        tone=tone
    )
    
    # Format exports
    export_txt = generator.format_for_export(shots)
    export_md = generator.format_for_markdown(shots)
    
    return {
        'shots': shots,
        'export_txt': export_txt,
        'export_md': export_md,
        'style_guide': style_guide
    }
