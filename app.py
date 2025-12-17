"""
🎬 PITCH GENERATOR
Application de génération de pitchs créatifs à partir d'images
Design inspiré Apple - Minimaliste et élégant
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
    initial_sidebar_state="collapsed"
)

# CSS Apple-style
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f5f5f7;
        --bg-tertiary: #e8e8ed;
        --text-primary: #1d1d1f;
        --text-secondary: #86868b;
        --accent: #0071e3;
        --accent-hover: #0077ed;
        --border: #d2d2d7;
        --shadow: rgba(0, 0, 0, 0.04);
        --radius: 12px;
        --radius-lg: 20px;
    }
    
    .stApp {
        background: var(--bg-secondary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        max-width: 1100px;
        padding: 2rem 1rem;
    }
    
    .app-header {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
    }
    
    .app-title {
        font-size: 2.75rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        margin: 0;
    }
    
    .app-subtitle {
        font-size: 1.125rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }
    
    .card {
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 12px var(--shadow), 0 0 1px rgba(0,0,0,0.08);
    }
    
    .card-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-secondary) !important;
        border: 1px solid transparent !important;
        border-radius: var(--radius) !important;
        padding: 0.875rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12) !important;
        background: var(--bg-primary) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-secondary) !important;
        border: none !important;
        border-radius: var(--radius) !important;
    }
    
    .stButton > button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 980px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: var(--accent-hover) !important;
        transform: scale(1.02);
        box-shadow: 0 4px 16px rgba(0, 113, 227, 0.25) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-secondary);
        border-radius: var(--radius);
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 1px 3px var(--shadow);
    }
    
    .progress-container {
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .progress-bar-bg {
        background: var(--bg-tertiary);
        border-radius: 6px;
        height: 6px;
        overflow: hidden;
        margin: 1rem auto;
        max-width: 300px;
    }
    
    .progress-bar-fill {
        background: linear-gradient(90deg, var(--accent), #34c759);
        height: 100%;
        border-radius: 6px;
        transition: width 0.3s ease;
    }
    
    .progress-text {
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    .progress-percent {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0.5rem 0;
    }
    
    .result-content {
        background: var(--bg-secondary);
        border-radius: var(--radius);
        padding: 1.5rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: var(--text-primary);
        white-space: pre-wrap;
    }
    
    .info-box {
        background: #f0f7ff;
        border-radius: var(--radius);
        padding: 1rem;
        font-size: 0.85rem;
        color: #1d4ed8;
        margin-top: 0.75rem;
        border-left: 3px solid var(--accent);
    }
    
    .stDownloadButton > button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 980px !important;
        font-weight: 500 !important;
    }
    
    .stDownloadButton > button:hover {
        background: var(--bg-tertiary) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    
    .stAlert {
        border-radius: var(--radius) !important;
        border: none !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .mode-selector {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
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
        'current_project': None,
        'input_mode': "Upload"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header():
    """Affiche l'en-tête"""
    st.markdown("""
        <div class="app-header">
            <h1 class="app-title">🎬 Pitch Generator</h1>
            <p class="app-subtitle">Transformez vos images en narrations cinématographiques</p>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Barre latérale avec configuration"""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration API")
        
        gemini_key = st.text_input(
            "Clé API Gemini",
            type="password",
            value=os.getenv("GEMINI_API_KEY", "")
        )
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
        
        google_key = st.text_input(
            "Clé API Google Drive",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", "")
        )
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
        
        st.divider()
        st.markdown("### 📁 Projets sauvegardés")
        
        project_manager = ProjectManager()
        projects = project_manager.list_projects()
        
        if projects:
            for project in projects[:5]:
                if st.button(f"📄 {project['name']}", key=f"load_{project['id']}", use_container_width=True):
                    loaded = project_manager.load_project(project['id'])
                    if loaded:
                        st.session_state.pitch = loaded.get('pitch')
                        st.session_state.sequencer = loaded.get('sequencer')
                        st.session_state.decoupage = loaded.get('decoupage')
                        st.rerun()
        else:
            st.caption("Aucun projet")


def render_input_section():
    """Section d'entrée des données"""
    
    # Mode d'entrée
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">📁 Source des images</p>', unsafe_allow_html=True)
    
    input_mode = st.radio(
        "Mode",
        ["Upload", "Google Drive", "Liens"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.input_mode = input_mode
    
    drive_url = None
    uploaded_files = None
    image_links = None
    
    if input_mode == "Google Drive":
        drive_url = st.text_input(
            "Lien du dossier Google Drive",
            placeholder="https://drive.google.com/drive/folders/..."
        )
        st.markdown("""
            <div class="info-box">
                💡 Le dossier doit être partagé avec "Tous ceux qui ont le lien"
            </div>
        """, unsafe_allow_html=True)
    
    elif input_mode == "Upload":
        uploaded_files = st.file_uploader(
            "Sélectionnez vos images",
            type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
            accept_multiple_files=True
        )
        if uploaded_files:
            st.success(f"✓ {len(uploaded_files)} images sélectionnées")
    
    else:
        image_links = st.text_area(
            "Liens des images (un par ligne)",
            placeholder="https://drive.google.com/file/d/xxx/view",
            height=100
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Brief
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">✏️ Brief créatif</p>', unsafe_allow_html=True)
    
    brief = st.text_area(
        "Décrivez votre vision",
        placeholder="Type de projet, ton souhaité, thématiques, références visuelles...",
        height=120,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Options
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">⚙️ Paramètres</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        format_type = st.selectbox("Format", ["Clip musical", "Court-métrage", "Documentaire", "Publicité", "Vidéo artistique"])
    with col2:
        duration = st.selectbox("Durée", ["1-2 min", "3-5 min", "5-10 min", "10-20 min", "20+ min"])
    with col3:
        tone = st.selectbox("Tonalité", ["Naturaliste", "Poétique", "Onirique", "Documentaire", "Narratif"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    modes_map = {
        "Upload": "📤 Upload direct",
        "Google Drive": "🔗 Lien Google Drive (dossier partagé)",
        "Liens": "📋 Liste de liens"
    }
    
    return {
        'mode': modes_map[input_mode],
        'drive_url': drive_url,
        'uploaded_files': uploaded_files,
        'image_links': image_links,
        'brief': brief,
        'format_type': format_type,
        'duration': duration,
        'tone': tone
    }


def render_progress(progress: float, message: str):
    """Barre de progression"""
    st.markdown(f"""
        <div class="progress-container">
            <p class="progress-text">{message}</p>
            <p class="progress-percent">{int(progress)}%</p>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {progress}%;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_results():
    """Affiche les résultats"""
    if not any([st.session_state.pitch, st.session_state.sequencer, st.session_state.decoupage]):
        return
    
    st.markdown("---")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">📄 Résultats générés</p>', unsafe_allow_html=True)
    
    tab_pitch, tab_seq, tab_dec, tab_images = st.tabs(["Pitch", "Séquencier", "Découpage", "Images"])
    
    with tab_pitch:
        if st.session_state.pitch:
            st.markdown(f'<div class="result-content">{st.session_state.pitch}</div>', unsafe_allow_html=True)
    
    with tab_seq:
        if st.session_state.sequencer:
            st.markdown(f'<div class="result-content">{st.session_state.sequencer}</div>', unsafe_allow_html=True)
    
    with tab_dec:
        if st.session_state.decoupage:
            st.markdown(f'<div class="result-content">{st.session_state.decoupage}</div>', unsafe_allow_html=True)
    
    with tab_images:
        if st.session_state.images_data:
            cols = st.columns(6)
            for idx, img in enumerate(st.session_state.images_data[:24]):
                with cols[idx % 6]:
                    if img.get('thumbnail'):
                        st.image(img['thumbnail'], use_container_width=True)
                    st.caption(img.get('name', '')[:15])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Export
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">💾 Exporter</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 PDF", use_container_width=True):
            export_pdf()
    
    with col2:
        if st.session_state.pitch:
            md_content = f"# Pitch\n\n{st.session_state.pitch}\n\n---\n\n# Séquencier\n\n{st.session_state.sequencer or ''}\n\n---\n\n# Découpage\n\n{st.session_state.decoupage or ''}"
            st.download_button(
                "📥 Markdown",
                md_content,
                file_name=f"pitch_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    with col3:
        project_name = st.text_input("Nom du projet", placeholder="Mon projet", label_visibility="collapsed")
    
    with col4:
        if st.button("💾 Sauvegarder", use_container_width=True):
            if project_name:
                save_project(project_name)
                st.success("✓ Sauvegardé")
    
    st.markdown('</div>', unsafe_allow_html=True)


def load_images_from_uploads(uploaded_files):
    """Charge les images uploadées"""
    import base64
    from PIL import Image as PILImage
    import io
    
    images = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            img = PILImage.open(uploaded_file)
            img.thumbnail((1024, 1024), PILImage.Resampling.LANCZOS)
            
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
            print(f"Erreur: {e}")
    
    return images


def load_images_from_links(links_text):
    """Charge depuis des liens"""
    from src.drive_loader import DriveLoaderManual
    
    loader = DriveLoaderManual()
    file_ids = loader.extract_ids_from_links(links_text)
    
    if not file_ids:
        raise ValueError("Aucun lien valide trouvé")
    
    return loader.load_from_ids(file_ids)


def process_images(inputs: dict):
    """Traite les images et génère le pitch"""
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        mode = inputs['mode']
        
        with progress_placeholder.container():
            render_progress(10, "Chargement des images...")
        
        if "Google Drive" in mode:
            if not inputs['drive_url']:
                raise ValueError("Veuillez entrer un lien Google Drive")
            loader = DriveLoader()
            images = loader.load_from_url(inputs['drive_url'])
        
        elif "Upload" in mode:
            if not inputs['uploaded_files']:
                raise ValueError("Veuillez uploader au moins une image")
            images = load_images_from_uploads(inputs['uploaded_files'])
        
        else:
            if not inputs['image_links']:
                raise ValueError("Veuillez coller au moins un lien")
            images = load_images_from_links(inputs['image_links'])
        
        st.session_state.images_data = images
        
        with progress_placeholder.container():
            render_progress(25, f"{len(images)} images chargées")
        
        valid_images = [img for img in images if 'data' in img and img['data']]
        
        if not valid_images:
            raise ValueError("Aucune image valide")
        
        with progress_placeholder.container():
            render_progress(40, f"Analyse de {len(valid_images)} images...")
        
        analyzer = ImageAnalyzer()
        analysis = analyzer.analyze_batch(valid_images)
        st.session_state.analysis_results = analysis
        
        with progress_placeholder.container():
            render_progress(70, "Génération du pitch...")
        
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
            render_progress(100, "Terminé !")
        
        status_placeholder.success("✓ Pitch généré avec succès !")
        
    except Exception as e:
        status_placeholder.error(f"Erreur : {str(e)}")


def export_pdf():
    """Export PDF"""
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
                "📥 Télécharger le PDF",
                f.read(),
                file_name=f"pitch_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Erreur PDF : {e}")


def save_project(name: str):
    """Sauvegarde le projet"""
    ProjectManager().save_project(
        name=name,
        data={
            'pitch': st.session_state.pitch,
            'sequencer': st.session_state.sequencer,
            'decoupage': st.session_state.decoupage,
            'images_data': st.session_state.images_data,
        }
    )


def main():
    """Fonction principale"""
    init_session_state()
    render_header()
    render_sidebar()
    
    inputs = render_input_section()
    
    # Bouton centré
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Générer le pitch", type="primary", use_container_width=True):
            mode = inputs['mode']
            
            if "Google Drive" in mode and not inputs['drive_url']:
                st.warning("Veuillez entrer un lien Google Drive")
            elif "Upload" in mode and not inputs['uploaded_files']:
                st.warning("Veuillez uploader au moins une image")
            elif "Liens" in mode and not inputs['image_links']:
                st.warning("Veuillez coller au moins un lien")
            elif not os.getenv("GEMINI_API_KEY"):
                st.warning("⚠️ Configurez votre clé API Gemini dans la barre latérale (flèche > en haut à gauche)")
            else:
                process_images(inputs)
    
    render_results()


if __name__ == "__main__":
    main()
