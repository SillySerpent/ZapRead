"""
Bionic Processor Factory

Provides a unified factory for creating and managing different file type processors
with automatic processor selection and configuration management.
"""

import logging
from typing import Dict, Any, Optional, Type, Union
from pathlib import Path

from ..core.config import BionicConfig
from ..core.exceptions import UnsupportedFileTypeError, BionicProcessingError
from ..utils.file_utils import detect_file_type


logger = logging.getLogger(__name__)


class BionicProcessorFactory:
    """
    Factory class for creating appropriate processors based on file type.
    
    Manages processor instances and provides a unified interface for
    processing different file types with optimal strategies.
    """
    
    def __init__(self, config: Optional[BionicConfig] = None):
        """
        Initialize the processor factory.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or BionicConfig()
        self.logger = logging.getLogger(__name__)
        
        # Processor registry
        self._processors = {}
        self._processor_classes = {}
        
        # Initialize processor registry
        self._register_processors()
    
    def _register_processors(self):
        """Register available processors for different file types."""
        try:
            # Register PDF processor
            from .pdf_advanced import AdvancedPDFProcessor
            self._processor_classes['pdf'] = AdvancedPDFProcessor
            
            # Register other processors as needed
            # Note: These would be imported if the modules exist
            # For now, we'll use the existing processors for compatibility
            
        except ImportError as e:
            self.logger.warning(f"Some processors not available: {e}")
    
    def get_processor(self, file_type: str, **kwargs) -> Any:
        """
        Get or create a processor for the specified file type.
        
        Args:
            file_type: Type of file to process
            **kwargs: Additional configuration options
            
        Returns:
            Processor instance for the file type
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
        """
        if file_type not in self.config.supported_types:
            raise UnsupportedFileTypeError(file_type)
        
        # Check if processor is already cached
        cache_key = f"{file_type}_{hash(str(sorted(kwargs.items())))}"
        if cache_key in self._processors:
            return self._processors[cache_key]
        
        # Create new processor instance
        processor = self._create_processor(file_type, **kwargs)
        
        # Cache the processor
        self._processors[cache_key] = processor
        
        return processor
    
    def _create_processor(self, file_type: str, **kwargs) -> Any:
        """
        Create a new processor instance for the file type.
        
        Args:
            file_type: Type of file to process
            **kwargs: Additional configuration options
            
        Returns:
            New processor instance
        """
        # Create configuration with overrides
        config = self._create_config_with_overrides(**kwargs)
        
        if file_type == 'pdf':
            if 'pdf' in self._processor_classes:
                return self._processor_classes['pdf'](config)
            else:
                # Fallback to existing processor
                return self._create_fallback_pdf_processor(config)
        
        elif file_type == 'docx':
            return self._create_docx_processor(config)
        
        elif file_type == 'txt':
            return self._create_text_processor(config)
        
        else:
            raise UnsupportedFileTypeError(file_type)
    
    def _create_config_with_overrides(self, **kwargs) -> BionicConfig:
        """Create configuration object with provided overrides."""
        # Start with base config
        config_dict = self.config.to_dict()
        
        # Apply overrides
        config_dict.update(kwargs)
        
        return BionicConfig.from_dict(config_dict)
    
    def _create_fallback_pdf_processor(self, config: BionicConfig):
        """Create fallback PDF processor using existing code."""
        class FallbackPDFProcessor:
            def __init__(self, config):
                self.config = config
                
            def process(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
                # Import existing processor function
                try:
                    from .pdf_processor import process_pdf_file
                    result = process_pdf_file(input_path)
                    
                    if result['success']:
                        return {
                            'success': True,
                            'output_path': result['output_path'],
                            'file_type': 'pdf',
                            'method_used': 'fallback',
                            'metadata': file_info.get('metadata', {})
                        }
                    else:
                        raise BionicProcessingError(result.get('error', 'PDF processing failed'))
                        
                except ImportError:
                    raise BionicProcessingError("No PDF processor available")
                except Exception as e:
                    raise BionicProcessingError(f"PDF processing failed: {str(e)}")
        
        return FallbackPDFProcessor(config)
    
    def _create_docx_processor(self, config: BionicConfig):
        """Create DOCX processor."""
        class DocxProcessor:
            def __init__(self, config):
                self.config = config
                
            def process(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
                try:
                    from .docx_processor import process_docx_file
                    result = process_docx_file(input_path)
                    
                    if result['success']:
                        return {
                            'success': True,
                            'output_path': result['output_path'],
                            'file_type': 'docx',
                            'method_used': 'standard',
                            'metadata': file_info.get('metadata', {})
                        }
                    else:
                        raise BionicProcessingError(result.get('error', 'DOCX processing failed'))
                        
                except ImportError:
                    raise BionicProcessingError("DOCX processor not available")
                except Exception as e:
                    raise BionicProcessingError(f"DOCX processing failed: {str(e)}")
        
        return DocxProcessor(config)
    
    def _create_text_processor(self, config: BionicConfig):
        """Create text processor."""
        class TextProcessor:
            def __init__(self, config):
                self.config = config
                
            def process(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
                try:
                    from .text_processor import process_text_file
                    result = process_text_file(input_path)
                    
                    if result['success']:
                        return {
                            'success': True,
                            'output_path': result['output_path'],
                            'file_type': 'txt',
                            'method_used': 'standard',
                            'metadata': file_info.get('metadata', {})
                        }
                    else:
                        raise BionicProcessingError(result.get('error', 'Text processing failed'))
                        
                except ImportError:
                    raise BionicProcessingError("Text processor not available")
                except Exception as e:
                    raise BionicProcessingError(f"Text processing failed: {str(e)}")
        
        return TextProcessor(config)
    
    def process_file(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a file using the appropriate processor.
        
        Args:
            input_path: Path to the input file
            **kwargs: Processing options
            
        Returns:
            Processing result dictionary
        """
        try:
            # Detect file type
            file_type = detect_file_type(input_path)
            
            if file_type == 'unknown':
                raise UnsupportedFileTypeError('unknown', input_path)
            
            # Get appropriate processor
            processor = self.get_processor(file_type, **kwargs)
            
            # Create file info (simplified for factory)
            file_info = {
                'file_type': file_type,
                'file_path': input_path,
                'metadata': {}
            }
            
            # Create processing config
            config = self._create_config_with_overrides(**kwargs)
            
            # Process the file
            if hasattr(processor, 'process'):
                return processor.process(input_path, config, file_info)
            else:
                # Fallback for simple processors
                return processor.process_file(input_path)
                
        except Exception as e:
            self.logger.error(f"Factory processing failed for {input_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': input_path,
                'processor': 'factory'
            }
    
    def get_supported_types(self) -> list:
        """Get list of supported file types."""
        return self.config.supported_types.copy()
    
    def is_supported(self, file_path_or_type: str) -> bool:
        """Check if a file type is supported."""
        if Path(file_path_or_type).exists():
            file_type = detect_file_type(file_path_or_type)
        else:
            file_type = file_path_or_type.lower().lstrip('.')
        
        return file_type in self.config.supported_types
    
    def clear_cache(self):
        """Clear processor cache."""
        self._processors.clear()
        self.logger.debug("Processor cache cleared")
    
    def get_processor_info(self, file_type: str) -> Dict[str, Any]:
        """Get information about a processor for a file type."""
        if file_type not in self.config.supported_types:
            return {
                'supported': False,
                'processor_class': None,
                'capabilities': []
            }
        
        processor_class = self._processor_classes.get(file_type)
        
        capabilities = []
        if file_type == 'pdf':
            capabilities = [
                'morphing', 'redaction', 'hybrid_processing',
                'multi_column_detection', 'image_preservation'
            ]
        elif file_type == 'docx':
            capabilities = ['text_extraction', 'formatting_preservation']
        elif file_type == 'txt':
            capabilities = ['text_processing', 'encoding_detection']
        
        return {
            'supported': True,
            'processor_class': processor_class.__name__ if processor_class else 'Fallback',
            'capabilities': capabilities,
            'advanced_features': processor_class is not None
        }
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """Get factory statistics."""
        return {
            'supported_types': len(self.config.supported_types),
            'cached_processors': len(self._processors),
            'registered_classes': len(self._processor_classes),
            'available_processors': list(self._processor_classes.keys()),
            'fallback_processors': [
                t for t in self.config.supported_types 
                if t not in self._processor_classes
            ]
        }

# Convenience function for backward compatibility
def create_bionic_reading_file(input_path):
    """
    Create a bionic reading file from the input file.
    
    Args:
        input_path (str): Path to the input file.
        
    Returns:
        dict: Processing result with success status and output path.
    """
    return BionicProcessorFactory().process_file(input_path) 