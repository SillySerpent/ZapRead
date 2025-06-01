"""
Advanced PDF Processor for Bionic Reading

Implements multiple PDF processing strategies using PyMuPDF's advanced capabilities
including morphing, redaction, and comprehensive text analysis.
"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import fitz  # PyMuPDF
from ..core.config import BionicConfig, PDFMethod
from ..core.exceptions import PDFProcessingError
from ..utils.file_utils import create_output_path, get_temp_file_path
from .text_analysis import TextAnalyzer, BionicFormatter


logger = logging.getLogger(__name__)


class AdvancedPDFProcessor:
    """
    Advanced PDF processor with multiple processing strategies.
    
    Supports:
    - Direct text morphing with PyMuPDF
    - Redaction and reconstruction techniques
    - Multi-column text detection
    - Image and annotation preservation
    - Comprehensive error handling and fallbacks
    """
    
    def __init__(self, config: BionicConfig):
        """
        Initialize the advanced PDF processor.
        
        Args:
            config: Configuration object with processing settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.text_analyzer = TextAnalyzer(config)
        self.bionic_formatter = BionicFormatter(config)
        
        # Processing statistics
        self.stats = {
            'pages_processed': 0,
            'text_spans_processed': 0,
            'bionic_spans_created': 0,
            'images_preserved': 0,
            'annotations_preserved': 0,
            'processing_method': None,
            'fallback_used': False
        }
    
    def process(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
        """
        Process PDF file using the best available method.
        
        Args:
            input_path: Path to input PDF
            config: Processing configuration
            file_info: File metadata and validation info
            
        Returns:
            Processing result dictionary
        """
        try:
            self.logger.info(f"Starting advanced PDF processing: {input_path}")
            
            # Reset stats
            self._reset_stats()
            
            # Determine processing method
            processing_method = self._determine_processing_method(input_path, config, file_info)
            self.stats['processing_method'] = processing_method.value
            
            # Create output path
            output_path = create_output_path(
                input_path, 
                output_dir=getattr(config, 'output_directory', None),
                suffix='_bionic',
                extension='pdf'
            )
            
            # Process based on determined method
            if processing_method == PDFMethod.MORPHING:
                result = self._process_with_morphing(input_path, output_path, config)
            elif processing_method == PDFMethod.REDACTION:
                result = self._process_with_redaction(input_path, output_path, config)
            elif processing_method == PDFMethod.HYBRID:
                result = self._process_with_hybrid(input_path, output_path, config)
            else:  # AUTO
                result = self._process_with_auto_fallback(input_path, output_path, config)
            
            # Add processing metadata
            result.update({
                'method_used': processing_method.value,
                'stats': self.stats.copy(),
                'file_type': 'pdf',
                'metadata': {
                    'original_pages': file_info.get('metadata', {}).get('page_count', 0),
                    'original_size_mb': file_info.get('size_mb', 0),
                    'has_images': file_info.get('metadata', {}).get('has_images', False),
                    'has_annotations': file_info.get('metadata', {}).get('has_annotations', False)
                }
            })
            
            self.logger.info(f"PDF processing completed successfully using {processing_method.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Advanced PDF processing failed: {e}")
            raise PDFProcessingError(f"Advanced PDF processing failed: {str(e)}", 
                                   file_path=input_path, original_error=e)
    
    def _reset_stats(self):
        """Reset processing statistics."""
        self.stats.update({
            'pages_processed': 0,
            'text_spans_processed': 0,
            'bionic_spans_created': 0,
            'images_preserved': 0,
            'annotations_preserved': 0,
            'processing_method': None,
            'fallback_used': False
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
    
    def _process_with_morphing(self, input_path: str, output_path: str, 
                             config: BionicConfig) -> Dict[str, Any]:
        """
        Process PDF using PyMuPDF's text morphing capabilities.
        
        Args:
            input_path: Input PDF path
            output_path: Output PDF path
            config: Processing configuration
            
        Returns:
            Processing result
        """
        try:
            doc = fitz.open(input_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                self._process_page_with_morphing(page, config)
                self.stats['pages_processed'] += 1
            
            # Save the modified document
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            
            return {
                'success': True,
                'output_path': output_path,
                'method_used': 'morphing'
            }
            
        except Exception as e:
            raise PDFProcessingError(f"Morphing processing failed: {str(e)}")
    
    def _process_page_with_morphing(self, page: fitz.Page, config: BionicConfig):
        """
        Process a single page using morphing technique.
        
        Args:
            page: PyMuPDF page object
            config: Processing configuration
        """
        try:
            # Get text with detailed information
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" not in block:
                    continue  # Skip image blocks
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        self._process_text_span_morphing(page, span, config)
                        self.stats['text_spans_processed'] += 1
        
        except Exception as e:
            self.logger.warning(f"Page morphing processing failed: {e}")
    
    def _process_text_span_morphing(self, page: fitz.Page, span: Dict, config: BionicConfig):
        """
        Process individual text span with morphing.
        
        Args:
            page: PyMuPDF page object
            span: Text span dictionary
            config: Processing configuration
        """
        try:
            text = span["text"]
            if not text.strip():
                return
            
            # Analyze and format text for bionic reading
            formatted_text = self.bionic_formatter.format_text(text)
            
            if formatted_text == text:
                return  # No changes needed
            
            # Create new text insertion with morphing
            bbox = fitz.Rect(span["bbox"])
            
            # Remove original text by covering with background color
            page.add_redact_annot(bbox)
            page.apply_redactions()
            
            # Insert formatted text with morphing
            font_size = span["size"]
            font_flags = span["flags"]
            color = span["color"]
            
            # Calculate morphing parameters for bold effect
            morph = fitz.Matrix(1.0, 0, 0, 1.0, 0, 0)  # Identity matrix as base
            
            # Insert the bionic formatted text
            page.insert_text(
                bbox.tl,
                formatted_text,
                fontsize=font_size,
                color=color,
                morph=morph
            )
            
            self.stats['bionic_spans_created'] += 1
            
        except Exception as e:
            self.logger.debug(f"Span morphing failed: {e}")
    
    def _process_with_redaction(self, input_path: str, output_path: str, 
                              config: BionicConfig) -> Dict[str, Any]:
        """
        Process PDF using redaction and reconstruction technique.
        
        Args:
            input_path: Input PDF path
            output_path: Output PDF path
            config: Processing configuration
            
        Returns:
            Processing result
        """
        try:
            doc = fitz.open(input_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                self._process_page_with_redaction(page, config)
                self.stats['pages_processed'] += 1
            
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            
            return {
                'success': True,
                'output_path': output_path,
                'method_used': 'redaction'
            }
            
        except Exception as e:
            raise PDFProcessingError(f"Redaction processing failed: {str(e)}")
    
    def _process_page_with_redaction(self, page: fitz.Page, config: BionicConfig):
        """
        Process page using redaction technique.
        
        Args:
            page: PyMuPDF page object
            config: Processing configuration
        """
        try:
            # Extract text blocks with positioning
            blocks = page.get_text("dict")["blocks"]
            text_insertions = []
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                # Process each line in the block
                for line in block["lines"]:
                    line_insertions = self._process_line_with_redaction(page, line, config)
                    text_insertions.extend(line_insertions)
            
            # Apply all redactions first
            page.apply_redactions()
            
            # Then insert all bionic formatted text
            for insertion in text_insertions:
                try:
                    page.insert_text(
                        insertion['point'],
                        insertion['text'],
                        fontsize=insertion['fontsize'],
                        color=insertion['color'],
                        fontname=insertion.get('fontname', 'helv')
                    )
                except Exception as e:
                    self.logger.debug(f"Text insertion failed: {e}")
        
        except Exception as e:
            self.logger.warning(f"Page redaction processing failed: {e}")
    
    def _process_line_with_redaction(self, page: fitz.Page, line: Dict, 
                                   config: BionicConfig) -> List[Dict]:
        """
        Process a line using redaction technique.
        
        Args:
            page: PyMuPDF page object
            line: Line dictionary
            config: Processing configuration
            
        Returns:
            List of text insertions to make
        """
        insertions = []
        
        for span in line["spans"]:
            text = span["text"]
            if not text.strip():
                continue
            
            self.stats['text_spans_processed'] += 1
            
            # Format text for bionic reading
            formatted_text = self.bionic_formatter.format_text(text)
            
            if formatted_text != text:
                # Create redaction annotation
                bbox = fitz.Rect(span["bbox"])
                page.add_redact_annot(bbox)
                
                # Prepare text insertion
                insertions.append({
                    'point': bbox.tl,
                    'text': formatted_text,
                    'fontsize': span["size"],
                    'color': span["color"],
                    'fontname': self._get_font_name(span)
                })
                
                self.stats['bionic_spans_created'] += 1
        
        return insertions
    
    def _get_font_name(self, span: Dict) -> str:
        """
        Get appropriate font name for text insertion.
        
        Args:
            span: Text span dictionary
            
        Returns:
            Font name for PyMuPDF
        """
        font_name = span.get("font", "").lower()
        
        # Map common fonts to PyMuPDF names
        if "bold" in font_name or span.get("flags", 0) & 2**4:
            return "helv-bold"
        elif "italic" in font_name or span.get("flags", 0) & 2**1:
            return "helv-oblique"
        else:
            return "helv"
    
    def _process_with_hybrid(self, input_path: str, output_path: str, 
                           config: BionicConfig) -> Dict[str, Any]:
        """
        Process PDF using hybrid approach (morphing + redaction).
        
        Args:
            input_path: Input PDF path
            output_path: Output PDF path
            config: Processing configuration
            
        Returns:
            Processing result
        """
        try:
            # Try morphing first, fall back to redaction if needed
            try:
                return self._process_with_morphing(input_path, output_path, config)
            except Exception as morphing_error:
                self.logger.warning(f"Morphing failed, trying redaction: {morphing_error}")
                self.stats['fallback_used'] = True
                return self._process_with_redaction(input_path, output_path, config)
                
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
        
        for method, processor_func in methods_to_try:
            try:
                self.logger.info(f"Trying {method.value} method")
                result = processor_func(input_path, output_path, config)
                self.stats['processing_method'] = method.value
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"{method.value} method failed: {e}")
                continue
        
        # If all methods failed, raise the last error
        raise PDFProcessingError(f"All processing methods failed. Last error: {str(last_error)}")
    
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