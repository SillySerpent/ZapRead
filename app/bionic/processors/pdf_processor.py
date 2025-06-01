"""
PDF Processor for Bionic Reading

This module handles the processing of PDF files for bionic reading format.
Uses PyMuPDF (fitz) for PDF manipulation and ReportLab for canvas operations.
"""

import os
import sys
import traceback
import fitz  # pymupdf
import tempfile
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .utils import process_text_bionic, detect_file_type, create_output_path, debug_print
from .pdf_utils import (
    process_pdf_span, 
    draw_image_on_canvas, 
    draw_text_span_on_canvas
)

def create_bionic_pdf_direct(input_path):
    """
    Create a bionic reading PDF by directly modifying the original PDF.
    
    Args:
        input_path (str): Path to input PDF file
        
    Returns:
        str: Path to the output bionic PDF file
    """
    try:
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Create output path
        output_path = create_output_path(input_path, 'pdf', '_bionic')
        debug_print(f"Processing PDF: {input_path} -> {output_path}")
        
        # Counter for tracking processed spans
        total_spans_processed = 0
        total_spans_found = 0
        bionic_annotations = []
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            debug_print(f"\nProcessing page {page_num + 1}")
            
            # Get all text spans on the page
            text_dict = page.get_text("dict")
            
            # Process each block
            for block in text_dict["blocks"]:
                if "lines" not in block:
                    continue
                    
                # Process each line in the block
                for line in block["lines"]:
                    # Process each span in the line
                    for span in line["spans"]:
                        total_spans_found += 1
                        
                        # Skip empty or whitespace-only spans
                        if not span["text"].strip():
                            continue
                            
                        try:
                            process_pdf_span(page, span, bionic_annotations)
                            total_spans_processed += 1
                        except Exception as e:
                            debug_print(f"Error processing span: {e}")
                            continue
        
        debug_print(f"\nTotal spans found: {total_spans_found}")
        debug_print(f"Total spans processed: {total_spans_processed}")
        debug_print(f"Total bionic annotations: {len(bionic_annotations)}")
        
        # Save the modified PDF
        doc.save(output_path)
        doc.close()
        
        debug_print(f"Successfully created bionic PDF: {output_path}")
        return output_path
        
    except Exception as e:
        debug_print(f"Error in create_bionic_pdf_direct: {e}")
        debug_print(f"Full traceback: {traceback.format_exc()}")
        return None

def create_bionic_pdf_reportlab(input_path):
    """
    Create a bionic reading PDF using ReportLab for text rendering.
    
    Args:
        input_path (str): Path to input PDF file
        
    Returns:
        str: Path to the output bionic PDF file
    """
    try:
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Create output path
        output_path = create_output_path(input_path, 'pdf', '_bionic_rl')
        debug_print(f"Processing PDF with ReportLab: {input_path} -> {output_path}")
        
        # Create a new PDF with ReportLab
        c = canvas.Canvas(output_path, pagesize=letter)
        page_width, page_height = letter
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            debug_print(f"\nProcessing page {page_num + 1} with ReportLab")
            
            # Extract images
            image_list = page.get_images(full=True)
            images_info = []
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_bytes = pix.tobytes("png")
                        
                        # Get image bounding box
                        img_dict = doc.extract_image(xref)
                        img_bbox = page.get_image_rects(xref)[0] if page.get_image_rects(xref) else fitz.Rect(0, 0, 100, 100)
                        
                        images_info.append({
                            "bytes": img_bytes,
                            "bbox_pdf": img_bbox
                        })
                    
                    pix = None
                except Exception as e:
                    debug_print(f"Error extracting image {img_index}: {e}")
                    continue
            
            # Extract text with positioning
            text_dict = page.get_text("dict")
            text_spans = []
            
            for block in text_dict["blocks"]:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            text_spans.append({
                                "text": span["text"],
                                "font_size": span["size"],
                                "flags": span["flags"],
                                "origin_pdf": fitz.Point(span["bbox"][0], span["bbox"][1] + span["size"])
                            })
            
            # Draw images on canvas
            for img_info in images_info:
                draw_image_on_canvas(c, img_info, page_height)
            
            # Draw text spans on canvas
            for span_info in text_spans:
                draw_text_span_on_canvas(c, span_info, page_height)
            
            # Finish the page
            c.showPage()
        
        # Save the canvas
        c.save()
        doc.close()
        
        debug_print(f"Successfully created bionic PDF with ReportLab: {output_path}")
        return output_path
        
    except Exception as e:
        debug_print(f"Error in create_bionic_pdf_reportlab: {e}")
        debug_print(f"Full traceback: {traceback.format_exc()}")
        return None

def process_pdf_file(input_path):
    """
    Main entry point for processing PDF files.
    
    Args:
        input_path (str): Path to input PDF file
        
    Returns:
        dict: Processing result with success status and output path
    """
    try:
        # First, try the direct PDF modification approach
        debug_print("Attempting direct PDF modification...")
        output_path = create_bionic_pdf_direct(input_path)
        
        if output_path and os.path.exists(output_path):
            return {
                'success': True,
                'output_path': output_path,
                'file_type': 'pdf',
                'method': 'direct'
            }
        
        # If direct approach fails, try ReportLab approach
        debug_print("Direct approach failed, trying ReportLab approach...")
        output_path = create_bionic_pdf_reportlab(input_path)
        
        if output_path and os.path.exists(output_path):
            return {
                'success': True,
                'output_path': output_path,
                'file_type': 'pdf',
                'method': 'reportlab'
            }
        
        # If both approaches fail
        return {
            'success': False,
            'error': 'Both PDF processing methods failed',
            'file_type': 'pdf'
        }
        
    except Exception as e:
        debug_print(f"Error in process_pdf_file: {e}")
        return {
            'success': False,
            'error': str(e),
            'file_type': 'pdf'
        }

# Backward compatibility functions
def create_bionic_pdf(input_path):
    """Backward compatibility function."""
    return create_bionic_pdf_direct(input_path)

def create_bionic_reading_pdf(input_path):
    """Backward compatibility function."""
    result = process_pdf_file(input_path)
    return result.get('output_path') if result.get('success') else None 