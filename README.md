# 🎬 Pitch Generator

Outil de génération automatique de pitchs créatifs à partir d'images.

Transformez votre moodboard en :
- **Pitch narratif** complet
- **Séquencier** détaillé  
- **Découpage technique** professionnel
- **Export PDF** stylisé avec vignettes

---

## 📋 Prérequis

1. **Compte Google Cloud** avec les APIs activées :
   - Google Drive API
   - Generative Language API (Gemini)

2. **Clé API Gemini** depuis [Google AI Studio](https://aistudio.google.com)

3. **Python 3.9+**

---

## 🚀 Installation locale

### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/pitch-generator.git
cd pitch-generator
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les credentials

Créez un fichier `.env` à la racine :

```env
GEMINI_API_KEY=votre_clé_api_gemini
GOOGLE_API_KEY=votre_clé_api_google  # Optionnel, pour Drive public
```

### 5. Lancer l'application

```bash
streamlit run app.py
```

L'application sera accessible sur `http://localhost:8501`

---

## ☁️ Déploiement sur Streamlit Cloud

### 1. Préparer le repository GitHub

Poussez le code sur GitHub (repository public ou privé).

### 2. Se connecter à Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Connectez votre compte GitHub
3. Cliquez sur "New app"

### 3. Configurer l'application

- **Repository** : votre-username/pitch-generator
- **Branch** : main
- **Main file path** : app.py

### 4. Configurer les secrets

Dans les settings de l'app Streamlit Cloud, ajoutez vos secrets :

```toml
GEMINI_API_KEY = "votre_clé_api_gemini"
GOOGLE_API_KEY = "votre_clé_api_google"
```

### 5. Déployer

Cliquez sur "Deploy!" et attendez quelques minutes.

---

## 🔧 Configuration Google Cloud

### Activer les APIs

1. Créez un projet sur [console.cloud.google.com](https://console.cloud.google.com)
2. Activez les APIs :
   - APIs & Services → Library → "Google Drive API" → Enable
   - APIs & Services → Library → "Generative Language API" → Enable

### Créer les credentials

#### Pour un usage local (OAuth) :

1. APIs & Services → Credentials → Create Credentials → OAuth client ID
2. Application type : Desktop app
3. Téléchargez `credentials.json`
4. Placez-le à la racine du projet

#### Pour Streamlit Cloud (API Key) :

1. APIs & Services → Credentials → Create Credentials → API key
2. Restreignez la clé aux APIs Google Drive et Generative Language
3. Ajoutez la clé dans les secrets Streamlit

---

## 📁 Structure du projet

```
pitch-generator/
├── app.py                 # Application principale Streamlit
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement (local)
├── credentials.json       # OAuth credentials (local)
├── .streamlit/
│   └── config.toml       # Configuration Streamlit
└── src/
    ├── __init__.py
    ├── drive_loader.py    # Chargement images Google Drive
    ├── image_analyzer.py  # Analyse via Gemini
    ├── narrative_builder.py # Génération narrative
    ├── pdf_generator.py   # Export PDF
    └── project_manager.py # Gestion des projets
```

---

## 🎯 Utilisation

### 1. Préparer vos images

- Placez vos images dans un dossier Google Drive
- Partagez le dossier (au moins en lecture)
- Copiez le lien de partage

### 2. Configurer l'analyse

- Collez le lien du dossier Drive
- Rédigez votre brief créatif
- Sélectionnez le format, la durée et le ton

### 3. Générer le pitch

- Cliquez sur "Générer le pitch"
- Attendez l'analyse (~2 min pour 100 images)
- Consultez les résultats dans les onglets

### 4. Exporter

- **PDF** : Document stylisé avec vignettes
- **Markdown** : Format texte brut
- **Sauvegarde** : Projets récupérables

---

## ⚙️ Personnalisation

### Modifier les prompts

Les prompts de génération se trouvent dans `src/narrative_builder.py`.
Vous pouvez les adapter à votre style.

### Modifier le style du PDF

Le générateur PDF est dans `src/pdf_generator.py`.
Personnalisez les styles, polices et mise en page.

### Ajouter des tons narratifs

Dans `src/narrative_builder.py`, classe `PitchRefiner`,
ajoutez vos propres instructions de ton dans `tone_instructions`.

---

## 🔒 Sécurité

- Ne commitez jamais vos clés API sur GitHub
- Utilisez les secrets Streamlit Cloud
- Limitez les permissions de vos clés API
- Désactivez les clés inutilisées

---

## 📝 Licence

MIT License - Libre d'utilisation et de modification.

---

## 🤝 Support

Pour toute question ou suggestion :
- Ouvrez une issue sur GitHub
- Contactez [votre email]

---

**Bon pitch ! 🎬**
