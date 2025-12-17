"""
🎬 PITCH GENERATOR
Application de génération de pitchs créatifs à partir d'images
"""

import streamlit as st
import os
from datetime import datetime
from src.drive_loader import DriveLoader, DriveLoaderManual
from src.image_analyzer import ImageAnalyzer
from src.narrative_builder import NarrativeBuilder
from src.pdf_generator import PDFGenerator
from src.project_manager import ProjectManager
from src.video_prompt_generator import VideoPromptGenerator

# Configuration
st.set_page_config(
    page_title="Pitch Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS minimal - sans toucher aux inputs
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialise les variables de session"""
    if 'pitch' not in st.session_state:
        st.session_state.pitch = None
    if 'sequencer' not in st.session_state:
        st.session_state.sequencer = None
    if 'decoupage' not in st.session_state:
        st.session_state.decoupage = None
    if 'video_prompts' not in st.session_state:
        st.session_state.video_prompts = None
    if 'images_data' not in st.session_state:
        st.session_state.images_data = []
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None


def render_sidebar():
    """Barre latérale"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        gemini_key = st.text_input(
            "Clé API Gemini",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            key="sidebar_gemini_key"
        )
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
        
        google_key = st.text_input(
            "Clé API Google Drive",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            key="sidebar_google_key"
        )
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
        
        st.divider()
        
        st.header("📁 Projets")
        pm = ProjectManager()
        projects = pm.list_projects()
        
        if projects:
            for p in projects[:5]:
                if st.button(f"📄 {p['name']}", key=f"proj_{p['id']}"):
                    data = pm.load_project(p['id'])
                    if data:
                        st.session_state.pitch = data.get('pitch')
                        st.session_state.sequencer = data.get('sequencer')
                        st.session_state.decoupage = data.get('decoupage')
                        st.session_state.video_prompts = data.get('video_prompts')
                        st.rerun()
        else:
            st.caption("Aucun projet sauvegardé")


def load_images_from_uploads(files):
    """Charge les images uploadées"""
    import base64
    from PIL import Image as PILImage
    import io
    
    images = []
    for idx, f in enumerate(files):
        try:
            img = PILImage.open(f)
            img.thumbnail((1024, 1024), PILImage.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=85)
            data = buffer.getvalue()
            
            images.append({
                'id': f"upload_{idx}",
                'name': f.name,
                'data': data,
                'base64': base64.b64encode(data).decode('utf-8'),
                'thumbnail': None,
                'mime_type': 'image/jpeg'
            })
        except Exception as e:
            st.warning(f"Erreur image {f.name}: {e}")
    
    return images


def process_images(mode, drive_url, uploaded_files, image_links, brief, format_type, duration, tone):
    """Traite les images et génère le pitch"""
    
    progress = st.progress(0, text="Démarrage...")
    
    try:
        # 1. Charger les images
        progress.progress(10, text="Chargement des images...")
        
        if mode == "Upload":
            if not uploaded_files:
                st.error("Veuillez uploader des images")
                return
            images = load_images_from_uploads(uploaded_files)
        
        elif mode == "Google Drive":
            if not drive_url:
                st.error("Veuillez entrer un lien Google Drive")
                return
            loader = DriveLoader()
            images = loader.load_from_url(drive_url)
        
        else:  # Liens
            if not image_links:
                st.error("Veuillez coller des liens")
                return
            loader = DriveLoaderManual()
            ids = loader.extract_ids_from_links(image_links)
            images = loader.load_from_ids(ids)
        
        st.session_state.images_data = images
        
        # Filtrer images valides
        valid_images = [img for img in images if img.get('data')]
        
        if not valid_images:
            st.error("Aucune image valide chargée")
            return
        
        progress.progress(30, text=f"{len(valid_images)} images chargées")
        
        # 2. Analyser
        progress.progress(40, text="Analyse des images...")
        
        analyzer = ImageAnalyzer()
        analysis = analyzer.analyze_batch(valid_images)
        st.session_state.analysis_results = analysis
        
        progress.progress(60, text="Analyse terminée")
        
        # 3. Générer
        progress.progress(70, text="Génération du pitch...")
        
        builder = NarrativeBuilder()
        context = {
            'brief': brief,
            'format': format_type,
            'duration': duration,
            'tone': tone
        }
        
        results = builder.generate_all(analysis, context)
        
        st.session_state.pitch = results['pitch']
        st.session_state.sequencer = results['sequencer']
        st.session_state.decoupage = results['decoupage']
        
        progress.progress(100, text="Terminé !")
        st.success("✅ Pitch généré avec succès !")
        
    except Exception as e:
        st.error(f"Erreur : {str(e)}")


