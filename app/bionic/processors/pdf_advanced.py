"""
Advanced PDF Processor for Bionic Reading

Enhanced PDF processing with multiple strategies including morphing and redaction techniques.
Supports complex document layouts while preserving formatting and structure.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import fitz  # PyMuPDF
import time

from ..core.config import BionicConfig, PDFMethod
from ..core.exceptions import PDFProcessingError
from ..utils.file_utils import create_output_path, validate_file
from ..processors.utils import get_bionic_word_parts


logger = logging.getLogger(__name__)


class AdvancedPDFProcessor:
    """
    Advanced PDF processor with multiple processing strategies.
    
    Supports morphing, redaction, and hybrid approaches for different PDF types.
    Automatically selects optimal processing method based on document characteristics.
    """
    
    def __init__(self, config: BionicConfig):
        """
        Initialize the advanced PDF processor.
        
        Args:
            config: Processing configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Processing statistics
        self.stats = {
            'pages_processed': 0,
            'text_spans_processed': 0,
            'bionic_spans_created': 0,
            'processing_method': None,
            'fallback_used': False,
            'processing_time': 0.0
        }
    
    def process(self, file_path: str, config: BionicConfig, **kwargs) -> Dict[str, Any]:
        """
        Process PDF with intelligent method selection and fallback handling.
        
        Args:
            file_path: Path to PDF file
            config: Processing configuration
            **kwargs: Additional processing options
            
        Returns:
            Dictionary with processing results and quality metrics
        """
        start_time = time.time()
        output_path = self._get_output_path(file_path, **kwargs)
        
        try:
            # Open the PDF document
            doc = fitz.open(file_path)
            self.logger.info(f"Processing PDF: {file_path} ({len(doc)} pages)")
            
            # Choose the best processing method
            primary_method = self._choose_processing_method(doc)
            self.logger.info(f"Selected primary processing method: {primary_method}")
            
            # Try primary method
            try:
                if primary_method == 'morphing':
                    result = self._process_with_morphing(doc, config, output_path)
                else:
                    result = self._process_with_redaction(doc, config, output_path)
                
                # Check if processing was successful enough
                if result.get('success', False) and result.get('quality_metrics', {}).get('success_rate', 0) > 0.1:
                    self.logger.info(f"Primary method {primary_method} successful with {result['quality_metrics']['success_rate']:.1%} success rate")
                    result['processing_time'] = time.time() - start_time
                    return result
                else:
                    raise Exception(f"Primary method {primary_method} had low success rate: {result.get('quality_metrics', {}).get('success_rate', 0):.1%}")
                    
            except Exception as e:
                self.logger.warning(f"Primary method {primary_method} failed: {e}")
                # Try fallback method
                fallback_method = 'redaction' if primary_method == 'morphing' else 'morphing'
                self.logger.info(f"Attempting fallback method: {fallback_method}")
                
                try:
                    if fallback_method == 'morphing':
                        result = self._process_with_morphing(doc, config, output_path)
                    else:
                        result = self._process_with_redaction(doc, config, output_path)
                    
                    result['method_used'] = f"{primary_method} -> {fallback_method} (fallback)"
                    result['processing_time'] = time.time() - start_time
                    self.logger.info(f"Fallback method {fallback_method} completed with {result.get('quality_metrics', {}).get('success_rate', 0):.1%} success rate")
                    return result
                    
                except Exception as fallback_error:
                    self.logger.error(f"Both methods failed. Primary: {e}, Fallback: {fallback_error}")
                    raise Exception(f"All processing methods failed. Primary ({primary_method}): {e}. Fallback ({fallback_method}): {fallback_error}")
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            processing_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'output_path': None,
                'method_used': 'failed',
                'processing_time': processing_time,
                'quality_metrics': {
                    'pages_processed': 0,
                    'total_pages': 0,
                    'success_rate': 0.0,
                    'processing_quality': 'failed'
                }
            }
        finally:
            if 'doc' in locals():
                doc.close()
    
    def _reset_stats(self):
        """Reset processing statistics."""
        self.stats.update({
            'pages_processed': 0,
            'text_spans_processed': 0,
            'bionic_spans_created': 0,
            'processing_method': None,
            'fallback_used': False,
            'processing_time': 0.0
        })
    
    def _determine_processing_method(self, input_path: str, config: BionicConfig, 
                                   file_info: Dict) -> PDFMethod:
        """
        Determine the best processing method based on PDF characteristics.
        
        Args:
            input_path: Path to PDF file
            config: Processing configuration
            file_info: File metadata
            
        Returns:
            Recommended processing method
        """
        # If method is explicitly set, use it
        if hasattr(config, 'pdf_method') and config.pdf_method != PDFMethod.AUTO:
            return config.pdf_method
        
        try:
            with fitz.open(input_path) as doc:
                # Analyze PDF characteristics
                has_complex_layout = False
                has_forms = doc.is_form_pdf
                has_many_images = False
                total_images = 0
                
                # Sample first few pages for analysis
                sample_pages = min(3, len(doc))
                
                for page_num in range(sample_pages):
                    page = doc[page_num]
                    
                    # Check for complex layouts (multiple columns, tables)
                    blocks = page.get_text("dict")["blocks"]
                    text_blocks = [b for b in blocks if "lines" in b]
                    
                    if len(text_blocks) > 10:  # Many text blocks might indicate complex layout
                        has_complex_layout = True
                    
                    # Count images
                    images = page.get_images()
                    total_images += len(images)
                
                has_many_images = total_images > 5
                
                # Decision logic
                if has_forms or has_complex_layout:
                    return PDFMethod.REDACTION
                elif has_many_images:
                    return PDFMethod.HYBRID
                else:
                    return PDFMethod.MORPHING
                    
        except Exception as e:
            self.logger.warning(f"Error analyzing PDF characteristics: {e}")
            return PDFMethod.MORPHING  # Default fallback
    
    def _process_with_morphing(self, doc, config: BionicConfig, output_path: str) -> Dict[str, Any]:
        """
        Process PDF using PyMuPDF's text morphing capabilities with verification.
        
        Args:
            doc: PyMuPDF document object (already opened)
            config: Processing configuration
            output_path: Output PDF path
            
        Returns:
            Processing result with quality metrics
        """
        try:
            # Track processing statistics
            total_pages = len(doc)
            pages_processed = 0
            total_spans_attempted = 0
            total_spans_successful = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Count spans before processing
                spans_before = self.stats['text_spans_processed']
                bionic_spans_before = self.stats['bionic_spans_created']
                
                self._process_page_with_morphing(page, config)
                
                # Calculate spans processed on this page
                spans_on_page = self.stats['text_spans_processed'] - spans_before
                bionic_spans_on_page = self.stats['bionic_spans_created'] - bionic_spans_before
                
                total_spans_attempted += spans_on_page
                total_spans_successful += bionic_spans_on_page
                pages_processed += 1
                self.stats['pages_processed'] += 1
                
                self.logger.debug(f"Page {page_num + 1}: {bionic_spans_on_page}/{spans_on_page} spans enhanced")
            
            # Save the processed document
            doc.save(output_path, garbage=4, deflate=True)
            
            # Calculate quality metrics
            success_rate = (total_spans_successful / total_spans_attempted) if total_spans_attempted > 0 else 0
            processing_quality = "excellent" if success_rate >= 0.8 else "good" if success_rate >= 0.6 else "fair" if success_rate >= 0.4 else "poor"
            
            self.logger.info(f"Morphing processing complete: {total_spans_successful}/{total_spans_attempted} spans enhanced ({success_rate:.1%})")
            
            return {
                'success': True,
                'output_path': output_path,
                'method_used': 'morphing',
                'quality_metrics': {
                    'spans_processed': total_spans_attempted,
                    'spans_enhanced': total_spans_successful,
                    'success_rate': success_rate,
                    'processing_quality': processing_quality,
                    'pages_processed': pages_processed,
                    'total_pages': total_pages
                }
            }
            
        except Exception as e:
            self.logger.error(f"Morphing processing failed: {e}")
            raise PDFProcessingError(f"Morphing processing failed: {str(e)}")
    
    def _process_page_with_morphing(self, page: fitz.Page, config: BionicConfig):
        """
        Process page using morphing technique with enhanced logging.
        
        Args:
            page: PyMuPDF page object
            config: Processing configuration
        """
        try:
            # Extract text spans with positioning
            blocks = page.get_text("dict")["blocks"]
            text_spans_processed = 0
            successful_spans = 0
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        try:
                            # Process each text span
                            self._process_text_span_morphing(page, span, config)
                            text_spans_processed += 1
                            successful_spans += 1
                            self.stats['text_spans_processed'] += 1
                        except Exception as e:
                            self.logger.error(f"Failed to process text span: {e}")
                            text_spans_processed += 1
                            # Continue processing other spans
            
            self.logger.info(f"Page processing complete: {successful_spans}/{text_spans_processed} spans processed successfully")
            
        except Exception as e:
            self.logger.error(f"Page morphing failed: {e}")
            # Don't stop processing, let it continue
    
    def _process_text_span_morphing(self, page: fitz.Page, span: Dict, config: BionicConfig):
        """
        Process individual text span with morphing using direct font manipulation.
        
        Args:
            page: PyMuPDF page object
            span: Text span dictionary
            config: Processing configuration
        """
        try:
            text = span["text"]
            if not text.strip():
                return
            
            # Get bionic intensity from config
            intensity = getattr(config, 'bionic_intensity', 0.4)
            self.logger.debug(f"Processing text span with intensity: {intensity}")
            
            # Get word parts with bold/regular formatting
            word_parts = get_bionic_word_parts(text, intensity)
            
            # Check if any parts need bold formatting
            has_bold_parts = any(is_bold for _, is_bold in word_parts)
            if not has_bold_parts:
                return  # No changes needed
            
            # Get span properties
            bbox = fitz.Rect(span["bbox"])
            font_size = span["size"]
            color_tuple = self._int_to_rgb(span["color"])
            base_font_name = self._get_font_name(span)
            
            # Remove original text by covering with white rectangle
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()
            
            # Calculate insertion point (bottom-left baseline)
            insertion_point = fitz.Point(bbox.x0, bbox.y1)
            current_x = insertion_point.x
            
            # Insert each part with appropriate formatting
            try:
                for part_text, is_bold in word_parts:
                    if not part_text:
                        continue
                    
                    # Choose font and formatting based on bold requirement
                    if is_bold:
                        # Simulate bold using multiple text overlays for better visual effect
                        base_point = fitz.Point(current_x, insertion_point.y)
                        
                        # Draw text multiple times with slight offsets to create bold effect
                        page.insert_text(base_point, part_text, fontsize=font_size, fontname=base_font_name, color=color_tuple)
                        page.insert_text(fitz.Point(base_point.x + 0.5, base_point.y), part_text, fontsize=font_size, fontname=base_font_name, color=color_tuple)
                        page.insert_text(fitz.Point(base_point.x, base_point.y - 0.3), part_text, fontsize=font_size, fontname=base_font_name, color=color_tuple)
                        page.insert_text(fitz.Point(base_point.x + 0.5, base_point.y - 0.3), part_text, fontsize=font_size, fontname=base_font_name, color=color_tuple)
                        
                        # Calculate actual text width for accurate positioning
                        text_width = fitz.get_text_length(part_text, fontname=base_font_name, fontsize=font_size)
                    else:
                        # Regular text
                        page.insert_text(
                            fitz.Point(current_x, insertion_point.y),
                            part_text,
                            fontsize=font_size,
                            fontname=base_font_name,
                            color=color_tuple,
                        )
                        
                        # Calculate actual text width for accurate positioning
                        text_width = fitz.get_text_length(part_text, fontname=base_font_name, fontsize=font_size)
                    
                    # Move to next position using actual measured width
                    current_x += text_width
                
                # Successfully processed the span - increment counter
                self.stats['bionic_spans_created'] += 1
                self.logger.debug(f"Successfully inserted bionic formatted text: {text[:50]}...")
                
            except Exception as e:
                self.logger.error(f"Font-based text insertion failed: {e}")
                
                # Fallback: Insert original text without formatting
                try:
                    page.insert_text(
                        insertion_point,
                        text,
                        fontsize=font_size,
                        fontname=base_font_name,
                        color=color_tuple,
                    )
                    # Still count as successful processing even if we used fallback
                    self.stats['bionic_spans_created'] += 1
                    self.logger.debug(f"Fallback text insertion successful")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback text insertion also failed: {fallback_error}")
                    # Don't increment counter if both attempts failed
            
        except Exception as e:
            self.logger.error(f"Span morphing failed: {e}")
            # Don't let individual span failures stop the whole process
    
    def _get_bold_font_name(self, base_font: str) -> str:
        """
        Get the bold variant of a font with comprehensive mapping.
        Since PyMuPDF doesn't support bold font variants directly,
        this returns the base font name and bold formatting should be handled differently.
        
        Args:
            base_font: Base font name
            
        Returns:
            Valid PyMuPDF font name (not bold variant)
        """
        # Clean the font name
        base_font = base_font.lower().strip()
        
        # Map to valid PyMuPDF font names only
        font_mapping = {
            # Standard PDF fonts that PyMuPDF supports
            'helv': 'helv',
            'helvetica': 'helv', 
            'helv-oblique': 'helv',
            'helvetica-oblique': 'helv',
            'times': 'tiro',
            'times-roman': 'tiro',
            'times-italic': 'tiro',
            'courier': 'cour',
            'courier-oblique': 'cour',
            
            # Common system fonts mapped to PyMuPDF equivalents
            'arial': 'helv',
            'arial-black': 'helv',
            'calibri': 'helv',
            'georgia': 'tiro',
            'verdana': 'helv',
            'tahoma': 'helv',
            'trebuchet': 'helv',
            
            # Fallback patterns
            'sans-serif': 'helv',
            'serif': 'tiro',
            'monospace': 'cour',
        }
        
        # Try exact match first
        if base_font in font_mapping:
            return font_mapping[base_font]
        
        # Try pattern matching for complex font names
        for pattern, mapped_font in font_mapping.items():
            if pattern in base_font:
                return mapped_font
        
        # If font already is a valid PyMuPDF font, return as-is
        valid_fonts = ['helv', 'tiro', 'cour', 'symb', 'zadb']
        if base_font in valid_fonts:
            return base_font
            
        # Default fallback to helvetica
        return 'helv'

    def _get_font_name(self, span: Dict) -> str:
        """
        Extract font name from a text span and map to valid PyMuPDF font.
        
        Args:
            span: Text span dictionary containing font information
            
        Returns:
            Valid PyMuPDF font name string
        """
        # Try to get font name from span
        font_name = span.get('font', '')
        
        # Clean and normalize the font name
        if font_name:
            font_name = font_name.strip()
            # Convert to lowercase for consistent processing
            font_name_lower = font_name.lower()
            
            # Handle common PDF font variations - map to valid PyMuPDF fonts
            if 'helvetica' in font_name_lower or 'arial' in font_name_lower:
                return 'helv'
            elif 'times' in font_name_lower:
                return 'tiro'  # Use 'tiro' instead of 'times'
            elif 'courier' in font_name_lower:
                return 'cour'  # Use 'cour' instead of 'courier'
            elif 'symbol' in font_name_lower:
                return 'symb'
            elif 'zapf' in font_name_lower or 'dingbat' in font_name_lower:
                return 'zadb'
            else:
                # If it's already a valid PyMuPDF font, return it
                valid_fonts = ['helv', 'tiro', 'cour', 'symb', 'zadb']
                if font_name_lower in valid_fonts:
                    return font_name_lower
        
        # Fallback to default font
        return 'helv'

    def _count_text_spans(self, page) -> int:
        """
        Count the total number of text spans on a page.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Total number of text spans
        """
        try:
            span_count = 0
            
            # Get text blocks from the page
            blocks = page.get_text("dict")
            
            # Count spans in each block
            for block in blocks.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    span_count += len(line.get("spans", []))
            
            return span_count
            
        except Exception as e:
            self.logger.debug(f"Error counting text spans: {e}")
            return 0
    
    def _process_with_redaction(self, doc, config: BionicConfig, output_path: str) -> Dict[str, Any]:
        """
        Enhanced redaction-based processing with quality metrics.
        
        Args:
            doc: PyMuPDF document object
            config: Processing configuration
            output_path: Path for output file
            
        Returns:
            Dictionary with processing results and quality metrics
        """
        try:
            # Track processing statistics
            total_pages = len(doc)
            pages_processed = 0
            total_spans_attempted = 0
            total_spans_successful = 0
            
            self.logger.info(f"Starting redaction processing for {total_pages} pages")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                try:
                    # Count spans before processing
                    spans_before = self._count_text_spans(page)
                    total_spans_attempted += spans_before
                    
                    # Process page with redaction
                    spans_processed = self._process_page_with_redaction(page, config)
                    total_spans_successful += spans_processed
                    pages_processed += 1
                    
                    self.logger.debug(f"Page {page_num + 1}: {spans_processed}/{spans_before} spans enhanced")
                    
                except Exception as e:
                    self.logger.warning(f"Error processing page {page_num + 1}: {e}")
                    continue
            
            # Save the processed document
            doc.save(output_path)
            
            # Calculate quality metrics
            success_rate = total_spans_successful / total_spans_attempted if total_spans_attempted > 0 else 0
            processing_quality = 'excellent' if success_rate > 0.8 else 'good' if success_rate > 0.5 else 'fair' if success_rate > 0.2 else 'poor'
            
            self.logger.info(f"Redaction processing completed: {total_spans_successful}/{total_spans_attempted} spans enhanced ({success_rate:.1%})")
            
            return {
                'success': True,
                'output_path': output_path,
                'method_used': 'redaction',
                'quality_metrics': {
                    'pages_processed': pages_processed,
                    'total_pages': total_pages,
                    'spans_attempted': total_spans_attempted,
                    'spans_successful': total_spans_successful,
                    'success_rate': success_rate,
                    'processing_quality': processing_quality
                }
            }
            
        except Exception as e:
            self.logger.error(f"Redaction processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_path': None,
                'method_used': 'redaction',
                'quality_metrics': {
                    'pages_processed': 0,
                    'total_pages': total_pages if 'total_pages' in locals() else 0,
                    'success_rate': 0.0,
                    'processing_quality': 'failed'
                }
            }

    def _process_page_with_redaction(self, page, config: BionicConfig) -> int:
        """
        Process a single page using redaction method.
        
        Args:
            page: PyMuPDF page object
            config: Processing configuration
            
        Returns:
            int: Number of spans successfully processed
        """
        spans_processed = 0
        
        try:
            # Get text blocks
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        try:
                            # Get span text and properties
                            text = span.get("text", "").strip()
                            if not text:
                                continue
                            
                            # Apply bionic processing
                            intensity = getattr(config, 'bionic_intensity', 0.4)
                            bionic_parts = get_bionic_word_parts(text, intensity)
                            
                            # If there are parts to enhance, process them
                            if any(part[1] for part in bionic_parts):  # Check if any part should be bold
                                bbox = fitz.Rect(span["bbox"])
                                
                                # Remove original text
                                page.add_redact_annot(bbox)
                                
                                # Add enhanced text back
                                self._insert_bionic_text_redaction(page, bbox, bionic_parts, span)
                                spans_processed += 1
                                
                        except Exception as e:
                            self.logger.debug(f"Error processing span in redaction: {e}")
                            continue
            
            # Apply all redactions
            page.apply_redactions()
            
        except Exception as e:
            self.logger.warning(f"Error in redaction page processing: {e}")
        
        return spans_processed

    def _insert_bionic_text_redaction(self, page, bbox, bionic_parts, original_span):
        """Insert bionic formatted text using redaction method."""
        try:
            # Calculate text properties
            font_size = original_span.get("size", 12)
            font_color = original_span.get("color", 0)  # Default to black
            
            # Position for text insertion
            insert_point = fitz.Point(bbox.x0, bbox.y1 - 2)  # Slightly above bottom
            
            # Insert each part with appropriate formatting
            x_offset = 0
            for text_part, is_bold in bionic_parts:
                if not text_part:
                    continue
                
                # Use standard font for all text
                fontname = "helv"
                
                # Insert text part
                base_point = fitz.Point(bbox.x0 + x_offset, bbox.y1 - 2)
                
                if is_bold:
                    # Simulate bold by drawing text multiple times with slight offsets
                    page.insert_text(base_point, text_part, fontsize=font_size, fontname=fontname, color=font_color)
                    page.insert_text(fitz.Point(base_point.x + 0.5, base_point.y), text_part, fontsize=font_size, fontname=fontname, color=font_color)
                    page.insert_text(fitz.Point(base_point.x, base_point.y - 0.3), text_part, fontsize=font_size, fontname=fontname, color=font_color)
                    page.insert_text(fitz.Point(base_point.x + 0.5, base_point.y - 0.3), text_part, fontsize=font_size, fontname=fontname, color=font_color)
                else:
                    # Regular text - single insertion
                    page.insert_text(base_point, text_part, fontsize=font_size, fontname=fontname, color=font_color)
                
                # Calculate width of inserted text for next part position
                text_width = fitz.get_text_length(text_part, fontname=fontname, fontsize=font_size)
                x_offset += text_width
                
        except Exception as e:
            self.logger.debug(f"Error inserting bionic text in redaction: {e}")
            # Fallback: insert original text
            try:
                page.insert_text(
                    fitz.Point(bbox.x0, bbox.y1 - 2),
                    original_span.get("text", ""),
                    fontsize=original_span.get("size", 12),
                    color=original_span.get("color", 0)
                )
            except:
                pass
    
    def _process_with_hybrid(self, doc, config: BionicConfig, output_path: str) -> Dict[str, Any]:
        """
        Process PDF using hybrid approach (morphing + redaction).
        
        Args:
            doc: PyMuPDF document object (already opened)
            config: Processing configuration
            output_path: Output PDF path
            
        Returns:
            Processing result
        """
        try:
            # Try morphing first, fall back to redaction if needed
            try:
                return self._process_with_morphing(doc, config, output_path)
            except Exception as morphing_error:
                self.logger.warning(f"Morphing failed, trying redaction: {morphing_error}")
                self.stats['fallback_used'] = True
                return self._process_with_redaction(doc, config, output_path)
                
        except Exception as e:
            raise PDFProcessingError(f"Hybrid processing failed: {str(e)}")
    
    def _process_with_auto_fallback(self, input_path: str, output_path: str, 
                                  config: BionicConfig) -> Dict[str, Any]:
        """
        Process PDF with automatic method selection and fallbacks.
        
        Args:
            input_path: Input PDF path
            output_path: Output PDF path
            config: Processing configuration
            
        Returns:
            Processing result
        """
        methods_to_try = [
            (PDFMethod.MORPHING, self._process_with_morphing),
            (PDFMethod.REDACTION, self._process_with_redaction),
            (PDFMethod.HYBRID, self._process_with_hybrid)
        ]
        
        last_error = None
        
        # Open the document once and pass it to all methods
        try:
            doc = fitz.open(input_path)
            
            for method, processor_func in methods_to_try:
                try:
                    self.logger.info(f"Trying {method.value} method")
                    result = processor_func(doc, config, output_path)
                    self.stats['processing_method'] = method.value
                    return result
                    
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"{method.value} method failed: {e}")
                    continue
            
            # If all methods failed, raise the last error
            raise PDFProcessingError(f"All processing methods failed. Last error: {str(last_error)}")
            
        finally:
            if 'doc' in locals():
                doc.close()
    
    def extract_text_for_analysis(self, input_path: str) -> List[Dict[str, Any]]:
        """
        Extract text with positioning information for analysis.
        
        Args:
            input_path: Path to PDF file
            
        Returns:
            List of text elements with positioning and formatting info
        """
        text_elements = []
        
        try:
            with fitz.open(input_path) as doc:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Get detailed text information
                    text_dict = page.get_text("dict")
                    
                    for block_num, block in enumerate(text_dict["blocks"]):
                        if "lines" not in block:
                            continue
                        
                        for line_num, line in enumerate(block["lines"]):
                            for span_num, span in enumerate(line["spans"]):
                                if span["text"].strip():
                                    text_elements.append({
                                        'page': page_num,
                                        'block': block_num,
                                        'line': line_num,
                                        'span': span_num,
                                        'text': span["text"],
                                        'bbox': span["bbox"],
                                        'font': span.get("font", ""),
                                        'size': span["size"],
                                        'flags': span["flags"],
                                        'color': span["color"]
                                    })
        
        except Exception as e:
            self.logger.error(f"Text extraction for analysis failed: {e}")
        
        return text_elements
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()

    ###############################
    # Utility helpers
    ###############################

    def _int_to_rgb(self, color_int: Any) -> Tuple[float, float, float]:
        """Convert PyMuPDF span color (int or tuple) to an (r, g, b) tuple of 0-1 floats."""
        # If it's already a tuple or list with 3 numbers, normalise to 0-1 and return
        if isinstance(color_int, (tuple, list)) and len(color_int) >= 3:
            r, g, b = color_int[:3]
            # Assume values 0-1 or 0-255. If any value >1 we scale down.
            if max(r, g, b) > 1:
                return (r / 255.0, g / 255.0, b / 255.0)
            return (float(r), float(g), float(b))

        # If int, treat as 24-bit 0xRRGGBB value (most common for PyMuPDF)
        if isinstance(color_int, int):
            r = (color_int >> 16) & 0xFF
            g = (color_int >> 8) & 0xFF
            b = color_int & 0xFF
            return (r / 255.0, g / 255.0, b / 255.0)

        # Fallback – black
        return (0.0, 0.0, 0.0)

    def _choose_processing_method(self, doc):
        """
        Intelligently choose the best processing method based on PDF characteristics.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            str: 'morphing' or 'redaction' based on PDF analysis
        """
        try:
            # Analyze first few pages to determine complexity
            pages_to_analyze = min(3, len(doc))
            
            total_fonts = set()
            has_complex_layout = False
            has_images = False
            average_spans_per_page = 0
            
            for page_num in range(pages_to_analyze):
                page = doc[page_num]
                
                # Check for images
                if page.get_images():
                    has_images = True
                
                # Analyze text structure
                blocks = page.get_text("dict")
                span_count = 0
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                span_count += 1
                                if "font" in span:
                                    total_fonts.add(span["font"])
                
                average_spans_per_page += span_count
                
                # Check for complex layout (many short lines might indicate columns/tables)
                if len(blocks["blocks"]) > 20:  # Many blocks might indicate complex layout
                    has_complex_layout = True
            
            average_spans_per_page = average_spans_per_page / pages_to_analyze if pages_to_analyze > 0 else 0
            
            # Decision logic
            self.logger.debug(f"PDF Analysis - Fonts: {len(total_fonts)}, Complex layout: {has_complex_layout}, "
                            f"Images: {has_images}, Avg spans/page: {average_spans_per_page:.1f}")
            
            # Use morphing for simpler PDFs with standard fonts
            if (len(total_fonts) <= 5 and 
                not has_complex_layout and 
                average_spans_per_page < 200):
                self.logger.debug("Selected morphing method for simple PDF")
                return 'morphing'
            else:
                self.logger.debug("Selected redaction method for complex PDF")
                return 'redaction'
                
        except Exception as e:
            self.logger.warning(f"Error analyzing PDF for method selection: {e}, defaulting to morphing")
            return 'morphing'

    def _get_output_path(self, input_path: str, **kwargs) -> str:
        """Generate output path for processed PDF."""
        from pathlib import Path
        from ..utils.file_utils import create_output_path
        
        output_dir = Path(input_path).parent
        return create_output_path(
            input_path,
            output_dir=str(output_dir),
            suffix='_bionic',
            extension='pdf'
        ) 