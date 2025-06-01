"""
Main Bionic Processor Interface

This module provides a unified interface for the bionic reading processing system.
It delegates to specialized processors in the processors/ directory.
"""

from .processors.factory import BionicProcessorFactory, create_bionic_reading_file
from .processors.utils import detect_file_type

# Main interface functions for backward compatibility
def process_file(input_path):
    """
    Process a file for bionic reading.
    
    Args:
        input_path (str): Path to the input file.
        
    Returns:
        dict: Processing result with success status and output path.
    """
    return BionicProcessorFactory.process_file(input_path)

def get_supported_file_types():
    """
    Get list of supported file types.
    
    Returns:
        list: List of supported file extensions.
    """
    return BionicProcessorFactory.get_supported_types()

def is_file_supported(file_path):
    """
    Check if a file type is supported.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        bool: True if supported, False otherwise.
    """
    return BionicProcessorFactory.is_supported_type(file_path)

# Export key functions for external use
__all__ = [
    'process_file',
    'create_bionic_reading_file',
    'get_supported_file_types',
    'is_file_supported',
    'detect_file_type',
    'BionicProcessorFactory'
] 