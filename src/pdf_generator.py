"""
Module de génération de PDF professionnels
Tous les styles utilisent le préfixe PG_ pour éviter les conflits
"""

import os
import io
import re
import base64
from datetime import datetime
from typing import List, Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage


# Couleurs
COLOR_PRIMARY = '#1a1a2e'
COLOR_ACCENT = '#e94560'
COLOR_TEXT = '#2d2d2d'
COLOR_LIGHT = '#666666'
COLOR_BORDER = '#e0e0e0'


def clean_text(text: str) -> str:
    """
    Nettoie le texte pour ReportLab - supprime TOUT formatage
    """
    if not text:
        return ""
    
    # Supprimer les balises HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Supprimer le markdown
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    text = re.sub(r'[\*_]{1,2}', '', text)
    
    # Échapper XML
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text


class PDFGenerator:
    """Génère des PDF professionnels"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """
        Ajoute des styles personnalisés avec préfixe PG_ pour éviter les conflits
        """
        # Titre couverture
        self.styles.add(ParagraphStyle(
            name='PG_CoverTitle',
            fontName='Helvetica-Bold',
            fontSize=32,
            leading=40,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor(COLOR_PRIMARY)
        ))
        
        # Sous-titre couverture
        self.styles.add(ParagraphStyle(
            name='PG_CoverSubtitle',
            fontName='Helvetica',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor(COLOR_LIGHT)
        ))
        
        # Titre de section
        self.styles.add(ParagraphStyle(
            name='PG_SectionTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=24,
            spaceBefore=25,
            spaceAfter=12,
            textColor=colors.HexColor(COLOR_PRIMARY)
        ))
        
        # Sous-titre
        self.styles.add(ParagraphStyle(
            name='PG_SubTitle',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor(COLOR_PRIMARY)
        ))
        
        # Texte de corps
        self.styles.add(ParagraphStyle(
            name='PG_Body',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            textColor=colors.HexColor(COLOR_TEXT)
        ))
        
        # Liste à puces
        self.styles.add(ParagraphStyle(
            name='PG_BulletItem',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            leftIndent=15,
            spaceAfter=4,
            textColor=colors.HexColor(COLOR_TEXT)
        ))
        
        # Légende image
        self.styles.add(ParagraphStyle(
            name='PG_Caption',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor(COLOR_LIGHT)
        ))
    
    def _parse_content(self, text: str) -> List:
        """Parse le contenu et retourne des éléments PDF"""
        elements = []
        
        if not text:
            return elements
        
        lines = text.split('\n')
        paragraph_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Ligne vide
            if not stripped:
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                continue
            
            # Titres markdown
            if stripped.startswith('#### '):
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                title = clean_text(stripped[5:])
                elements.append(Paragraph(title, self.styles['PG_SubTitle']))
                continue
            
            if stripped.startswith('### '):
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                title = clean_text(stripped[4:])
                elements.append(Paragraph(title, self.styles['PG_SubTitle']))
                continue
            
            if stripped.startswith('## '):
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                title = clean_text(stripped[3:])
                elements.append(Paragraph(title, self.styles['PG_SectionTitle']))
                continue
            
            if stripped.startswith('# '):
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                title = clean_text(stripped[2:])
                elements.append(Paragraph(title, self.styles['PG_SectionTitle']))
                continue
            
            # Ligne **titre**
            if stripped.startswith('**') and stripped.endswith('**') and stripped.count('**') == 2:
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                title = clean_text(stripped[2:-2])
                elements.append(Paragraph(title, self.styles['PG_SubTitle']))
                continue
            
            # Liste à puces
            if stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                bullet = clean_text(stripped[2:])
                elements.append(Paragraph("• " + bullet, self.styles['PG_BulletItem']))
                continue
            
            # Séparateur
            if stripped in ['---', '***', '___']:
                if paragraph_lines:
                    clean = clean_text(' '.join(paragraph_lines))
                    if clean.strip():
                        elements.append(Paragraph(clean, self.styles['PG_Body']))
                    paragraph_lines = []
                elements.append(Spacer(1, 10))
                continue
            
            # Texte normal
            paragraph_lines.append(stripped)
        
        # Dernier paragraphe
        if paragraph_lines:
            clean = clean_text(' '.join(paragraph_lines))
            if clean.strip():
                elements.append(Paragraph(clean, self.styles['PG_Body']))
        
        return elements
    
    def _process_image(self, image_data: Dict, max_width: float = 2.5*cm) -> Optional[Image]:
        """Traite une image"""
        try:
            if 'data' in image_data:
                img_bytes = image_data['data']
            elif 'base64' in image_data:
                img_bytes = base64.b64decode(image_data['base64'])
            else:
                return None
            
            pil_img = PILImage.open(io.BytesIO(img_bytes))
            
            aspect = pil_img.height / pil_img.width
            width = max_width
            height = width * aspect
            
            if height > 2.5*cm:
                height = 2.5*cm
                width = height / aspect
            
            img_buffer = io.BytesIO()
            if pil_img.mode == 'RGBA':
                pil_img = pil_img.convert('RGB')
            pil_img.save(img_buffer, format='JPEG', quality=80)
            img_buffer.seek(0)
            
            return Image(img_buffer, width=width, height=height)
        except:
            return None
    
    def _create_thumbnail_grid(self, images: List[Dict]) -> List:
        """Crée une grille de vignettes"""
        elements = []
        
        valid = [img for img in images if 'data' in img or 'base64' in img]
        
        if not valid:
            for img in images[:15]:
                name = clean_text(img.get('name', 'Image')[:25])
                elements.append(Paragraph("• " + name, self.styles['PG_BulletItem']))
            return elements
        
        rows = []
        row = []
        cols = 5
        
        for img in valid[:15]:
            img_el = self._process_image(img)
            if img_el:
                name = clean_text(img.get('name', '')[:10])
                cell = Table(
                    [[img_el], [Paragraph(name, self.styles['PG_Caption'])]],
                    colWidths=[2.8*cm]
                )
                cell.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                row.append(cell)
            
            if len(row) == cols:
                rows.append(row)
                row = []
        
        if row:
            while len(row) < cols:
                row.append('')
            rows.append(row)
        
        if rows:
            grid = Table(rows, colWidths=[3*cm] * cols)
            grid.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(grid)
        
        return elements
    
    def _add_header_footer(self, canvas, doc):
        """En-tête et pied de page"""
        canvas.saveState()
        
        # Ligne accent
        canvas.setStrokeColor(colors.HexColor(COLOR_ACCENT))
        canvas.setLineWidth(2)
        canvas.line(1.5*cm, A4[1] - 1.2*cm, A4[0] - 1.5*cm, A4[1] - 1.2*cm)
        
        # Numéro page
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor(COLOR_LIGHT))
        canvas.drawCentredString(A4[0] / 2, 1*cm, str(canvas.getPageNumber()))
        
        canvas.restoreState()
    
    def generate(
        self,
        pitch: str,
        sequencer: str,
        decoupage: str,
        images: List[Dict],
        output_path: Optional[str] = None,
        title: str = "Pitch Creatif"
    ) -> str:
        """Génère le PDF complet"""
        
        if output_path is None:
            output_path = f"/tmp/pitch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # COUVERTURE
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph(clean_text(title), self.styles['PG_CoverTitle']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(datetime.now().strftime('%d/%m/%Y'), self.styles['PG_CoverSubtitle']))
        elements.append(Spacer(1, 1.5*cm))
        
        if images:
            elements.append(Paragraph("REFERENCES VISUELLES", self.styles['PG_SubTitle']))
            elements.append(Spacer(1, 0.3*cm))
            elements.extend(self._create_thumbnail_grid(images))
        
        elements.append(PageBreak())
        
        # PITCH
        elements.append(Paragraph("PITCH", self.styles['PG_SectionTitle']))
        elements.append(Spacer(1, 0.3*cm))
        if pitch:
            elements.extend(self._parse_content(pitch))
        else:
            elements.append(Paragraph("Contenu non disponible", self.styles['PG_Body']))
        
        elements.append(PageBreak())
        
        # SEQUENCIER
        elements.append(Paragraph("SEQUENCIER", self.styles['PG_SectionTitle']))
        elements.append(Spacer(1, 0.3*cm))
        if sequencer:
            elements.extend(self._parse_content(sequencer))
        else:
            elements.append(Paragraph("Contenu non disponible", self.styles['PG_Body']))
        
        elements.append(PageBreak())
        
        # DECOUPAGE
        elements.append(Paragraph("DECOUPAGE TECHNIQUE", self.styles['PG_SectionTitle']))
        elements.append(Spacer(1, 0.3*cm))
        if decoupage:
            elements.extend(self._parse_content(decoupage))
        else:
            elements.append(Paragraph("Contenu non disponible", self.styles['PG_Body']))
        
        # INDEX
        if images:
            elements.append(PageBreak())
            elements.append(Paragraph("INDEX DES IMAGES", self.styles['PG_SectionTitle']))
            elements.append(Spacer(1, 0.3*cm))
            for idx, img in enumerate(images, 1):
                name = clean_text(img.get('name', 'Sans nom'))
                elements.append(Paragraph(f"{idx:03d}. {name}", self.styles['PG_Body']))
        
        # Build
        doc.build(elements, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        return output_path
