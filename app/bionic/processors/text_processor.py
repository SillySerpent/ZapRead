"""
Enhanced Bionic Text Processor - Modernized System

This module provides enhanced bionic reading text processing with intelligent
document analysis, configurable intensity, and multiple output formats.
"""

import logging
from typing import Dict, Any, Optional, Union
import time

# Import modernized bionic components
from .utils import (
    process_text_with_bionic_reading,
    apply_bionic_formatting_to_text,
    ProcessingPipeline,
    ProcessingConfig,
    OutputFormat,
    ReadingProfile,
    ProcessingStrategy
)
from ..core.bionic_config import BionicConfiguration

logger = logging.getLogger(__name__)


class BionicTextProcessor:
    """
    Enhanced Bionic Text Processor with intelligent document analysis,
    configurable intensity management, and multi-format output support.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the bionic text processor.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config = BionicConfiguration(config_file)
        self.processing_stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0
        }
        
        logger.info("BionicTextProcessor initialized with modernized system")
    
    def process_text(self, 
                    text: str, 
                    intensity: Optional[float] = None,
                    output_format: str = "plain_text",
                    document_type: Optional[str] = None,
                    custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process text with bionic reading enhancement.
        
        Args:
            text: Input text to process
            intensity: Custom intensity (0.0-1.0), overrides config
            output_format: Output format (plain_text, html, markdown, json)
            document_type: Type of document for optimized processing
            custom_config: Additional configuration options
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        try:
            # Get configuration for this document type
            doc_config = self.config.get_config_for_document(
                document_type or "general",
                {}
            )
            
            # Extract user preferences from nested structure
            user_prefs = doc_config.get('user_preferences', {})
            
            # Build processing configuration
            processing_config = {
                'intensity': intensity or user_prefs.get('default_intensity', 0.4),
                'profile': user_prefs.get('default_profile', 'standard'),
                'strategy': user_prefs.get('processing_strategy', 'balanced')
            }
            
            # Apply custom configuration
            if custom_config:
                processing_config.update(custom_config)
            
            # Process text using modernized system
            result = process_text_with_bionic_reading(
                text=text,
                config=processing_config,
                output_format=output_format
            )
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(result, processing_time)
            
            # Add processor metadata
            result['processor_metadata'] = {
                'processor_version': '2.0.0',
                'document_type': document_type,
                'intensity_used': processing_config['intensity'],
                'profile_used': processing_config['profile'],
                'strategy_used': processing_config['strategy'],
                'processing_time': processing_time
            }
            
            logger.info(f"Text processed successfully in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            # Fallback to simple processing
            logger.warning(f"Advanced processing failed, using fallback: {e}")
            
            fallback_result = {
                'success': True,
                'output': apply_bionic_formatting_to_text(text, intensity or 0.4),
                'metadata': {
                    'fallback_used': True,
                    'fallback_reason': str(e)
                },
                'warnings': [f"Advanced processing failed: {e}"],
                'errors': [],
                'processing_time': time.time() - start_time,
                'quality_score': 0.3,
                'processor_metadata': {
                    'processor_version': '2.0.0-fallback',
                    'document_type': document_type,
                    'intensity_used': intensity or 0.4,
                    'fallback_mode': True
                }
            }
            
            self._update_stats(fallback_result, time.time() - start_time)
            return fallback_result
    
    def process_html(self, 
                    text: str, 
                    intensity: Optional[float] = None,
                    custom_css: Optional[str] = None,
                    document_type: Optional[str] = None) -> str:
        """
        Process text and return HTML formatted output.
        
        Args:
            text: Input text to process
            intensity: Custom intensity (0.0-1.0)
            custom_css: Custom CSS for styling
            document_type: Type of document for optimized processing
            
        Returns:
            HTML formatted bionic text
        """
        try:
            result = self.process_text(
                text=text,
                intensity=intensity,
                output_format="html",
                document_type=document_type,
                custom_config={'custom_css': custom_css} if custom_css else None
            )
            
            if result['success']:
                return result['output']
            else:
                logger.warning("HTML processing failed, returning original text")
                return text
                
        except Exception as e:
            logger.error(f"HTML processing error: {e}")
            return text
    
    def batch_process(self, 
                     texts: list, 
                     intensity: Optional[float] = None,
                     output_format: str = "plain_text",
                     document_type: Optional[str] = None) -> list:
        """
        Process multiple texts in batch.
        
        Args:
            texts: List of texts to process
            intensity: Custom intensity for all texts
            output_format: Output format for all texts
            document_type: Document type for all texts
            
        Returns:
            List of processing results
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.process_text(
                    text=text,
                    intensity=intensity,
                    output_format=output_format,
                    document_type=document_type
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch processing failed for text {i}: {e}")
                results.append({
                    'success': False,
                    'output': text,
                    'errors': [str(e)],
                    'batch_index': i
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0
        }
        logger.info("Processing statistics reset")
    
    def update_config(self, config_updates: Dict[str, Any]):
        """
        Update processor configuration.
        
        Args:
            config_updates: Configuration updates to apply
        """
        try:
            if 'user_preferences' in config_updates:
                self.config.update_user_preferences(config_updates['user_preferences'])
            
            if 'document_types' in config_updates:
                for doc_type, config in config_updates['document_types'].items():
                    self.config.update_document_type_config(doc_type, config)
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            raise
    
    def _update_stats(self, result: Dict[str, Any], processing_time: float):
        """Update internal processing statistics."""
        self.processing_stats['total_processed'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        
        if result['success']:
            self.processing_stats['successful_processes'] += 1
        else:
            self.processing_stats['failed_processes'] += 1
        
        # Update average quality score
        if 'quality_score' in result:
            current_avg = self.processing_stats['average_quality_score']
            total_processed = self.processing_stats['total_processed']
            
            new_avg = ((current_avg * (total_processed - 1)) + result['quality_score']) / total_processed
            self.processing_stats['average_quality_score'] = new_avg


# Backward compatibility functions
def process_text_bionic(text: str, intensity: float = 0.4) -> str:
    """
    Legacy compatibility function for simple bionic text processing.
    
    Args:
        text: Text to process
        intensity: Bionic intensity (0.0-1.0)
        
    Returns:
        Processed bionic text
    """
    processor = BionicTextProcessor()
    result = processor.process_text(text, intensity=intensity)
    return result['output']


def process_text_html(text: str, intensity: float = 0.4) -> str:
    """
    Legacy compatibility function for HTML bionic text processing.
    
    Args:
        text: Text to process  
        intensity: Bionic intensity (0.0-1.0)
        
    Returns:
        HTML formatted bionic text
    """
    processor = BionicTextProcessor()
    return processor.process_html(text, intensity=intensity) 