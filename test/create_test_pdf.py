from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def create_test_pdf(output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    # Create content elements
    elements = []
    
    # Title
    elements.append(Paragraph("Test PDF Document with Formatting", title_style))
    elements.append(Spacer(1, 12))
    
    # Introduction
    elements.append(Paragraph("This is a test PDF document created to demonstrate various formatting features including headings, paragraphs, and text formatting.", normal_style))
    elements.append(Spacer(1, 12))
    
    # Heading
    elements.append(Paragraph("Section 1: Different Text Formats", heading_style))
    elements.append(Spacer(1, 6))
    
    # Regular paragraph
    elements.append(Paragraph("This is a regular paragraph with standard text formatting. It should be preserved in the bionic reading version.", normal_style))
    elements.append(Spacer(1, 6))
    
    # Bold and italic text
    elements.append(Paragraph("This contains <b>bold text</b> and <i>italic text</i> and <b><i>both bold and italic</i></b> which should be preserved.", normal_style))
    elements.append(Spacer(1, 12))
    
    # Another heading
    elements.append(Paragraph("Section 2: Structure and Spacing", heading_style))
    elements.append(Spacer(1, 6))
    
    # Multiple paragraphs
    elements.append(Paragraph("This is the first paragraph in a section. It demonstrates paragraph spacing and structure preservation.", normal_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("This is a second paragraph with different content. The spacing between paragraphs should be maintained in the bionic reading version.", normal_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("This third paragraph has some <b>important words</b> that should be highlighted. The bionic reading algorithm should still work correctly with this formatting.", normal_style))
    elements.append(Spacer(1, 12))
    
    # Conclusion
    elements.append(Paragraph("Conclusion", heading_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("This test PDF demonstrates various formatting features that should be preserved during bionic reading conversion. The structure, headings, paragraph spacing, and text formatting should all be maintained.", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    return output_path

if __name__ == "__main__":
    output_file = "test_formatted.pdf"
    create_test_pdf(output_file)
    print(f"Test PDF created successfully: {output_file}") 