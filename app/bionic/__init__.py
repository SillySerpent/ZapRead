"""
Enhanced Bionic Reading System - Modernized Architecture

This package provides advanced bionic reading capabilities with intelligent
document analysis, configurable intensity management, multi-format output,
and robust error handling.

Features:
- Intelligent document structure analysis
- Configurable bionic reading intensity
- Multiple output formats (plain text, HTML, Markdown, JSON)
- Advanced processing pipeline with fallbacks
- Comprehensive configuration system
- Performance optimization and error handling
"""

from .processors.text_processor import BionicTextProcessor, process_text_bionic, process_text_html
from .processors.pdf_advanced import AdvancedPDFProcessor
from .processors.utils import (
    apply_bionic_formatting_to_text,
    process_text_with_bionic_reading,
    DocumentAnalyzer,
    IntensityManager,
    OutputFormatterManager,
    ProcessingPipeline
)
from .core.bionic_config import BionicConfiguration

# Version information
__version__ = "2.0.0"
__author__ = "ZapRead Team"

# Main processor classes
__all__ = [
    # Main processors
    'BionicTextProcessor',
    'AdvancedPDFProcessor',
    
    # Configuration
    'BionicConfiguration',
    
    # Processing components
    'DocumentAnalyzer',
    'IntensityManager', 
    'OutputFormatterManager',
    'ProcessingPipeline',
    
    # Utility functions
    'apply_bionic_formatting_to_text',
    'process_text_with_bionic_reading',
    
    # Legacy compatibility
    'process_text_bionic',
    'process_text_html',
    
    # Version info
    '__version__'
]

# Default processor instance for quick access
_default_processor = None

def get_default_processor():
    """Get the default bionic text processor instance."""
    global _default_processor
    if _default_processor is None:
        _default_processor = BionicTextProcessor()
    return _default_processor

def process_text(text: str, **kwargs):
    """
    Quick text processing using default processor.
    
    Args:
        text: Text to process
        **kwargs: Additional processing options
        
    Returns:
        Processing result dictionary
    """
    return get_default_processor().process_text(text, **kwargs)

def reset_default_processor():
    """Reset the default processor instance."""
    global _default_processor
    _default_processor = None 