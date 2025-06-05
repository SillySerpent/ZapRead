"""
Bionic Processor Core

Main processor class that coordinates all bionic reading processing operations
with advanced PDF capabilities and robust error handling.
"""

import os
import time
import logging
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .config import BionicConfig, get_config, PDFMethod, ProcessingMode
from .exceptions import (
    BionicProcessingError, UnsupportedFileTypeError, 
    FileNotFoundError, ProcessingTimeoutError, PDFProcessingError
)
from ..processors.pdf_advanced import AdvancedPDFProcessor
from ..processors.docx_processor import process_docx_file
from ..processors.utils import apply_bionic_formatting_to_text
from ..utils.file_utils import detect_file_type, validate_file


class BionicProcessor:
    """
    Main bionic reading processor with advanced capabilities.
    
    Supports multiple file formats with optimized processing strategies
    and comprehensive error handling.
    """
    
    def __init__(self, config: Optional[BionicConfig] = None):
        """
        Initialize the bionic processor.
        
        Args:
            config: Optional configuration object. If None, uses default config.
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        self._setup_temp_directory()
        
        # Initialize specialized processors
        self.pdf_processor = AdvancedPDFProcessor(self.config)
        
        # Processing statistics
        self.stats = {
            'files_processed': 0,
            'processing_time_total': 0.0,
            'errors_count': 0,
            'last_error': None
        }
    
    def _setup_temp_directory(self):
        """Setup temporary directory for processing."""
        self.temp_dir = tempfile.mkdtemp(prefix='bionic_processor_')
        self.logger.debug(f"Created temporary directory: {self.temp_dir}")
    
    def process_file(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a file for bionic reading.
        
        Args:
            input_path: Path to the input file
            **kwargs: Additional processing options that override config
            
        Returns:
            Dictionary with processing results:
            {
                'success': bool,
                'output_path': str,
                'file_type': str,
                'processing_time': float,
                'method_used': str,
                'metadata': dict,
                'error': str (if success=False)
            }
        """
        start_time = time.time()
        
        try:
            # Validate input file
            if not os.path.exists(input_path):
                raise FileNotFoundError(input_path)
            
            file_info = validate_file(input_path, self.config)
            
            # Check if validation was successful
            if not file_info.get('is_valid', False):
                validation_errors = file_info.get('validation_errors', ['Unknown validation error'])
                raise BionicProcessingError(f"File validation failed: {'; '.join(validation_errors)}")
            
            file_type = file_info.get('file_type', 'unknown')
            
            if file_type == 'unknown':
                raise UnsupportedFileTypeError('unknown', input_path)
            
            if file_type not in self.config.supported_types:
                raise UnsupportedFileTypeError(file_type, input_path)
            
            self.logger.info(f"Processing {file_type} file: {input_path}")
            
            # Create temporary config with kwargs overrides
            processing_config = self._create_processing_config(**kwargs)
            
            # Route to appropriate processor
            if file_type == 'pdf':
                result = self._process_pdf(input_path, processing_config, file_info)
            elif file_type == 'docx':
                result = self._process_docx(input_path, processing_config, file_info)
            elif file_type == 'txt':
                result = self._process_text(input_path, processing_config, file_info)
            else:
                raise UnsupportedFileTypeError(file_type, input_path)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            result.update({
                'processing_time': processing_time,
                'processor_version': '2.0.0',
                'method_used': result.get('method_used', 'standard'),
                'processor_metadata': {
                    'processor_version': '2.0.0',
                    'intensity_used': processing_config.bionic_intensity,
                    'reading_profile': kwargs.get('reading_profile', 'standard'),
                    'processing_mode': processing_config.processing_mode.value,
                    'fallback_used': False
                },
                'config_used': processing_config.to_dict() if hasattr(processing_config, 'to_dict') else str(processing_config)
            })
            
            self._update_stats(processing_time, True)
            self.logger.info(f"Successfully processed file in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            processing_time = time.time() - start_time
            
            self.logger.error(f"Processing failed for {input_path}: {error_msg}")
            self._update_stats(processing_time, False, error_msg)
            
            # Try to get file_type from exception or file_info, fallback to 'unknown'
            file_type = 'unknown'
            if hasattr(e, 'file_type'):
                file_type = e.file_type
            elif 'file_info' in locals():
                file_type = file_info.get('file_type', 'unknown')
            
            return {
                'success': False,
                'error': error_msg,
                'file_type': file_type,
                'processing_time': processing_time,
                'file_path': input_path
            }
    
    def _create_processing_config(self, **kwargs) -> BionicConfig:
        """Create a processing-specific configuration with enhanced parameter mapping."""
        # Create a copy of the current config
        config_dict = self.config.to_dict()
        
        # Map new parameters to existing config parameters with validation
        if 'bionic_intensity' in kwargs:
            intensity = kwargs['bionic_intensity']
            # Ensure intensity is in valid range
            intensity = max(0.0, min(1.0, float(intensity)))
            config_dict['bionic_intensity'] = intensity
            self.logger.debug(f"Applied bionic intensity: {intensity}")
        
        if 'reading_profile' in kwargs:
            # Map reading profiles to processing modes for compatibility
            profile_mapping = {
                'speed': ProcessingMode.SPEED,
                'speed_reading': ProcessingMode.SPEED,
                'balanced': ProcessingMode.BALANCED,
                'standard': ProcessingMode.BALANCED,
                'quality': ProcessingMode.QUALITY,
                'accessibility': ProcessingMode.BALANCED,
                'technical': ProcessingMode.QUALITY,
                'preservation': ProcessingMode.QUALITY
            }
            profile = kwargs['reading_profile']
            if profile in profile_mapping:
                config_dict['processing_mode'] = profile_mapping[profile]
                self.logger.debug(f"Applied reading profile: {profile} -> {profile_mapping[profile].value}")
        
        # Create the config object
        config = BionicConfig.from_dict(config_dict)
        
        # Attach additional processing options as attributes for easy access
        if 'output_format' in kwargs:
            config._output_format = kwargs['output_format']
        if 'processing_strategy' in kwargs:
            config._processing_strategy = kwargs['processing_strategy']
        if 'preserve_formatting' in kwargs:
            config._preserve_formatting = kwargs['preserve_formatting']
        if 'skip_technical' in kwargs:
            config._skip_technical = kwargs['skip_technical']
        
        # Log final configuration for debugging
        self.logger.debug(f"Final processing config - Intensity: {config.bionic_intensity}, Mode: {config.processing_mode.value}")
        
        return config
    
    def _process_pdf(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
        """Process PDF file with advanced capabilities."""
        try:
            result = self.pdf_processor.process(input_path, config, file_info=file_info)
            
            # Add file_type to successful results (matches pattern from other processors)
            if result.get('success'):
                result['file_type'] = 'pdf'
            
            return result
        except Exception as e:
            raise PDFProcessingError(f"PDF processing failed: {str(e)}", file_path=input_path, original_error=e)
    
    def _process_docx(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
        """Process DOCX file."""
        try:
            # Use existing DOCX processor with config parameters
            result = process_docx_file(input_path)
            
            if result['success']:
                return {
                    'success': True,
                    'output_path': result['output_path'],
                    'file_type': 'docx',
                    'method_used': 'docx_standard',
                    'metadata': {
                        'original_size': file_info.get('size_bytes', 0),
                        'pages_processed': file_info.get('page_count', 0)
                    }
                }
            else:
                raise BionicProcessingError(result.get('error', 'Unknown DOCX processing error'))
                
        except Exception as e:
            raise BionicProcessingError(f"DOCX processing failed: {str(e)}", file_path=input_path, original_error=e)
    
    def _process_text(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
        """Process text file using modernized bionic processing."""
        try:
            # Read the text file
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get output format preference
            output_format = getattr(config, '_output_format', 'html')
            
            # Apply bionic formatting using the modernized system
            formatted_content = apply_bionic_formatting_to_text(
                content, 
                intensity=getattr(config, 'bionic_intensity', 0.4)
            )
            
            # Create output path with appropriate extension
            input_path_obj = Path(input_path)
            
            if output_format == 'html':
                output_filename = f"{input_path_obj.stem}_bionic.html"
                # Wrap plain text in basic HTML structure
                formatted_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bionic Reading - {input_path_obj.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 2rem; }}
        .bionic {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="bionic">{formatted_content}</div>
</body>
</html>"""
            elif output_format == 'markdown':
                output_filename = f"{input_path_obj.stem}_bionic.md"
                # Convert to markdown format (basic conversion)
                lines = formatted_content.split('\n')
                markdown_lines = []
                for line in lines:
                    if line.strip():
                        markdown_lines.append(line)
                    else:
                        markdown_lines.append('')
                formatted_content = '\n'.join(markdown_lines)
            else:  # plain_text or fallback
                output_filename = f"{input_path_obj.stem}_bionic.txt"
            
            output_path = input_path_obj.parent / output_filename
            
            # Save the formatted content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'file_type': 'txt',
                'method_used': f'text_modernized_{output_format}',
                'metadata': {
                    'original_size': file_info.get('size_bytes', 0),
                    'lines_processed': len(content.splitlines()),
                    'intensity_used': getattr(config, 'bionic_intensity', 0.4),
                    'output_format': output_format
                }
            }
                
        except Exception as e:
            raise BionicProcessingError(f"Text processing failed: {str(e)}", file_path=input_path, original_error=e)
    
    def _update_stats(self, processing_time: float, success: bool, error: Optional[str] = None):
        """Update processing statistics."""
        self.stats['files_processed'] += 1
        self.stats['processing_time_total'] += processing_time
        
        if not success:
            self.stats['errors_count'] += 1
            self.stats['last_error'] = error
    
    def process_batch(self, input_paths: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Process multiple files in batch.
        
        Args:
            input_paths: List of file paths to process
            **kwargs: Processing options
            
        Returns:
            List of processing results
        """
        results = []
        
        if self.config.enable_parallel_processing and len(input_paths) > 1:
            results = self._process_batch_parallel(input_paths, **kwargs)
        else:
            for path in input_paths:
                result = self.process_file(path, **kwargs)
                results.append(result)
        
        return results
    
    def _process_batch_parallel(self, input_paths: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Process files in parallel using threading."""
        import concurrent.futures
        
        max_workers = min(self.config.max_worker_threads, len(input_paths))
        results = [None] * len(input_paths)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_index = {
                executor.submit(self.process_file, path, **kwargs): i 
                for i, path in enumerate(input_paths)
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    results[index] = {
                        'success': False,
                        'error': str(e),
                        'file_path': input_paths[index]
                    }
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        if stats['files_processed'] > 0:
            stats['average_processing_time'] = stats['processing_time_total'] / stats['files_processed']
        else:
            stats['average_processing_time'] = 0.0
        
        return stats
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temporary directory: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported file types."""
        return get_config().supported_types.copy()
    
    @classmethod
    def is_supported_type(cls, file_path_or_type: str) -> bool:
        """Check if a file type is supported."""
        if os.path.exists(file_path_or_type):
            file_type = detect_file_type(file_path_or_type)
        else:
            file_type = file_path_or_type.lower().lstrip('.')
        
        return file_type in cls.get_supported_types()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup() 