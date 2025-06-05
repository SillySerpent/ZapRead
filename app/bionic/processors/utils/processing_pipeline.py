"""
Advanced Bionic Processing Pipeline

Provides robust processing pipeline with fallback mechanisms,
error handling, and performance optimization.
"""

from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from enum import Enum
import time
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

from .document_analyzer import DocumentAnalyzer, DocumentElement
from .intensity_manager import IntensityManager, ReadingProfile
from .output_formatter import OutputFormatterManager, OutputFormat


class ProcessingStrategy(Enum):
    """Processing strategies for different scenarios."""
    CONSERVATIVE = "conservative"    # Safe processing with minimal changes
    BALANCED = "balanced"           # Optimal balance of enhancement and safety
    AGGRESSIVE = "aggressive"       # Maximum enhancement
    ADAPTIVE = "adaptive"          # Adapts based on content analysis
    CUSTOM = "custom"              # User-defined strategy


class ProcessingError(Exception):
    """Custom exception for processing errors."""
    pass


class ProcessingWarning(Exception):
    """Custom warning for processing issues."""
    pass


@dataclass
class ProcessingResult:
    """Container for processing results."""
    success: bool
    output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    processing_time: Optional[float] = None
    fallback_used: bool = False
    quality_score: Optional[float] = None


@dataclass
class ProcessingConfig:
    """Configuration for processing pipeline."""
    strategy: ProcessingStrategy = ProcessingStrategy.BALANCED
    output_format: OutputFormat = OutputFormat.PLAIN_TEXT
    reading_profile: ReadingProfile = ReadingProfile.ACCESSIBILITY
    enable_fallbacks: bool = True
    parallel_processing: bool = False
    max_workers: int = 4
    timeout_seconds: Optional[float] = 30.0
    preserve_formatting: bool = True
    quality_threshold: float = 0.7
    custom_intensity_map: Optional[Dict[DocumentElement, float]] = None
    debug_mode: bool = False


