"""
Module de construction narrative et génération de pitchs
"""

import os
from typing import Dict, List, Optional
import google.generativeai as genai


class NarrativeBuilder:
    """Génère les éléments narratifs à partir des analyses d'images"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API Gemini non trouvée")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def generate_all(self, analysis: 'GlobalAnalysis', context: Dict) -> Dict:
        """
        Génère tous les éléments narratifs
        
        Args:
            analysis: Analyse globale des images
            context: Contexte créatif (brief, format, durée, ton)
        
        Returns:
            Dict avec pitch, sequencer, decoupage
        """
        pitch = self.generate_pitch(analysis, context)
        sequencer = self.generate_sequencer(analysis, context, pitch)
        decoupage = self.generate_decoupage(analysis, context, sequencer)
        
        return {
            'pitch': pitch,
            'sequencer': sequencer,
            'decoupage': decoupage
        }
    
    def _format_analysis_summary(self, analysis: 'GlobalAnalysis') -> str:
        """Formate l'analyse pour les prompts"""
        lines = []
        
        # Sujets récurrents
        if analysis.recurring_subjects:
            subjects = ", ".join([f"{s['name']} (x{s['count']})" for s in analysis.recurring_subjects[:10]])
            lines.append(f"SUJETS RÉCURRENTS: {subjects}")
        
        # Lieux
        if analysis.recurring_settings:
            lines.append(f"LIEUX: {', '.join(analysis.recurring_settings[:5])}")
        
        # Ambiances
        if analysis.dominant_moods:
            lines.append(f"AMBIANCES: {', '.join(analysis.dominant_moods[:5])}")
        
        # Palette
        if analysis.color_palette:
            lines.append(f"PALETTE: {', '.join(analysis.color_palette[:8])}")
        
        # Style visuel
        if analysis.visual_style:
            lines.append(f"STYLE VISUEL: {analysis.visual_style}")
        
        # Fils narratifs
        if analysis.narrative_threads:
            lines.append(f"FILS NARRATIFS POTENTIELS: {', '.join(analysis.narrative_threads)}")
        
        # Clusters thématiques
        if analysis.thematic_clusters:
            clusters_text = []
            for c in analysis.thematic_clusters[:5]:
                clusters_text.append(f"- {c.get('theme', 'N/A')}: {c.get('description', '')}")
            lines.append(f"CLUSTERS THÉMATIQUES:\n" + "\n".join(clusters_text))
        
        # Échantillon d'images
        lines.append("\nÉCHANTILLON D'IMAGES ANALYSÉES:")
        for img in analysis.individual_analyses[:20]:
            lines.append(f"• [{img.image_name}] {img.description[:100]}...")
        
        return "\n".join(lines)
    
    def generate_pitch(self, analysis: 'GlobalAnalysis', context: Dict) -> str:
        """Génère le pitch narratif"""
        
        analysis_summary = self._format_analysis_summary(analysis)
        
        prompt = f"""Tu es un scénariste et réalisateur de renom, spécialisé dans l'écriture de projets audiovisuels originaux avec une forte identité visuelle.

BRIEF CRÉATIF:
{context.get('brief', 'Non spécifié')}

FORMAT: {context.get('format', 'Non spécifié')}
DURÉE CIBLE: {context.get('duration', 'Non spécifié')}
TONALITÉ: {context.get('tone', 'Non spécifié')}

ANALYSE DES IMAGES DE RÉFÉRENCE:
{analysis_summary}

---

À partir de ces éléments visuels et du brief, rédige un PITCH NARRATIF complet.

Le pitch doit inclure :

1. **TITRE** (provisoire, évocateur)

2. **LOGLINE** (1-2 phrases qui résument le concept)

3. **SYNOPSIS** (300-500 mots)
   - Présentation de l'univers
   - Présentation des personnages principaux (basés sur les sujets récurrents des images)
   - Arc narratif général
   - Tonalité et atmosphère

4. **NOTE D'INTENTION** (200-300 mots)
   - Ta vision artistique
   - Les thèmes explorés
   - L'approche visuelle et narrative
   - Les références/inspirations

5. **PERSONNAGES PRINCIPAUX**
   - Descriptions basées sur les figures identifiées dans les images

Écris de manière cinématographique, évocatrice. Intègre naturellement les éléments visuels identifiés dans les images.
Le ton doit correspondre à la tonalité demandée : {context.get('tone', 'naturaliste')}."""

        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_sequencer(
        self, 
        analysis: 'GlobalAnalysis', 
        context: Dict,
        pitch: str
    ) -> str:
        """Génère le séquencier"""
        
        # Lister toutes les images pour attribution
        image_list = "\n".join([
            f"- {img.image_name}: {img.description[:80]}..." 
            for img in analysis.individual_analyses
        ])
        
        prompt = f"""Tu es un scénariste professionnel. Voici le pitch d'un projet audiovisuel :

---
{pitch}
---

LISTE DES IMAGES DISPONIBLES:
{image_list}

FORMAT: {context.get('format', 'Non spécifié')}
DURÉE CIBLE: {context.get('duration', 'Non spécifié')}

---

Crée un SÉQUENCIER DÉTAILLÉ qui structure le projet en séquences.

Pour chaque séquence, indique :

**SÉQUENCE [N] - [TITRE DE LA SÉQUENCE]**
- **Durée estimée** : XX secondes / XX minutes
- **Lieu** : [description du lieu]
- **Personnages** : [personnages présents]
- **Action** : [description de l'action en 2-3 phrases]
- **Intention** : [ce que cette séquence apporte au récit]
- **Images de référence** : [LISTE DES NOMS DE FICHIERS des images qui correspondent à cette séquence]
- **Ambiance** : [atmosphère, lumière, son]

---

Le séquencier doit :
1. Couvrir l'intégralité du récit décrit dans le pitch
2. Attribuer TOUTES les images disponibles aux séquences appropriées
3. Créer une progression narrative cohérente
4. Respecter la durée cible
5. Alterner les rythmes et les ambiances

Génère entre 8 et 15 séquences selon la durée du projet."""

        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_decoupage(
        self, 
        analysis: 'GlobalAnalysis', 
        context: Dict,
        sequencer: str
    ) -> str:
        """Génère le découpage technique"""
        
        prompt = f"""Tu es un réalisateur expérimenté. Voici le séquencier d'un projet audiovisuel :

---
{sequencer}
---

FORMAT: {context.get('format', 'Non spécifié')}
TONALITÉ: {context.get('tone', 'Non spécifié')}

---

Crée un DÉCOUPAGE TECHNIQUE détaillé pour chaque séquence.

Pour chaque plan :

**Séquence [N] - [Titre]**

| # | Valeur | Mouvement | Description | Image ref | Son | Durée |
|---|--------|-----------|-------------|-----------|-----|-------|
| 1 | [TPE/PE/PM/PA/PG/TGP] | [Fixe/Pano/Travelling/etc.] | [Description du plan] | [Nom fichier image] | [Son diégétique/musique] | [Xs] |

---

LÉGENDE DES VALEURS DE PLAN:
- TGP : Très Gros Plan
- GP : Gros Plan  
- PE : Plan Épaule
- PM : Plan Moyen
- PA : Plan Américain
- PG : Plan General
- TPG : Très Plan Général

MOUVEMENTS:
- Fixe
- Panoramique (gauche/droite/haut/bas)
- Travelling (avant/arrière/latéral)
- Zoom (in/out)
- Steadicam
- Épaule
- Drone

---

Le découpage doit :
1. Détailler chaque plan de chaque séquence
2. Associer chaque plan à une image de référence quand pertinent
3. Inclure des indications de rythme et de montage
4. Proposer des intentions de mise en scène
5. Suggérer l'ambiance sonore

Sois précis et technique tout en restant créatif."""

        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_treatment(
        self, 
        analysis: 'GlobalAnalysis', 
        context: Dict,
        pitch: str,
        sequencer: str
    ) -> str:
        """Génère un traitement complet (optionnel, format long)"""
        
        prompt = f"""En tant que scénariste, développe un TRAITEMENT complet à partir du pitch et du séquencier suivants.

PITCH:
{pitch}

SÉQUENCIER:
{sequencer}

---

Le traitement doit :
1. Développer chaque séquence en prose narrative (comme un roman court)
2. Inclure les dialogues esquissés
3. Décrire les émotions et les intentions des personnages
4. Détailler l'atmosphère visuelle et sonore
5. Créer des transitions fluides entre les séquences

Écris environ 2000-3000 mots, dans un style littéraire et évocateur."""

        response = self.model.generate_content(prompt)
        return response.text


