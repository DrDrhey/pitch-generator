"""
🎬 PITCH GENERATOR
Application de génération de pitchs créatifs à partir d'images
"""

import streamlit as st
import os
from datetime import datetime
from src.drive_loader import DriveLoader, DriveLoaderLite, DriveLoaderManual
from src.image_analyzer import ImageAnalyzer
from src.narrative_builder import NarrativeBuilder
from src.pdf_generator import PDFGenerator
from src.project_manager import ProjectManager

# Configuration de la page
st.set_page_config(
    page_title="Pitch Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour une interface élégante
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');
    
    :root {
        --bg-primary: #0a0a0b;
        --bg-secondary: #141416;
        --bg-tertiary: #1c1c1f;
        --accent: #e63946;
        --accent-soft: #ff6b6b;
        --text-primary: #f8f8f8;
        --text-secondary: #a0a0a0;
        --border: #2a2a2e;
    }
    
    .stApp {
        background: linear-gradient(180deg, var(--bg-primary) 0%, #0d0d0f 100%);
    }
    
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-family: 'Crimson Pro', serif;
        font-size: 1.3rem;
        color: var(--text-secondary);
        font-style: italic;
        margin-bottom: 2rem;
    }
    
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--accent);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-soft);
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .stTextArea textarea {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'Crimson Pro', serif !important;
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
    }
    
    .stTextInput input {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, #c1121f 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(230, 57, 70, 0.3) !important;
    }
    
    .output-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 2rem;
        font-family: 'Crimson Pro', serif;
        font-size: 1.1rem;
        line-height: 1.8;
        color: var(--text-primary);
    }
    
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 0.75rem;
    }
    
    .image-thumb {
        aspect-ratio: 1;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    .progress-bar {
        background: var(--bg-tertiary);
        border-radius: 4px;
        height: 8px;
        overflow: hidden;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent-soft) 100%);
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .tab-content {
        padding: 1.5rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: var(--bg-secondary);
    }
    
    .sidebar-project {
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .sidebar-project:hover {
        border-color: var(--accent);
    }
    
    .project-name {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    
    .project-date {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialise les variables de session"""
    defaults = {
        'analysis_results': None,
        'pitch': None,
        'sequencer': None,
        'decoupage': None,
        'images_data': [],
        'processing': False,
        'progress': 0,
        'current_project': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header():
    """Affiche l'en-tête de l'application"""
    st.markdown('<h1 class="main-header">🎬 Pitch Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transformez vos images en narrations cinématographiques</p>', unsafe_allow_html=True)


def render_sidebar():
    """Affiche la barre latérale avec les projets sauvegardés"""
    with st.sidebar:
        st.markdown('<p class="section-title">📁 Projets sauvegardés</p>', unsafe_allow_html=True)
        
        project_manager = ProjectManager()
        projects = project_manager.list_projects()
        
        if projects:
            for project in projects:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📄 {project['name']}", key=f"load_{project['id']}"):
                        loaded = project_manager.load_project(project['id'])
                        if loaded:
                            st.session_state.current_project = loaded
                            st.session_state.pitch = loaded.get('pitch')
                            st.session_state.sequencer = loaded.get('sequencer')
                            st.session_state.decoupage = loaded.get('decoupage')
                            st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{project['id']}"):
                        project_manager.delete_project(project['id'])
                        st.rerun()
        else:
            st.markdown("*Aucun projet sauvegardé*")
        
        st.divider()
        
        # Configuration API
        st.markdown('<p class="section-title">⚙️ Configuration</p>', unsafe_allow_html=True)
        
        gemini_key = st.text_input(
            "Clé API Gemini",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Votre clé API Google Gemini"
        )
        
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            st.success("✓ API configurée")


def render_input_section():
    """Affiche la section d'entrée des données"""
    
    st.markdown('<p class="section-title">📁 Source des images</p>', unsafe_allow_html=True)
    
    # Choix du mode d'entrée
    input_mode = st.radio(
        "Comment souhaitez-vous charger vos images ?",
        ["🔗 Lien Google Drive (dossier partagé)", "📤 Upload direct", "📋 Liste de liens"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    drive_url = None
    uploaded_files = None
    image_links = None
    
    if input_mode == "🔗 Lien Google Drive (dossier partagé)":
        drive_url = st.text_input(
            "Lien du dossier Google Drive",
            placeholder="https://drive.google.com/drive/folders/...",
            help="Collez le lien de partage de votre dossier. Le dossier doit être partagé avec 'Tous ceux qui ont le lien'."
        )
        
        st.info("""
        💡 **Comment partager votre dossier Google Drive :**
        1. Clic droit sur le dossier → "Partager"
        2. Cliquez sur "Accès limité" → "Tous ceux qui ont le lien"
        3. Copiez le lien et collez-le ci-dessus
        """)
    
    elif input_mode == "📤 Upload direct":
        uploaded_files = st.file_uploader(
            "Uploadez vos images",
            type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
            accept_multiple_files=True,
            help="Sélectionnez plusieurs images à la fois (max 200MB au total)"
        )
        
        if uploaded_files:
            st.success(f"✓ {len(uploaded_files)} images sélectionnées")
    
    else:  # Liste de liens
        image_links = st.text_area(
            "Collez les liens des images (un par ligne)",
            placeholder="""https://drive.google.com/file/d/xxx/view
https://drive.google.com/file/d/yyy/view
https://drive.google.com/file/d/zzz/view""",
            height=150,
            help="Copiez les liens de partage de chaque image"
        )
    
    st.markdown('<p class="section-title">✏️ Brief créatif</p>', unsafe_allow_html=True)
    
    brief = st.text_area(
        "Décrivez votre vision",
        placeholder="""Décrivez ici votre projet :
- Type : clip musical, court-métrage, documentaire...
- Ton : naturaliste, onirique, brut, poétique...
- Thématiques : jeunesse, urbanité, mélancolie...
- Références : réalisateurs, photographes, œuvres...
- Contraintes techniques : durée, format...""",
        height=200
    )
    
    # Options avancées
    st.markdown('<p class="section-title">⚙️ Options</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        format_type = st.selectbox(
            "Format",
            ["Clip musical", "Court-métrage", "Documentaire", "Film publicitaire", "Vidéo artistique"]
        )
    
    with col2:
        duration = st.selectbox(
            "Durée cible",
            ["1-2 min", "3-5 min", "5-10 min", "10-20 min", "20+ min"]
        )
    
    with col3:
        tone = st.selectbox(
            "Tonalité",
            ["Naturaliste / Brut", "Poétique / Contemplatif", "Onirique / Surréaliste", "Documentaire / Observationnel", "Fictionnel / Narratif"]
        )
    
    return {
        'mode': input_mode,
        'drive_url': drive_url,
        'uploaded_files': uploaded_files,
        'image_links': image_links,
        'brief': brief,
        'format_type': format_type,
        'duration': duration,
        'tone': tone
    }


def render_progress(progress: float, message: str):
    """Affiche la barre de progression"""
    st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #a0a0a0; font-size: 0.9rem;">{message}</span>
                <span style="color: #e63946; font-weight: 600;">{int(progress)}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress}%;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_results():
    """Affiche les résultats de l'analyse"""
    if not any([st.session_state.pitch, st.session_state.sequencer, st.session_state.decoupage]):
        return
    
    st.markdown('<p class="section-title">📄 Résultats</p>', unsafe_allow_html=True)
    
    # Onglets pour les différents outputs
    tab_pitch, tab_seq, tab_dec, tab_images = st.tabs(["Pitch", "Séquencier", "Découpage", "Moodboard"])
    
    with tab_pitch:
        if st.session_state.pitch:
            st.markdown(f'<div class="output-container">{st.session_state.pitch}</div>', unsafe_allow_html=True)
    
    with tab_seq:
        if st.session_state.sequencer:
            st.markdown(f'<div class="output-container">{st.session_state.sequencer}</div>', unsafe_allow_html=True)
    
    with tab_dec:
        if st.session_state.decoupage:
            st.markdown(f'<div class="output-container">{st.session_state.decoupage}</div>', unsafe_allow_html=True)
    
    with tab_images:
        if st.session_state.images_data:
            cols = st.columns(6)
            for idx, img in enumerate(st.session_state.images_data[:30]):  # Limite à 30 vignettes
                with cols[idx % 6]:
                    if img.get('thumbnail'):
                        st.image(img['thumbnail'], caption=img.get('name', ''), use_container_width=True)
                    else:
                        st.markdown(f"📷 {img.get('name', 'Image')}")
    
    # Boutons d'export
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Exporter PDF", type="primary"):
            export_pdf()
    
    with col2:
        if st.button("📥 Exporter Markdown"):
            export_markdown()
    
    with col3:
        project_name = st.text_input("Nom du projet", placeholder="Mon projet")
    
    with col4:
        if st.button("💾 Sauvegarder"):
            if project_name:
                save_project(project_name)
                st.success("Projet sauvegardé !")


def load_images_from_uploads(uploaded_files, progress_callback=None):
    """Charge les images depuis les fichiers uploadés"""
    import base64
    from PIL import Image as PILImage
    import io
    
    images = []
    total = len(uploaded_files)
    
    for idx, uploaded_file in enumerate(uploaded_files):
        if progress_callback:
            progress_callback((idx + 1) / total, f"Traitement : {uploaded_file.name}")
        
        try:
            # Lire et redimensionner l'image
            img = PILImage.open(uploaded_file)
            img.thumbnail((1024, 1024), PILImage.Resampling.LANCZOS)
            
            # Convertir en bytes
            buffer = io.BytesIO()
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(buffer, format='JPEG', quality=85)
            image_data = buffer.getvalue()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            images.append({
                'id': f"upload_{idx}",
                'name': uploaded_file.name,
                'data': image_data,
                'base64': image_b64,
                'thumbnail': None,
                'mime_type': 'image/jpeg'
            })
        except Exception as e:
            print(f"Erreur traitement {uploaded_file.name}: {e}")
    
    return images


def load_images_from_links(links_text, progress_callback=None):
    """Charge les images depuis une liste de liens"""
    from src.drive_loader import DriveLoaderManual
    
    loader = DriveLoaderManual()
    file_ids = loader.extract_ids_from_links(links_text)
    
    if not file_ids:
        raise ValueError("Aucun lien valide trouvé. Vérifiez le format des liens.")
    
    return loader.load_from_ids(file_ids, progress_callback)


def process_images(inputs: dict):
    """Traite les images et génère le pitch"""
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        mode = inputs['mode']
        
        # Étape 1: Chargement des images selon le mode
        with progress_placeholder.container():
            render_progress(10, "Chargement des images...")
        
        if mode == "🔗 Lien Google Drive (dossier partagé)":
            drive_url = inputs['drive_url']
            if not drive_url:
                raise ValueError("Veuillez entrer un lien Google Drive")
            
            from src.drive_loader import DriveLoader
            loader = DriveLoader()
            
            images = loader.load_from_url(
                drive_url,
                progress_callback=lambda p, m: None
            )
        
        elif mode == "📤 Upload direct":
            uploaded_files = inputs['uploaded_files']
            if not uploaded_files:
                raise ValueError("Veuillez uploader au moins une image")
            
            images = load_images_from_uploads(
                uploaded_files,
                progress_callback=lambda p, m: None
            )
        
        else:  # Liste de liens
            image_links = inputs['image_links']
            if not image_links:
                raise ValueError("Veuillez coller au moins un lien d'image")
            
            images = load_images_from_links(
                image_links,
                progress_callback=lambda p, m: None
            )
        
        st.session_state.images_data = images
        
        with progress_placeholder.container():
            render_progress(30, f"{len(images)} images chargées")
        
        if len(images) == 0:
            raise ValueError("Aucune image n'a pu être chargée")
        
        # Filtrer les images sans données
        valid_images = [img for img in images if 'data' in img and img['data']]
        
        if len(valid_images) == 0:
            raise ValueError("Aucune image valide n'a pu être téléchargée")
        
        # Étape 2: Analyse des images
        with progress_placeholder.container():
            render_progress(40, f"Analyse de {len(valid_images)} images...")
        
        analyzer = ImageAnalyzer()
        analysis = analyzer.analyze_batch(
            valid_images, 
            progress_callback=lambda p, m: progress_placeholder.container() or render_progress(40 + p * 0.3, m)
        )
        st.session_state.analysis_results = analysis
        
        with progress_placeholder.container():
            render_progress(70, "Analyse terminée")
        
        # Étape 3: Génération narrative
        with progress_placeholder.container():
            render_progress(80, "Génération du pitch...")
        
        builder = NarrativeBuilder()
        context = {
            'brief': inputs['brief'],
            'format': inputs['format_type'],
            'duration': inputs['duration'],
            'tone': inputs['tone']
        }
        
        results = builder.generate_all(analysis, context)
        
        st.session_state.pitch = results['pitch']
        st.session_state.sequencer = results['sequencer']
        st.session_state.decoupage = results['decoupage']
        
        with progress_placeholder.container():
            render_progress(100, "Génération terminée !")
        
        status_placeholder.success("✅ Pitch généré avec succès !")
        
    except Exception as e:
        status_placeholder.error(f"❌ Erreur : {str(e)}")
        raise e


def export_pdf():
    """Exporte les résultats en PDF"""
    try:
        generator = PDFGenerator()
        pdf_path = generator.generate(
            pitch=st.session_state.pitch,
            sequencer=st.session_state.sequencer,
            decoupage=st.session_state.decoupage,
            images=st.session_state.images_data
        )
        
        with open(pdf_path, 'rb') as f:
            st.download_button(
                label="📥 Télécharger le PDF",
                data=f.read(),
                file_name=f"pitch_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Erreur lors de l'export PDF : {e}")


def export_markdown():
    """Exporte les résultats en Markdown"""
    content = f"""# Pitch

{st.session_state.pitch or ''}

---

# Séquencier

{st.session_state.sequencer or ''}

---

# Découpage technique

{st.session_state.decoupage or ''}
"""
    
    st.download_button(
        label="📥 Télécharger MD",
        data=content,
        file_name=f"pitch_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown"
    )


def save_project(name: str):
    """Sauvegarde le projet actuel"""
    project_manager = ProjectManager()
    project_manager.save_project(
        name=name,
        data={
            'pitch': st.session_state.pitch,
            'sequencer': st.session_state.sequencer,
            'decoupage': st.session_state.decoupage,
            'images_data': st.session_state.images_data,
            'analysis_results': st.session_state.analysis_results
        }
    )


def main():
    """Fonction principale"""
    init_session_state()
    render_header()
    render_sidebar()
    
    # Section d'entrée
    inputs = render_input_section()
    
    # Bouton de génération
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button("🚀 GÉNÉRER LE PITCH", type="primary", use_container_width=True)
    
    if generate_btn:
        # Vérification des entrées selon le mode
        mode = inputs['mode']
        
        if mode == "🔗 Lien Google Drive (dossier partagé)" and not inputs['drive_url']:
            st.warning("⚠️ Veuillez entrer un lien Google Drive")
        elif mode == "📤 Upload direct" and not inputs['uploaded_files']:
            st.warning("⚠️ Veuillez uploader au moins une image")
        elif mode == "📋 Liste de liens" and not inputs['image_links']:
            st.warning("⚠️ Veuillez coller au moins un lien d'image")
        elif not os.getenv("GEMINI_API_KEY"):
            st.warning("⚠️ Veuillez configurer votre clé API Gemini dans la barre latérale")
        else:
            process_images(inputs)
    
    # Affichage des résultats
    render_results()


if __name__ == "__main__":
    main()
