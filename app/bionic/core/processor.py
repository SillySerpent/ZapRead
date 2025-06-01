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
from ..processors.text_processor import process_text_file
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
            file_type = file_info['file_type']
            
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
            
            return {
                'success': False,
                'error': error_msg,
                'file_type': getattr(e, 'file_type', 'unknown'),
                'processing_time': processing_time,
                'file_path': input_path
            }
    
    def _create_processing_config(self, **kwargs) -> BionicConfig:
        """Create a processing-specific configuration."""
        # Create a copy of the current config
        config_dict = self.config.to_dict()
        
        # Override with provided kwargs
        config_dict.update(kwargs)
        
        return BionicConfig.from_dict(config_dict)
    
    def _process_pdf(self, input_path: str, config: BionicConfig, file_info: Dict) -> Dict[str, Any]:
        """Process PDF file with advanced capabilities."""
        try:
            return self.pdf_processor.process(input_path, config, file_info)
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
        """Process text file."""
        try:
            # Use existing text processor
            result = process_text_file(input_path)
            
            if result['success']:
                return {
                    'success': True,
                    'output_path': result['output_path'],
                    'file_type': 'txt',
                    'method_used': 'text_standard',
                    'metadata': {
                        'original_size': file_info.get('size_bytes', 0),
                        'lines_processed': file_info.get('line_count', 0)
                    }
                }
            else:
                raise BionicProcessingError(result.get('error', 'Unknown text processing error'))
                
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