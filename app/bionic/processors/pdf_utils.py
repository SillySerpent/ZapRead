import os
import re
import fitz  # pymupdf
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from .utils import process_text_bionic, create_temp_output_path, debug_print

def process_pdf_span(page, span, bionic_annotations):
    """
    Process a single text span in a PDF page.
    
    Args:
        page: PDF page object
        span: Text span dictionary
        bionic_annotations: List to store annotations
    """
    # Extract span information
    text = span["text"]
    if not text.strip():
        return
        
    # Extract span properties for reconstruction
    font_name = span["font"]
    font_size = span["size"]
    color = span["color"]
    bbox = span["bbox"]
    flags = span["flags"]
    
    debug_print(f"Processing text: '{text[:20]}...' with font={font_name}, size={font_size}")
    
    # Check for italic text - adjust our approach if italic
    is_italic = (flags & 2) != 0
    is_bold = (flags & 16) != 0
    
    debug_print(f"  Text style: italic={is_italic}, bold={is_bold}")
    
    # Parse the text into words while preserving spacing and punctuation
    words = []
    for match in re.finditer(r'(\s+)|([^\s]+(?:\s*[^\w\s]\s*[^\s]+)*)', text):
        if match.group(1):  # Space
            words.append((match.group(1), None))
        else:  # Word or word with punctuation
            words.append((None, match.group(2)))
    
    debug_print(f"  Parsed into {len(words)} word/space segments: {[w for _, w in words if w][:5]}")
    
    # Convert to bionic format - FIXED: Convert (space, word) format to bionic (word, is_bold) format
    bionic_words = []
    for space, word in words:
        if word:  # Only process actual words, skip spaces
            _, bold_part, regular_part = process_text_bionic(word)
            if bold_part and regular_part:
                bionic_words.append((bold_part, True))
                bionic_words.append((regular_part, False))
            elif bold_part:
                bionic_words.append((bold_part, True))
            elif regular_part:
                bionic_words.append((regular_part, False))
            # FIXED: Add single space after each word (not after bionic parts)
            if space:
                bionic_words.append((space, False))
        elif space:  # Handle standalone spaces
            bionic_words.append((space, False))
    
    # Apply the text replacement - CHANGED: Use simplified redaction approach
    apply_simplified_redaction_with_formatting(page, span, bbox, bionic_words)

def apply_simplified_redaction_with_formatting(page, span, bbox, words):
    """
    Final approach: single redaction for positioning + direct text modification for bionic formatting.
    Uses optimized direct insertion with precise character positioning.
    """
    # Reconstruct the complete text
    reconstructed_text = ""
    bold_char_positions = []
    
    # FIXED: Proper reconstruction without double spaces
    for i, (word, is_bold) in enumerate(words):
        start_pos = len(reconstructed_text)
        reconstructed_text += word
        if is_bold:
            for j in range(start_pos, start_pos + len(word)):
                bold_char_positions.append(j)
        # No automatic space addition - spaces are already in the words list
    
    # Apply single redaction for reliable positioning - FIXED: Proper bbox handling
    if isinstance(bbox, (list, tuple)):
        bbox_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
    elif hasattr(bbox, 'x0'):  # Already a Rect-like object
        bbox_rect = bbox
    else:
        bbox_rect = fitz.Rect(bbox)
    
    # FIXED: Use white fill redaction to completely remove original text
    page.add_redact_annot(bbox_rect, "", fill=(1, 1, 1))  # White fill, no text
    page.apply_redactions()
    
    # Get font object for accurate measurements
    fontname = span.get('font', 'Helvetica')
    font_size = span.get('size', 12)
    
    try:
        # Try to get the font object for accurate measurements
        font = fitz.Font(fontname)
    except Exception:
        # Fallback to default font
        font = fitz.Font("helv")
    
    # Use exact baseline Y from original bbox
    baseline_y = bbox_rect.y0 + (bbox_rect.height * 0.8)
    
    # FIXED: Use proper font-based positioning instead of uniform character width
    current_x = bbox_rect.x0
    
    for word_text, is_bold in words:
        # Insert each word/space with proper font
        if is_bold:
            page.insert_text((current_x, baseline_y), word_text, fontname="Helvetica-Bold", fontsize=font_size)
        else:
            page.insert_text((current_x, baseline_y), word_text, fontname=fontname, fontsize=font_size)
        
        # FIXED: Use actual font metrics for accurate character positioning
        try:
            # Calculate actual text width using font metrics
            if is_bold:
                # For bold text, try to get bold font or estimate 10% wider
                try:
                    bold_font = fitz.Font("Helvetica-Bold")
                    text_width = bold_font.text_length(word_text, fontsize=font_size)
                except Exception:
                    # Fallback: estimate bold as 10% wider than regular
                    text_width = font.text_length(word_text, fontsize=font_size) * 1.1
            else:
                text_width = font.text_length(word_text, fontsize=font_size)
            
            current_x += text_width
            
        except Exception as e:
            debug_print(f"Font metrics failed, using fallback: {e}")
            # Fallback to estimated width
            fallback_width = len(word_text) * font_size * 0.6
            current_x += fallback_width

