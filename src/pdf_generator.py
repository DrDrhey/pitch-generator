"""
Module de génération de PDF stylisés avec vignettes
"""

import os
import io
import base64
from datetime import datetime
from typing import List, Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage


class PDFGenerator:
    """Génère des PDF stylisés avec vignettes d'images"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a1a')
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            fontName='Helvetica-Oblique',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#666666')
        ))
        
        # Style section
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#e63946'),
            borderPadding=5
        ))
        
        # Style sous-section
        self.styles.add(ParagraphStyle(
            name='SubSection',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#333333')
        ))
        
        # Style body
        self.styles.add(ParagraphStyle(
            name='BodyText',
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            textColor=colors.HexColor('#333333')
        ))
        
        # Style note
        self.styles.add(ParagraphStyle(
            name='Note',
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=14,
            leftIndent=20,
            rightIndent=20,
            spaceBefore=10,
            spaceAfter=10,
            textColor=colors.HexColor('#666666'),
            backColor=colors.HexColor('#f5f5f5'),
            borderPadding=10
        ))
        
        # Style image caption
        self.styles.add(ParagraphStyle(
            name='ImageCaption',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#888888')
        ))
        
        # Style table header
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.white
        ))
        
        # Style table cell
        self.styles.add(ParagraphStyle(
            name='TableCell',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#333333')
        ))
    
    def _create_header(self, canvas, doc):
        """Crée l'en-tête des pages"""
        canvas.saveState()
        
        # Ligne décorative
        canvas.setStrokeColor(colors.HexColor('#e63946'))
        canvas.setLineWidth(2)
        canvas.line(1.5*cm, A4[1] - 1.5*cm, A4[0] - 1.5*cm, A4[1] - 1.5*cm)
        
        # Date
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        date_str = datetime.now().strftime('%d/%m/%Y')
        canvas.drawRightString(A4[0] - 1.5*cm, A4[1] - 1.2*cm, date_str)
        
        canvas.restoreState()
    
    def _create_footer(self, canvas, doc):
        """Crée le pied de page"""
        canvas.saveState()
        
        # Numéro de page
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#999999'))
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(A4[0] / 2, 1*cm, f"— {page_num} —")
        
        # Ligne décorative
        canvas.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas.setLineWidth(0.5)
        canvas.line(1.5*cm, 1.5*cm, A4[0] - 1.5*cm, 1.5*cm)
        
        canvas.restoreState()
    
    def _process_image(self, image_data: Dict, max_width: float = 4*cm) -> Optional[Image]:
        """Traite une image pour l'intégrer au PDF"""
        try:
            if 'data' in image_data:
                img_bytes = image_data['data']
            elif 'base64' in image_data:
                img_bytes = base64.b64decode(image_data['base64'])
            else:
                return None
            
            # Charger et redimensionner
            pil_img = PILImage.open(io.BytesIO(img_bytes))
            
            # Calculer les dimensions
            aspect = pil_img.height / pil_img.width
            width = max_width
            height = width * aspect
            
            # Limiter la hauteur
            max_height = 4*cm
            if height > max_height:
                height = max_height
                width = height / aspect
            
            # Convertir pour ReportLab
            img_buffer = io.BytesIO()
            if pil_img.mode == 'RGBA':
                pil_img = pil_img.convert('RGB')
            pil_img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            print(f"Erreur traitement image: {e}")
            return None
    
    def _create_thumbnail_grid(self, images: List[Dict], cols: int = 5) -> List:
        """Crée une grille de vignettes"""
        elements = []
        
        # Filtrer les images avec données
        valid_images = [img for img in images if 'data' in img or 'base64' in img]
        
        if not valid_images:
            # Si pas de données d'images, lister les noms
            elements.append(Paragraph("Images de référence :", self.styles['SubSection']))
            for img in images[:30]:
                elements.append(Paragraph(f"• {img.get('name', 'Image')}", self.styles['BodyText']))
            return elements
        
        rows = []
        current_row = []
        
        for idx, img in enumerate(valid_images[:20]):  # Limiter à 20 vignettes
            img_element = self._process_image(img, max_width=3*cm)
            
            if img_element:
                # Créer une mini-table pour image + légende
                cell_content = [
                    [img_element],
                    [Paragraph(img.get('name', '')[:15], self.styles['ImageCaption'])]
                ]
                cell_table = Table(cell_content, colWidths=[3.2*cm])
                cell_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                current_row.append(cell_table)
            else:
                current_row.append(Paragraph(img.get('name', '')[:15], self.styles['ImageCaption']))
            
            if len(current_row) == cols:
                rows.append(current_row)
                current_row = []
        
        if current_row:
            # Compléter la dernière ligne
            while len(current_row) < cols:
                current_row.append('')
            rows.append(current_row)
        
        if rows:
            grid = Table(rows, colWidths=[3.5*cm] * cols)
            grid.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(grid)
        
        return elements
    
    def _parse_markdown_to_paragraphs(self, text: str) -> List:
        """Convertit le markdown en éléments PDF"""
        elements = []
        
        lines = text.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                continue
            
            # Titres
            if line.startswith('# '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                elements.append(Paragraph(line[2:], self.styles['MainTitle']))
            
            elif line.startswith('## '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                elements.append(Paragraph(line[3:], self.styles['SectionTitle']))
            
            elif line.startswith('### '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                elements.append(Paragraph(line[4:], self.styles['SubSection']))
            
            elif line.startswith('**') and line.endswith('**'):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                elements.append(Paragraph(f"<b>{line[2:-2]}</b>", self.styles['SubSection']))
            
            elif line.startswith('- ') or line.startswith('• '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                bullet_text = line[2:]
                elements.append(Paragraph(f"• {bullet_text}", self.styles['BodyText']))
            
            elif line.startswith('---'):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
                    current_paragraph = []
                elements.append(Spacer(1, 15))
            
            else:
                # Nettoyer le markdown inline
                line = line.replace('**', '<b>').replace('__', '<b>')
                line = line.replace('*', '<i>').replace('_', '<i>')
                current_paragraph.append(line)
        
        if current_paragraph:
            elements.append(Paragraph(' '.join(current_paragraph), self.styles['BodyText']))
        
        return elements
    
    def generate(
        self,
        pitch: str,
        sequencer: str,
        decoupage: str,
        images: List[Dict],
        output_path: Optional[str] = None,
        title: str = "Pitch Créatif"
    ) -> str:
        """
        Génère le PDF complet
        
        Args:
            pitch: Texte du pitch
            sequencer: Texte du séquencier
            decoupage: Texte du découpage technique
            images: Liste des images avec métadonnées
            output_path: Chemin de sortie (optionnel)
            title: Titre du document
        
        Returns:
            Chemin du fichier PDF généré
        """
        if output_path is None:
            output_path = f"/tmp/pitch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Créer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )
        
        elements = []
        
        # Page de titre
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph(title, self.styles['MainTitle']))
        elements.append(Paragraph(
            datetime.now().strftime('%B %Y'),
            self.styles['Subtitle']
        ))
        elements.append(Spacer(1, 2*cm))
        
        # Moodboard miniature
        if images:
            elements.append(Paragraph("MOODBOARD", self.styles['SectionTitle']))
            elements.extend(self._create_thumbnail_grid(images))
        
        elements.append(PageBreak())
        
        # Section PITCH
        elements.append(Paragraph("PITCH", self.styles['SectionTitle']))
        elements.append(Spacer(1, 0.5*cm))
        if pitch:
            elements.extend(self._parse_markdown_to_paragraphs(pitch))
        
        elements.append(PageBreak())
        
        # Section SÉQUENCIER
        elements.append(Paragraph("SÉQUENCIER", self.styles['SectionTitle']))
        elements.append(Spacer(1, 0.5*cm))
        if sequencer:
            elements.extend(self._parse_markdown_to_paragraphs(sequencer))
        
        elements.append(PageBreak())
        
        # Section DÉCOUPAGE
        elements.append(Paragraph("DÉCOUPAGE TECHNIQUE", self.styles['SectionTitle']))
        elements.append(Spacer(1, 0.5*cm))
        if decoupage:
            elements.extend(self._parse_markdown_to_paragraphs(decoupage))
        
        # Index des images
        if images:
            elements.append(PageBreak())
            elements.append(Paragraph("INDEX DES IMAGES", self.styles['SectionTitle']))
            elements.append(Spacer(1, 0.5*cm))
            
            for idx, img in enumerate(images, 1):
                elements.append(Paragraph(
                    f"{idx:03d}. {img.get('name', 'Sans nom')}",
                    self.styles['BodyText']
                ))
        
        # Construire le PDF
        doc.build(
            elements,
            onFirstPage=lambda c, d: (self._create_header(c, d), self._create_footer(c, d)),
            onLaterPages=lambda c, d: (self._create_header(c, d), self._create_footer(c, d))
        )
        
        return output_path
