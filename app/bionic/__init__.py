"""
ZapRead Bionic Reading Processor

A comprehensive bionic reading processor that supports multiple file formats
with advanced PDF processing capabilities and robust text analysis.
"""

from .core.processor import BionicProcessor
from .core.exceptions import BionicProcessingError, UnsupportedFileTypeError
from .processors.factory import BionicProcessorFactory

# Main interface functions (backwards compatibility)
def process_file(input_path, **kwargs):
    """
    Process a file for bionic reading.
    
    Args:
        input_path (str): Path to the input file
        **kwargs: Additional processing options
        
    Returns:
        dict: Processing result with success status and output path
    """
    processor = BionicProcessor()
    return processor.process_file(input_path, **kwargs)

def get_supported_file_types():
    """Get list of supported file types."""
    return BionicProcessor.get_supported_types()

def is_file_supported(file_path):
    """Check if a file type is supported."""
    return BionicProcessor.is_supported_type(file_path)

# Main exports
__all__ = [
    'BionicProcessor',
    'BionicProcessorFactory', 
    'BionicProcessingError',
    'UnsupportedFileTypeError',
    'process_file',
    'get_supported_file_types',
    'is_file_supported'
]

__version__ = '2.0.0' 