def apply_redaction_approach(page, bbox, replaced_text, font_name, font_size, replacement_positions, bionic_annotations):
    """Apply redaction approach for standard text - DEPRECATED: Not used anymore due to highlighting issues."""
    debug_print(f"  WARNING: Using deprecated redaction approach - highlighting may fail")
    
    page.add_redact_annot(
        fitz.Rect(bbox),
        text=replaced_text,
        fontname=font_name,
        fontsize=font_size
    )
    
    # Apply redactions
    page.apply_redactions()
    
    # Now add highlighting for the bold parts
    for start_pos, end_pos in replacement_positions:
        highlight_text = replaced_text[start_pos:end_pos]
        
        # Find this text on the page with appropriate context
        rect = fitz.Rect(bbox)
        expanded_rect = fitz.Rect(rect.x0 - 5, rect.y0 - 5, rect.x1 + 5, rect.y1 + 5)
        
        try:
            instances = page.search_for(highlight_text, clip=expanded_rect)
            
            # Add highlight annotations for each instance
            for inst in instances:
                highlight = page.add_highlight_annot(inst)
                highlight.set_colors(stroke=(0.3, 0.3, 0.3))
                highlight.update()
                bionic_annotations.append(highlight)
        except Exception as e:
            debug_print(f"Error highlighting text: {e}")

def get_render_mode_for_text(is_bold, is_italic, is_bionic_bold):
    """Get appropriate render mode for text styling."""
    if is_bold and is_italic:
        return 2  # Fill + stroke helps with bold
    elif is_bold:
        return 2  # Fill + stroke for bold effect
    elif is_italic:
        return 0  # Normal rendering for italic
    else:
        # Normal text - bold part should be bold
        return 2 if is_bionic_bold else 0

def get_font_for_style(font_name, is_bold, is_italic, is_bionic_bold):
    """Get appropriate font name for text styling."""
    if is_bold and is_italic:
        if 'BoldOblique' in font_name or 'BoldItalic' in font_name:
            return font_name
        else:
            actual_font = font_name.replace('Oblique', 'BoldOblique').replace('Italic', 'BoldItalic')
            if 'Bold' not in actual_font:
                actual_font = actual_font.replace('Oblique', '').replace('Italic', '')
                actual_font = actual_font + '-BoldOblique'
            return actual_font
    elif is_bold:
        if 'Bold' in font_name:
            return font_name
        else:
            return font_name + '-Bold' if '-' not in font_name else font_name
    elif is_italic:
        if 'Oblique' in font_name or 'Italic' in font_name:
            return font_name
        else:
            return font_name + '-Oblique' if '-' not in font_name else font_name
    else:
        # Normal text - bold part should be bold
        if is_bionic_bold and 'Bold' not in font_name:
            return font_name + '-Bold' if '-' not in font_name else font_name
        return font_name

def insert_fallback_text(page, x, y, word, font_name, font_size, color):
    """Insert text as fallback when styling fails."""
    try:
        page.insert_text(
            (x, y),
            word,
            fontname=font_name,
            fontsize=font_size,
            color=color
        )
        
        word_width = len(word) * font_size * 0.75
        return word_width
    except Exception as e2:
        debug_print(f"Fallback text insertion failed: {e2}")
        return 0

def draw_image_on_canvas(canvas_obj, img_info, page_height):
    """Draw an image on the ReportLab canvas."""
    img_bytes = img_info["bytes"]
    bbox_pdf = img_info["bbox_pdf"]

    rl_img_x = bbox_pdf.x0
    rl_img_y = page_height - bbox_pdf.y1 
    rl_img_width = bbox_pdf.width
    rl_img_height = bbox_pdf.height
    
    try:
        image_reader = ImageReader(io.BytesIO(img_bytes))
        canvas_obj.drawImage(image_reader, rl_img_x, rl_img_y, 
                            width=rl_img_width, height=rl_img_height, mask='auto')
    except Exception as e:
        print(f"Error drawing image: {e}. Image bbox: {bbox_pdf}")

def draw_text_span_on_canvas(canvas_obj, span_info, page_height):
    """Draw a text span on the ReportLab canvas with bionic formatting."""
    text = span_info["text"]
    font_size = span_info["font_size"]
    flags = span_info["flags"]
    origin_pdf = span_info["origin_pdf"]

    rl_x_start = origin_pdf.x
    rl_y_baseline = page_height - origin_pdf.y
    
    current_x = rl_x_start

    words = re.findall(r'\S+|\s+', text)
    
    for i, word in enumerate(words):
        if not word.strip(): 
            space_width = canvas_obj.stringWidth(word, "Helvetica", font_size) if word else 0
            current_x += space_width
            continue

        clean_word, bold_part, regular_part = process_text_bionic(word)

        if bold_part:
            canvas_obj.setFont("Helvetica-Bold", font_size)
            canvas_obj.drawString(current_x, rl_y_baseline, bold_part)
            current_x += canvas_obj.stringWidth(bold_part, "Helvetica-Bold", font_size)
        
        if regular_part:
            is_bold_flag = flags & 16
            is_italic_flag = flags & 2
            
            font_rl = "Helvetica"
            if is_bold_flag and is_italic_flag:
                font_rl = "Helvetica-BoldOblique"
            elif is_bold_flag:
                font_rl = "Helvetica-Bold"
            elif is_italic_flag:
                font_rl = "Helvetica-Oblique"
            
            canvas_obj.setFont(font_rl, font_size)
            canvas_obj.drawString(current_x, rl_y_baseline, regular_part)
            current_x += canvas_obj.stringWidth(regular_part, font_rl, font_size)
        
        # Add spacing between words
        if i < len(words) - 1 and not words[i+1].isspace():
            current_x += canvas_obj.stringWidth(" ", "Helvetica", font_size) * 0.3 