class ProcessingPipeline:
    """
    Advanced bionic reading processing pipeline with comprehensive error handling.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the processing pipeline.
        
        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.document_analyzer = DocumentAnalyzer()
        self.intensity_manager = IntensityManager(self.config.reading_profile)
        self.output_formatter = OutputFormatterManager()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'fallbacks_used': 0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0
        }
        
        # Apply custom settings if provided
        if self.config.custom_intensity_map:
            for element_type, intensity in self.config.custom_intensity_map.items():
                self.intensity_manager.set_custom_intensity(element_type, intensity)
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process single text element with bionic reading enhancement.
        
        Args:
            text: Text to process
            metadata: Optional metadata for the text
            
        Returns:
            Processing result
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # Validate input
            if not text or not text.strip():
                return ProcessingResult(
                    success=True,
                    output=text,
                    processing_time=time.time() - start_time,
                    warnings=["Empty or whitespace-only text provided"]
                )
            
            # Analyze text element
            element_analysis = self.document_analyzer.analyze_text_element(
                text, metadata or {}
            )
            
            # Get intensity recommendation
            intensity_data = self.intensity_manager.get_intensity_for_text(
                text, metadata
            )
            
            # Check if processing should be performed
            if not intensity_data['should_process']:
                if self.config.debug_mode:
                    warnings.append(f"Skipping processing for {intensity_data['element_type'].value}")
                
                return ProcessingResult(
                    success=True,
                    output=text,
                    metadata={
                        'element_analysis': element_analysis,
                        'intensity_data': intensity_data,
                        'processing_skipped': True
                    },
                    warnings=warnings,
                    processing_time=time.time() - start_time
                )
            
            # Primary processing attempt
            try:
                output = self._format_text_with_strategy(
                    text, intensity_data, element_analysis
                )
                
                # Quality check
                quality_score = self._calculate_quality_score(
                    text, output, intensity_data
                )
                
                if quality_score < self.config.quality_threshold and self.config.enable_fallbacks:
                    if self.config.debug_mode:
                        warnings.append(f"Quality score {quality_score:.2f} below threshold, trying fallback")
                    
                    # Attempt fallback processing
                    fallback_result = self._fallback_processing(
                        text, intensity_data, element_analysis
                    )
                    
                    if fallback_result:
                        output = fallback_result
                        quality_score = self._calculate_quality_score(
                            text, output, intensity_data
                        )
                        self.stats['fallbacks_used'] += 1
            
            except Exception as e:
                if self.config.enable_fallbacks:
                    if self.config.debug_mode:
                        warnings.append(f"Primary processing failed: {str(e)}")
                    
                    # Attempt fallback processing
                    fallback_result = self._fallback_processing(
                        text, intensity_data, element_analysis
                    )
                    
                    if fallback_result:
                        output = fallback_result
                        quality_score = self._calculate_quality_score(
                            text, output, intensity_data
                        )
                        self.stats['fallbacks_used'] += 1
                    else:
                        raise ProcessingError(f"Both primary and fallback processing failed: {str(e)}")
                else:
                    raise ProcessingError(f"Processing failed: {str(e)}")
            
            # Update statistics
            self.stats['total_processed'] += 1
            self.stats['successful_processes'] += 1
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            return ProcessingResult(
                success=True,
                output=output,
                metadata={
                    'element_analysis': element_analysis,
                    'intensity_data': intensity_data,
                    'original_length': len(text),
                    'processed_length': len(output) if output else 0
                },
                warnings=warnings,
                processing_time=processing_time,
                quality_score=quality_score
            )
            
        except Exception as e:
            # Final error handling
            error_msg = f"Processing failed completely: {str(e)}"
            errors.append(error_msg)
            
            if self.config.debug_mode:
                errors.append(traceback.format_exc())
            
            self.logger.error(error_msg)
            self.stats['total_processed'] += 1
            self.stats['failed_processes'] += 1
            
            return ProcessingResult(
                success=False,
                output=text if self.config.enable_fallbacks else None,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time,
                fallback_used=self.config.enable_fallbacks
            )
    
    def process_document(self, elements: List[Dict[str, Any]], 
                        document_metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process entire document with bionic reading enhancement.
        
        Args:
            elements: List of document elements to process
            document_metadata: Optional document metadata
            
        Returns:
            Processing result for entire document
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            if not elements:
                return ProcessingResult(
                    success=True,
                    output="",
                    warnings=["No elements provided for processing"],
                    processing_time=time.time() - start_time
                )
            
            # Analyze document structure
            doc_analysis = self.intensity_manager.analyze_document_and_recommend(elements)
            
            if self.config.debug_mode:
                warnings.append(f"Document analysis: {doc_analysis['processing_summary']}")
            
            # Process elements
            if self.config.parallel_processing and len(elements) > 5:
                processed_elements = self._process_elements_parallel(elements)
            else:
                processed_elements = self._process_elements_sequential(elements)
            
            # Check for processing errors
            failed_elements = [elem for elem in processed_elements if not elem.get('success', True)]
            if failed_elements:
                error_count = len(failed_elements)
                total_count = len(processed_elements)
                
                if error_count == total_count:
                    raise ProcessingError("All elements failed to process")
                elif error_count > total_count * 0.5:
                    warnings.append(f"High failure rate: {error_count}/{total_count} elements failed")
                else:
                    warnings.append(f"{error_count} elements failed to process")
            
            # Format final document
            formatted_document = self.output_formatter.format_document(
                processed_elements, 
                self.config.output_format,
                document_metadata or {}
            )
            
            # Calculate overall quality
            quality_scores = [elem.get('quality_score', 0.0) for elem in processed_elements 
                            if elem.get('quality_score') is not None]
            overall_quality = sum(quality_scores) / max(len(quality_scores), 1)
            
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            return ProcessingResult(
                success=True,
                output=formatted_document,
                metadata={
                    'document_analysis': doc_analysis,
                    'elements_processed': len(processed_elements),
                    'elements_failed': len(failed_elements),
                    'processing_strategy': self.config.strategy.value,
                    'output_format': self.config.output_format.value
                },
                warnings=warnings,
                processing_time=processing_time,
                quality_score=overall_quality
            )
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            errors.append(error_msg)
            
            if self.config.debug_mode:
                errors.append(traceback.format_exc())
            
            self.logger.error(error_msg)
            
            return ProcessingResult(
                success=False,
                errors=errors,
                warnings=warnings,
                processing_time=time.time() - start_time
            )
    
    def _format_text_with_strategy(self, text: str, intensity_data: Dict, 
                                 element_analysis: Dict) -> str:
        """
        Format text based on processing strategy.
        
        Args:
            text: Text to format
            intensity_data: Intensity recommendations
            element_analysis: Element analysis results
            
        Returns:
            Formatted text
        """
        strategy = self.config.strategy
        
        if strategy == ProcessingStrategy.CONSERVATIVE:
            # Reduce intensity for conservative processing
            adjusted_intensity = intensity_data['intensity'] * 0.7
        elif strategy == ProcessingStrategy.AGGRESSIVE:
            # Increase intensity for aggressive processing
            adjusted_intensity = min(1.0, intensity_data['intensity'] * 1.3)
        elif strategy == ProcessingStrategy.ADAPTIVE:
            # Adjust based on element confidence
            confidence = intensity_data.get('confidence', 0.8)
            adjusted_intensity = intensity_data['intensity'] * confidence
        else:  # BALANCED or CUSTOM
            adjusted_intensity = intensity_data['intensity']
        
        # Apply formatting
        return self.output_formatter.format_text(
            text, 
            adjusted_intensity, 
            self.config.output_format,
            element_analysis
        )
    
    def _fallback_processing(self, text: str, intensity_data: Dict, 
                           element_analysis: Dict) -> Optional[str]:
        """
        Attempt fallback processing strategies.
        
        Args:
            text: Text to process
            intensity_data: Intensity data
            element_analysis: Element analysis
            
        Returns:
            Processed text or None if all fallbacks fail
        """
        fallback_strategies = [
            # Try with reduced intensity
            lambda: self.output_formatter.format_text(
                text, intensity_data['intensity'] * 0.5, self.config.output_format
            ),
            # Try with plain text format
            lambda: self.output_formatter.format_text(
                text, intensity_data['intensity'], OutputFormat.PLAIN_TEXT
            ),
            # Try with minimal intensity
            lambda: self.output_formatter.format_text(
                text, 0.2, OutputFormat.PLAIN_TEXT
            ),
            # Last resort: return original text
            lambda: text
        ]
        
        for i, strategy in enumerate(fallback_strategies):
            try:
                result = strategy()
                if result and result != text:  # Ensure some processing occurred
                    if self.config.debug_mode:
                        self.logger.info(f"Fallback strategy {i+1} succeeded")
                    return result
                elif i == len(fallback_strategies) - 1:  # Last resort
                    return result
            except Exception as e:
                if self.config.debug_mode:
                    self.logger.warning(f"Fallback strategy {i+1} failed: {str(e)}")
                continue
        
        return None
    
    def _process_elements_sequential(self, elements: List[Dict]) -> List[Dict]:
        """Process elements sequentially."""
        processed_elements = []
        
        for element in elements:
            text = element.get('text', '')
            metadata = element.get('metadata', {})
            
            result = self.process_text(text, metadata)
            
            processed_element = {
                'text': result.output or text,
                'element_type': element.get('element_type', 'paragraph'),
                'metadata': {**metadata, **(result.metadata or {})},
                'success': result.success,
                'warnings': result.warnings,
                'errors': result.errors,
                'quality_score': result.quality_score
            }
            
            processed_elements.append(processed_element)
        
        return processed_elements
    
    def _process_elements_parallel(self, elements: List[Dict]) -> List[Dict]:
        """Process elements in parallel."""
        processed_elements = [None] * len(elements)
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit tasks
            future_to_index = {
                executor.submit(
                    self.process_text, 
                    element.get('text', ''), 
                    element.get('metadata', {})
                ): i
                for i, element in enumerate(elements)
            }
            
            # Collect results
            for future in as_completed(future_to_index, timeout=self.config.timeout_seconds):
                index = future_to_index[future]
                element = elements[index]
                
                try:
                    result = future.result()
                    
                    processed_element = {
                        'text': result.output or element.get('text', ''),
                        'element_type': element.get('element_type', 'paragraph'),
                        'metadata': {**element.get('metadata', {}), **(result.metadata or {})},
                        'success': result.success,
                        'warnings': result.warnings,
                        'errors': result.errors,
                        'quality_score': result.quality_score
                    }
                    
                    processed_elements[index] = processed_element
                    
                except Exception as e:
                    # Handle individual element failure
                    processed_elements[index] = {
                        'text': element.get('text', ''),
                        'element_type': element.get('element_type', 'paragraph'),
                        'metadata': element.get('metadata', {}),
                        'success': False,
                        'errors': [f"Parallel processing failed: {str(e)}"],
                        'quality_score': 0.0
                    }
        
        return processed_elements
    
    def _calculate_quality_score(self, original: str, processed: str, 
                               intensity_data: Dict) -> float:
        """
        Calculate quality score for processed text.
        
        Args:
            original: Original text
            processed: Processed text
            intensity_data: Intensity data used
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        if not processed or processed == original:
            return 0.5  # Neutral score for unchanged text
        
        try:
            # Basic quality metrics
            length_ratio = len(processed) / max(len(original), 1)
            
            # Penalize extreme length changes
            if length_ratio < 0.8 or length_ratio > 1.5:
                return 0.3
            
            # Check for malformed output (basic HTML tag check)
            if self.config.output_format == OutputFormat.HTML:
                tag_balance = self._check_html_tag_balance(processed)
                if not tag_balance:
                    return 0.4
            
            # Factor in confidence from intensity data
            confidence = intensity_data.get('confidence', 0.8)
            
            # Calculate base quality
            base_quality = 0.7  # Assume good quality by default
            
            # Adjust based on confidence
            adjusted_quality = base_quality * confidence
            
            # Bonus for appropriate length ratio
            if 0.9 <= length_ratio <= 1.2:
                adjusted_quality += 0.1
            
            return min(1.0, adjusted_quality)
            
        except Exception:
            return 0.5  # Default to neutral on error
    
    def _check_html_tag_balance(self, html_text: str) -> bool:
        """
        Basic check for balanced HTML tags.
        
        Args:
            html_text: HTML text to check
            
        Returns:
            True if tags appear balanced
        """
        import re
        
        # Count opening and closing span tags (main bionic formatting)
        opening_spans = len(re.findall(r'<span[^>]*>', html_text))
        closing_spans = len(re.findall(r'</span>', html_text))
        
        return opening_spans == closing_spans
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Statistics dictionary
        """
        total_time = self.stats['total_processing_time']
        total_processed = self.stats['total_processed']
        
        return {
            'total_processed': total_processed,
            'successful_processes': self.stats['successful_processes'],
            'failed_processes': self.stats['failed_processes'],
            'success_rate': (
                self.stats['successful_processes'] / max(total_processed, 1)
            ),
            'fallbacks_used': self.stats['fallbacks_used'],
            'fallback_rate': (
                self.stats['fallbacks_used'] / max(total_processed, 1)
            ),
            'total_processing_time': total_time,
            'average_processing_time': total_time / max(total_processed, 1),
            'configuration': {
                'strategy': self.config.strategy.value,
                'output_format': self.config.output_format.value,
                'reading_profile': self.config.reading_profile.value,
                'parallel_processing': self.config.parallel_processing,
                'enable_fallbacks': self.config.enable_fallbacks
            }
        }
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'fallbacks_used': 0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0
        }
    
    def update_config(self, **kwargs):
        """
        Update processing configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
                # Update dependent components
                if key == 'reading_profile':
                    self.intensity_manager = IntensityManager(value)
                elif key == 'custom_intensity_map' and value:
                    for element_type, intensity in value.items():
                        self.intensity_manager.set_custom_intensity(element_type, intensity)
    
    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        if self.config.quality_threshold < 0.0 or self.config.quality_threshold > 1.0:
            issues.append("Quality threshold must be between 0.0 and 1.0")
        
        if self.config.max_workers < 1:
            issues.append("Max workers must be at least 1")
        
        if self.config.timeout_seconds and self.config.timeout_seconds <= 0:
            issues.append("Timeout must be positive or None")
        
        if self.config.parallel_processing and self.config.max_workers > 10:
            issues.append("High worker count may cause performance issues")
        
        return issues 