"""
Bionic Processor Exception Classes

Custom exceptions for the bionic reading processor system.
"""


class BionicProcessingError(Exception):
    """Base exception for bionic processing errors."""
    
    def __init__(self, message, file_path=None, processor_type=None, original_error=None):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.processor_type = processor_type
        self.original_error = original_error
    
    def __str__(self):
        parts = [self.message]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.processor_type:
            parts.append(f"Processor: {self.processor_type}")
        if self.original_error:
            parts.append(f"Original error: {str(self.original_error)}")
        return " | ".join(parts)


class UnsupportedFileTypeError(BionicProcessingError):
    """Exception raised when an unsupported file type is encountered."""
    
    def __init__(self, file_type, file_path=None):
        message = f"Unsupported file type: {file_type}"
        super().__init__(message, file_path=file_path)
        self.file_type = file_type


class FileNotFoundError(BionicProcessingError):
    """Exception raised when input file is not found."""
    
    def __init__(self, file_path):
        message = f"File not found: {file_path}"
        super().__init__(message, file_path=file_path)


class ProcessingTimeoutError(BionicProcessingError):
    """Exception raised when processing takes too long."""
    
    def __init__(self, timeout_seconds, file_path=None):
        message = f"Processing timeout after {timeout_seconds} seconds"
        super().__init__(message, file_path=file_path)
        self.timeout_seconds = timeout_seconds


class MemoryError(BionicProcessingError):
    """Exception raised when processing runs out of memory."""
    
    def __init__(self, file_path=None):
        message = "Insufficient memory for processing"
        super().__init__(message, file_path=file_path)


class PDFProcessingError(BionicProcessingError):
    """Exception raised for PDF-specific processing errors."""
    
    def __init__(self, message, page_number=None, **kwargs):
        super().__init__(message, processor_type="PDF", **kwargs)
        self.page_number = page_number


class TextAnalysisError(BionicProcessingError):
    """Exception raised for text analysis errors."""
    
    def __init__(self, message, text_segment=None, **kwargs):
        super().__init__(message, processor_type="TextAnalysis", **kwargs)
        self.text_segment = text_segment


class ConfigurationError(BionicProcessingError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message, config_key=None, **kwargs):
        super().__init__(message, processor_type="Configuration", **kwargs)
        self.config_key = config_key 