class PitchRefiner:
    """Affine et améliore les pitchs générés"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def refine_for_tone(self, pitch: str, target_tone: str) -> str:
        """Affine le pitch pour correspondre à un ton spécifique"""
        
        tone_instructions = {
            'Naturaliste / Brut': """
                - Langage direct, sans fioritures
                - Descriptions réalistes et ancrées
                - Dialogues authentiques, argotiques si pertinent
                - Éviter le lyrisme excessif
                - Privilégier l'observation à l'interprétation
            """,
            'Poétique / Contemplatif': """
                - Langage évocateur et métaphorique
                - Rythme lent, respirations narratives
                - Attention aux détails sensoriels
                - Silences significatifs
                - Beauté dans l'ordinaire
            """,
            'Onirique / Surréaliste': """
                - Logique de rêve, associations libres
                - Glissements temporels et spatiaux
                - Symbolisme fort
                - Ambiguïté narrative assumée
                - Images mentales puissantes
            """,
            'Documentaire / Observationnel': """
                - Neutralité du regard
                - Respect des sujets
                - Contextualisation sociale
                - Absence de jugement
                - Vérité des situations
            """,
            'Fictionnel / Narratif': """
                - Arc dramatique classique
                - Personnages développés
                - Enjeux clairs
                - Progression narrative
                - Résolution satisfaisante
            """
        }
        
        instructions = tone_instructions.get(target_tone, "")
        
        prompt = f"""Réécris ce pitch pour qu'il corresponde parfaitement à la tonalité demandée.

PITCH ORIGINAL:
{pitch}

TONALITÉ CIBLE: {target_tone}

INSTRUCTIONS DE TON:
{instructions}

Conserve la structure et les éléments narratifs, mais adapte le style d'écriture."""

        response = self.model.generate_content(prompt)
        return response.text
    
    def add_references(self, pitch: str, references: List[str]) -> str:
        """Enrichit le pitch avec des références cinématographiques"""
        
        prompt = f"""Enrichis ce pitch en y intégrant subtilement les influences des références suivantes.

PITCH:
{pitch}

RÉFÉRENCES À INTÉGRER:
{', '.join(references)}

Ajoute une section "RÉFÉRENCES ET INFLUENCES" et intègre des clins d'œil stylistiques tout au long du texte."""

        response = self.model.generate_content(prompt)
        return response.text