def generate_video_prompts(platform, style, duration):
    """Génère les prompts vidéo"""
    if not st.session_state.decoupage:
        st.warning("Générez d'abord le découpage")
        return
    
    try:
        gen = VideoPromptGenerator()
        prompts = gen.generate_prompts_from_decoupage(
            st.session_state.decoupage,
            platform=platform,
            style_context=style,
            default_duration=duration
        )
        st.session_state.video_prompts = prompts
        st.success(f"✅ {len(prompts)} prompts générés")
    except Exception as e:
        st.error(f"Erreur : {str(e)}")


def export_pdf():
    """Export PDF"""
    try:
        gen = PDFGenerator()
        path = gen.generate(
            pitch=st.session_state.pitch,
            sequencer=st.session_state.sequencer,
            decoupage=st.session_state.decoupage,
            images=st.session_state.images_data
        )
        with open(path, 'rb') as f:
            st.download_button(
                "📥 Télécharger le PDF",
                f.read(),
                file_name=f"pitch_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Erreur PDF : {str(e)}")


def main():
    init_session_state()
    render_sidebar()
    
    # Header
    st.markdown('<h1 class="main-title">🎬 Pitch Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transformez vos images en narrations cinématographiques</p>', unsafe_allow_html=True)
    
    # === SECTION ENTRÉE ===
    st.header("📁 Source des images")
    
    mode = st.radio(
        "Comment charger vos images ?",
        ["Upload", "Google Drive", "Liens"],
        horizontal=True
    )
    
    drive_url = None
    uploaded_files = None
    image_links = None
    
    if mode == "Upload":
        uploaded_files = st.file_uploader(
            "Sélectionnez vos images",
            type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
            accept_multiple_files=True
        )
        if uploaded_files:
            st.success(f"✓ {len(uploaded_files)} images sélectionnées")
    
    elif mode == "Google Drive":
        drive_url = st.text_input(
            "Lien du dossier Google Drive",
            placeholder="https://drive.google.com/drive/folders/..."
        )
        st.info("💡 Le dossier doit être partagé avec 'Tous ceux qui ont le lien'")
    
    else:
        image_links = st.text_area(
            "Liens des images (un par ligne)",
            placeholder="https://drive.google.com/file/d/xxx/view\nhttps://drive.google.com/file/d/yyy/view",
            height=100
        )
    
    st.divider()
    
    # Brief
    st.header("✏️ Brief créatif")
    
    brief = st.text_area(
        "Décrivez votre vision du projet",
        placeholder="Type de projet (clip, documentaire...), ton souhaité, thématiques, références visuelles...",
        height=150
    )
    
    st.divider()
    
    # Options
    st.header("⚙️ Paramètres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        format_type = st.selectbox(
            "Format",
            ["Clip musical", "Court-métrage", "Documentaire", "Publicité", "Vidéo artistique"]
        )
    
    with col2:
        duration = st.selectbox(
            "Durée cible",
            ["1-2 min", "3-5 min", "5-10 min", "10-20 min", "20+ min"]
        )
    
    with col3:
        tone = st.selectbox(
            "Tonalité",
            ["Naturaliste", "Poétique", "Onirique", "Documentaire", "Narratif"]
        )
    
    st.divider()
    
    # Bouton génération
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Générer le pitch", type="primary", use_container_width=True):
            if not os.getenv("GEMINI_API_KEY"):
                st.error("⚠️ Configurez votre clé API Gemini dans la barre latérale (flèche > en haut à gauche)")
            else:
                process_images(mode, drive_url, uploaded_files, image_links, brief, format_type, duration, tone)
    
    # === SECTION RÉSULTATS ===
    if st.session_state.pitch or st.session_state.sequencer or st.session_state.decoupage:
        st.divider()
        st.header("📄 Résultats")
        
        tabs = st.tabs(["Pitch", "Séquencier", "Découpage", "🎬 Prompts Vidéo", "Images"])
        
        with tabs[0]:
            if st.session_state.pitch:
                st.markdown(st.session_state.pitch)
        
        with tabs[1]:
            if st.session_state.sequencer:
                st.markdown(st.session_state.sequencer)
        
        with tabs[2]:
            if st.session_state.decoupage:
                st.markdown(st.session_state.decoupage)
        
        with tabs[3]:
            st.subheader("Génération de prompts vidéo")
            
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox(
                    "Plateforme",
                    ['veo3', 'kling', 'runway'],
                    format_func=lambda x: {'veo3': 'Google Veo 3', 'kling': 'Kling 2.6', 'runway': 'Runway Gen-4'}[x]
                )
            with col2:
                vid_duration = st.number_input("Durée par défaut (sec)", 2, 30, 5)
            
            vid_style = st.text_input(
                "Style visuel (optionnel)",
                placeholder="cinematic, film grain, natural lighting..."
            )
            
            if st.button("🎬 Générer les prompts"):
                generate_video_prompts(platform, vid_style, vid_duration)
            
            if st.session_state.video_prompts:
                st.divider()
                for idx, p in enumerate(st.session_state.video_prompts):
                    with st.expander(f"Plan {p.get('shot_number', idx+1)} | {p.get('shot_value', '')} | {p.get('duration', 5)}s"):
                        if p.get('image_ref'):
                            st.caption(f"📷 Image: {p.get('image_ref')}")
                        st.code(p.get('prompt', ''))
        
        with tabs[4]:
            if st.session_state.images_data:
                cols = st.columns(6)
                for idx, img in enumerate(st.session_state.images_data[:30]):
                    with cols[idx % 6]:
                        if img.get('thumbnail'):
                            st.image(img['thumbnail'], use_container_width=True)
                        st.caption(img.get('name', '')[:12])
        
        # Export
        st.divider()
        st.header("💾 Export")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Exporter PDF"):
                export_pdf()
        
        with col2:
            if st.session_state.pitch:
                content = f"# Pitch\n\n{st.session_state.pitch}\n\n---\n\n# Séquencier\n\n{st.session_state.sequencer or ''}\n\n---\n\n# Découpage\n\n{st.session_state.decoupage or ''}"
                st.download_button("📥 Markdown", content, f"pitch_{datetime.now().strftime('%Y%m%d')}.md")
        
        with col3:
            if st.session_state.video_prompts:
                lines = []
                for p in st.session_state.video_prompts:
                    lines.append(f"Plan {p.get('shot_number', '?')} | {p.get('shot_value', '')}")
                    lines.append(p.get('prompt', ''))
                    lines.append("")
                st.download_button("🎬 Prompts vidéo", "\n".join(lines), f"prompts_{datetime.now().strftime('%Y%m%d')}.txt")
        
        with col4:
            project_name = st.text_input("Nom du projet", placeholder="Mon projet", label_visibility="collapsed")
            if st.button("💾 Sauvegarder") and project_name:
                ProjectManager().save_project(project_name, {
                    'pitch': st.session_state.pitch,
                    'sequencer': st.session_state.sequencer,
                    'decoupage': st.session_state.decoupage,
                    'video_prompts': st.session_state.video_prompts
                })
                st.success("✓ Sauvegardé")


if __name__ == "__main__":
    main()
