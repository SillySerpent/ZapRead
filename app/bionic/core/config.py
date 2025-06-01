"""
Bionic Processor Configuration

Centralized configuration management for the bionic reading processor.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class LogLevel(Enum):
    """Logging levels for the bionic processor."""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProcessingMode(Enum):
    """Processing modes for different optimization strategies."""
    SPEED = "speed"          # Prioritize processing speed
    QUALITY = "quality"      # Prioritize output quality
    MEMORY = "memory"        # Optimize for low memory usage
    BALANCED = "balanced"    # Balance between speed and quality


class PDFMethod(Enum):
    """PDF processing methods."""
    MORPHING = "morphing"           # Use morphing for text replacement
    REDACTION = "redaction"         # Use redaction-based approach
    REPORTLAB = "reportlab"         # Use ReportLab reconstruction
    PYMUPDF4LLM = "pymupdf4llm"    # Use PyMuPDF4LLM for advanced analysis
    AUTO = "auto"                   # Automatically select best method


@dataclass
class BionicConfig:
    """Configuration settings for the bionic processor."""
    
    # File processing
    supported_types: List[str] = field(default_factory=lambda: ['pdf', 'docx', 'txt'])
    max_file_size_mb: int = 500
    processing_timeout_seconds: int = 300
    
    # PDF processing
    pdf_method: PDFMethod = PDFMethod.AUTO
    preserve_original_formatting: bool = True
    preserve_images: bool = True
    preserve_tables: bool = True
    enable_multi_column_detection: bool = True
    
    # Text processing
    bionic_intensity: float = 0.5  # 0.0 to 1.0, controls how much text is made bold
    preserve_math_expressions: bool = True
    preserve_code_blocks: bool = True
    respect_existing_formatting: bool = True
    
    # Performance
    processing_mode: ProcessingMode = ProcessingMode.BALANCED
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    chunk_size_mb: int = 10
    
    # Memory management
    enable_memory_monitoring: bool = True
    memory_limit_mb: int = 1024
    enable_temp_file_cleanup: bool = True
    temp_file_retention_hours: int = 24
    
    # Debugging and logging
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    save_debug_files: bool = False
    debug_output_dir: Optional[str] = None
    
    # Output settings
    output_format_fallbacks: List[str] = field(default_factory=lambda: ['html', 'txt'])
    preserve_file_metadata: bool = True
    add_processing_metadata: bool = True
    
    # Advanced features
    enable_experimental_features: bool = False
    custom_bionic_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._setup_logging()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not 0.0 <= self.bionic_intensity <= 1.0:
            raise ValueError("bionic_intensity must be between 0.0 and 1.0")
        
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.processing_timeout_seconds <= 0:
            raise ValueError("processing_timeout_seconds must be positive")
        
        if self.max_worker_threads <= 0:
            raise ValueError("max_worker_threads must be positive")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.value),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BionicConfig':
        """Create configuration from dictionary."""
        # Convert enum strings to enum values
        if 'log_level' in config_dict and isinstance(config_dict['log_level'], str):
            config_dict['log_level'] = LogLevel(config_dict['log_level'])
        
        if 'processing_mode' in config_dict and isinstance(config_dict['processing_mode'], str):
            config_dict['processing_mode'] = ProcessingMode(config_dict['processing_mode'])
        
        if 'pdf_method' in config_dict and isinstance(config_dict['pdf_method'], str):
            config_dict['pdf_method'] = PDFMethod(config_dict['pdf_method'])
        
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> 'BionicConfig':
        """Create configuration from environment variables."""
        config_dict = {}
        
        # Map environment variables to config keys
        env_mappings = {
            'BIONIC_DEBUG_MODE': ('debug_mode', lambda x: x.lower() == 'true'),
            'BIONIC_LOG_LEVEL': ('log_level', lambda x: LogLevel(x.upper())),
            'BIONIC_MAX_FILE_SIZE_MB': ('max_file_size_mb', int),
            'BIONIC_PROCESSING_MODE': ('processing_mode', lambda x: ProcessingMode(x.lower())),
            'BIONIC_PDF_METHOD': ('pdf_method', lambda x: PDFMethod(x.lower())),
            'BIONIC_INTENSITY': ('bionic_intensity', float),
            'BIONIC_TIMEOUT': ('processing_timeout_seconds', int),
        }
        
        for env_var, (config_key, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    config_dict[config_key] = converter(value)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid environment variable {env_var}={value}: {e}")
        
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    def update(self, **kwargs):
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
        
        self._validate_config()


# Default configuration instance
default_config = BionicConfig()


def get_config() -> BionicConfig:
    """Get the current configuration."""
    return default_config


def set_config(config: BionicConfig):
    """Set the global configuration."""
    global default_config
    default_config = config


def update_config(**kwargs):
    """Update the global configuration."""
    default_config.update(**kwargs) 