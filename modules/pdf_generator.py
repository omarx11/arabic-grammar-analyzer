"""
PDF Report Generation Module
Creates downloadable PDF reports of analysis results
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import io
import os

# Register Arabic font
try:
    font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Amiri-Regular.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Arabic', font_path))
        ARABIC_FONT = 'Arabic'
    else:
        ARABIC_FONT = 'Helvetica'
except:
    ARABIC_FONT = 'Helvetica'

def format_arabic_text(text):
    """
    Format Arabic text for proper RTL display in PDF
    """
    try:
        reshaped_text = reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except:
        return text

def generate_pdf_report(student_name, text, analysis_result):
    """
    Generate a PDF report of the analysis
    
    Args:
        student_name: Name of the student
        text: Original text analyzed
        analysis_result: Analysis data from grammar checker
        
    Returns:
        BytesIO: PDF file in memory
    """
    buffer = io.BytesIO()
    
    # Create PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=ARABIC_FONT,
        alignment=TA_CENTER,
        fontSize=20,
        textColor=colors.HexColor('#2563eb')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=ARABIC_FONT,
        alignment=TA_RIGHT,
        fontSize=14,
        textColor=colors.HexColor('#1e293b')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=ARABIC_FONT,
        alignment=TA_RIGHT,
        fontSize=11
    )
    
    # Title
    story.append(Paragraph("Arabic Grammar Analysis Report", title_style))
    story.append(Paragraph(format_arabic_text("تقرير تحليل النحو العربي"), title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Metadata
    metadata = [
        [format_arabic_text("اسم الطالب:"), format_arabic_text(student_name)],
        [format_arabic_text("التاريخ:"), datetime.now().strftime('%Y-%m-%d %H:%M')],
        [format_arabic_text("عدد الكلمات:"), str(analysis_result.get('word_count', 0))],
        [format_arabic_text("عدد الجمل:"), str(analysis_result.get('sentence_count', 0))],
        [format_arabic_text("الدرجة:"), f"{analysis_result.get('score', 0)}/100"],
        [format_arabic_text("الأخطاء:"), str(len(analysis_result.get('errors', [])))],
    ]
    
    metadata_table = Table(metadata, colWidths=[2.5*inch, 3.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    story.append(metadata_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Original Text
    story.append(Paragraph(format_arabic_text("النصّ الأصلي"), heading_style))
    story.append(Spacer(1, 0.1 * inch))
    formatted_text = format_arabic_text(text[:500] + ('...' if len(text) > 500 else ''))
    story.append(Paragraph(formatted_text, normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Errors Section
    if analysis_result.get('errors'):
        story.append(Paragraph(format_arabic_text("الأخطاء المُكتشَفة"), heading_style))
        story.append(Spacer(1, 0.1 * inch))
        
        error_data = [["#", format_arabic_text("النوع"), format_arabic_text("الكلمة"), format_arabic_text("التصحيح"), format_arabic_text("الشرح")]]
        for idx, error in enumerate(analysis_result['errors'][:10], 1):  # Limit to 10 errors
            error_data.append([
                str(idx),
                format_arabic_text(error.get('type', '-')),
                format_arabic_text(error.get('word', '-')),
                format_arabic_text(error.get('correction', '-')),
                format_arabic_text(error.get('explanation', error.get('message', '-'))[:80])
            ])
        
        error_table = Table(error_data, colWidths=[0.5*inch, 1*inch, 1.2*inch, 1.2*inch, 2.5*inch])
        error_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fee2e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(error_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Overall Feedback
    if analysis_result.get('overall_feedback'):
        story.append(Paragraph(format_arabic_text("الملاحظات العامّة"), heading_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(format_arabic_text(analysis_result['overall_feedback']), normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer
