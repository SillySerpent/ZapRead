"""
Bionic Reading Configuration System

Provides comprehensive configuration management for the bionic processor
with user preferences, profiles, and validation.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict, field
import json
import os
import time
from pathlib import Path
import logging

from ..processors.utils.document_analyzer import DocumentElement
from ..processors.utils.intensity_manager import ReadingProfile
from ..processors.utils.output_formatter import OutputFormat, FormattingStyle
from ..processors.utils.processing_pipeline import ProcessingStrategy


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


@dataclass
class UserPreferences:
    """User-specific preferences for bionic reading."""
    # Reading preferences
    default_profile: ReadingProfile = ReadingProfile.ACCESSIBILITY
    preferred_output_format: OutputFormat = OutputFormat.PLAIN_TEXT
    default_intensity: float = 0.4
    
    # Visual preferences
    html_style: FormattingStyle = FormattingStyle.BOLD
    custom_css: Optional[str] = None
    font_size_adjustment: float = 1.0
    
    # Processing preferences
    processing_strategy: ProcessingStrategy = ProcessingStrategy.BALANCED
    enable_parallel_processing: bool = False
    max_processing_workers: int = 4
    enable_fallbacks: bool = True
    quality_threshold: float = 0.7
    
    # Document handling
    preserve_document_structure: bool = True
    skip_technical_content: bool = True
    skip_code_blocks: bool = True
    skip_math_content: bool = True
    
    # Performance preferences
    timeout_seconds: float = 30.0
    enable_caching: bool = True
    debug_mode: bool = False
    
    # Accessibility preferences
    high_contrast_mode: bool = False
    larger_emphasis: bool = False
    screen_reader_friendly: bool = False


@dataclass
class DocumentTypeConfig:
    """Configuration for specific document types."""
    document_type: str
    intensity_override: Optional[float] = None
    profile_override: Optional[ReadingProfile] = None
    output_format_override: Optional[OutputFormat] = None
    custom_element_intensities: Dict[DocumentElement, float] = field(default_factory=dict)
    processing_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    # Application settings
    app_name: str = "ZapRead Bionic Processor"
    version: str = "2.0.0"
    config_version: str = "1.0"
    
    # File handling
    max_file_size_mb: int = 100
    supported_formats: List[str] = field(default_factory=lambda: [
        'pdf', 'docx', 'txt', 'md', 'html'
    ])
    temp_directory: Optional[str] = None
    output_directory: Optional[str] = None
    
    # Security settings
    allow_custom_css: bool = True
    sanitize_html_output: bool = True
    enable_file_upload: bool = True
    
    # Performance settings
    max_concurrent_processes: int = 10
    cache_duration_hours: int = 24
    enable_monitoring: bool = False
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_performance_logging: bool = False


class BionicConfiguration:
    """
    Comprehensive configuration management for the bionic processor.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # Initialize default configurations
        self.user_preferences = UserPreferences()
        self.system_config = SystemConfig()
        self.document_type_configs: Dict[str, DocumentTypeConfig] = {}
        
        # Built-in profiles
        self._initialize_builtin_profiles()
        
        # Load configuration if file provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def _initialize_builtin_profiles(self):
        """Initialize built-in document type configurations."""
        # Academic/Research documents
        self.document_type_configs['academic'] = DocumentTypeConfig(
            document_type='academic',
            profile_override=ReadingProfile.TECHNICAL,
            intensity_override=0.3,
            custom_element_intensities={
                DocumentElement.HEADING: 0.5,
                DocumentElement.PARAGRAPH: 0.3,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.REFERENCE: 0.2,
                DocumentElement.MATH_CONTENT: 0.0
            },
            processing_hints={
                'preserve_citations': True,
                'careful_with_numbers': True,
                'preserve_technical_formatting': True
            }
        )
        
        # News/Blog articles
        self.document_type_configs['news'] = DocumentTypeConfig(
            document_type='news',
            profile_override=ReadingProfile.SPEED_READING,
            intensity_override=0.6,
            custom_element_intensities={
                DocumentElement.HEADING: 0.7,
                DocumentElement.PARAGRAPH: 0.6,
                DocumentElement.QUOTE: 0.5,
                DocumentElement.CAPTION: 0.4
            },
            processing_hints={
                'emphasize_headlines': True,
                'quick_reading_optimized': True
            }
        )
        
        # Technical documentation
        self.document_type_configs['technical'] = DocumentTypeConfig(
            document_type='technical',
            profile_override=ReadingProfile.TECHNICAL,
            intensity_override=0.25,
            custom_element_intensities={
                DocumentElement.HEADING: 0.4,
                DocumentElement.PARAGRAPH: 0.25,
                DocumentElement.CODE: 0.0,
                DocumentElement.TECHNICAL_TERM: 0.0,
                DocumentElement.LIST_ITEM: 0.3
            },
            processing_hints={
                'preserve_code_blocks': True,
                'careful_with_technical_terms': True,
                'preserve_formatting': True
            }
        )
        
        # Fiction/Literature
        self.document_type_configs['fiction'] = DocumentTypeConfig(
            document_type='fiction',
            profile_override=ReadingProfile.ACCESSIBILITY,
            intensity_override=0.45,
            custom_element_intensities={
                DocumentElement.PARAGRAPH: 0.45,
                DocumentElement.QUOTE: 0.4,
                DocumentElement.HEADING: 0.5
            },
            processing_hints={
                'preserve_dialogue_formatting': True,
                'maintain_reading_flow': True
            }
        )
    
    def get_config_for_document(self, document_type: Optional[str] = None,
                               document_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get complete configuration for processing a specific document.
        
        Args:
            document_type: Type of document (e.g., 'academic', 'news')
            document_metadata: Optional document metadata
            
        Returns:
            Complete configuration dictionary
        """
        # Start with user preferences
        config = {
            'user_preferences': asdict(self.user_preferences),
            'system_config': asdict(self.system_config)
        }
        
        # Apply document type overrides if specified
        if document_type and document_type in self.document_type_configs:
            doc_config = self.document_type_configs[document_type]
            
            # Override profile if specified
            if doc_config.profile_override:
                config['user_preferences']['default_profile'] = doc_config.profile_override.value
            
            # Override intensity if specified
            if doc_config.intensity_override is not None:
                config['user_preferences']['default_intensity'] = doc_config.intensity_override
            
            # Override output format if specified
            if doc_config.output_format_override:
                config['user_preferences']['preferred_output_format'] = doc_config.output_format_override.value
            
            # Add custom element intensities
            config['custom_element_intensities'] = {
                elem.value: intensity 
                for elem, intensity in doc_config.custom_element_intensities.items()
            }
            
            # Add processing hints
            config['processing_hints'] = doc_config.processing_hints
            
            # Store document type config
            config['document_type_config'] = asdict(doc_config)
        
        # Apply document metadata overrides
        if document_metadata:
            # Extract hints from metadata
            if 'is_technical' in document_metadata and document_metadata['is_technical']:
                if 'processing_hints' not in config:
                    config['processing_hints'] = {}
                config['processing_hints']['technical_content_detected'] = True
            
            if 'has_code' in document_metadata and document_metadata['has_code']:
                config['user_preferences']['skip_code_blocks'] = True
            
            if 'language' in document_metadata:
                config['document_language'] = document_metadata['language']
        
        return config
    
    def update_user_preference(self, key: str, value: Any) -> bool:
        """
        Update a user preference.
        
        Args:
            key: Preference key
            value: New value
            
        Returns:
            True if update successful
        """
        try:
            if hasattr(self.user_preferences, key):
                # Validate the value
                self._validate_preference_value(key, value)
                setattr(self.user_preferences, key, value)
                return True
            else:
                raise ConfigurationError(f"Unknown preference key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to update preference {key}: {str(e)}")
            return False
    
    def _validate_preference_value(self, key: str, value: Any):
        """
        Validate a preference value.
        
        Args:
            key: Preference key
            value: Value to validate
            
        Raises:
            ConfigurationError: If value is invalid
        """
        # Intensity validation
        if key in ['default_intensity', 'quality_threshold'] and isinstance(value, (int, float)):
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{key} must be between 0.0 and 1.0")
        
        # Worker count validation
        elif key == 'max_processing_workers' and isinstance(value, int):
            if value < 1 or value > 20:
                raise ConfigurationError("max_processing_workers must be between 1 and 20")
        
        # Timeout validation
        elif key == 'timeout_seconds' and isinstance(value, (int, float)):
            if value <= 0:
                raise ConfigurationError("timeout_seconds must be positive")
        
        # Font size validation
        elif key == 'font_size_adjustment' and isinstance(value, (int, float)):
            if not 0.5 <= value <= 3.0:
                raise ConfigurationError("font_size_adjustment must be between 0.5 and 3.0")
        
        # Enum validations
        elif key == 'default_profile':
            if isinstance(value, str):
                try:
                    ReadingProfile(value)
                except ValueError:
                    raise ConfigurationError(f"Invalid reading profile: {value}")
            elif not isinstance(value, ReadingProfile):
                raise ConfigurationError("default_profile must be a ReadingProfile")
        
        elif key == 'preferred_output_format':
            if isinstance(value, str):
                try:
                    OutputFormat(value)
                except ValueError:
                    raise ConfigurationError(f"Invalid output format: {value}")
            elif not isinstance(value, OutputFormat):
                raise ConfigurationError("preferred_output_format must be an OutputFormat")
        
        elif key == 'html_style':
            if isinstance(value, str):
                try:
                    FormattingStyle(value)
                except ValueError:
                    raise ConfigurationError(f"Invalid formatting style: {value}")
            elif not isinstance(value, FormattingStyle):
                raise ConfigurationError("html_style must be a FormattingStyle")
    
    def create_document_type_config(self, document_type: str, 
                                   config: DocumentTypeConfig) -> bool:
        """
        Create or update a document type configuration.
        
        Args:
            document_type: Document type identifier
            config: Document type configuration
            
        Returns:
            True if successful
        """
        try:
            self.document_type_configs[document_type] = config
            return True
        except Exception as e:
            self.logger.error(f"Failed to create document type config: {str(e)}")
            return False
    
    def get_available_profiles(self) -> Dict[str, str]:
        """
        Get available reading profiles with descriptions.
        
        Returns:
            Dictionary mapping profile names to descriptions
        """
        from ..processors.utils.intensity_manager import IntensityManager
        
        manager = IntensityManager()
        profiles = {}
        
        for profile in ReadingProfile:
            profiles[profile.value] = manager.get_profile_description(profile)
        
        return profiles
    
    def get_available_output_formats(self) -> List[str]:
        """
        Get available output formats.
        
        Returns:
            List of output format names
        """
        return [fmt.value for fmt in OutputFormat]
    
    def export_configuration(self) -> Dict[str, Any]:
        """
        Export complete configuration for backup or sharing.
        
        Returns:
            Complete configuration dictionary
        """
        return {
            'version': self.system_config.config_version,
            'exported_at': str(time.time()),
            'user_preferences': asdict(self.user_preferences),
            'system_config': asdict(self.system_config),
            'document_type_configs': {
                doc_type: asdict(config) 
                for doc_type, config in self.document_type_configs.items()
            }
        }
    
    def import_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Import configuration from dictionary.
        
        Args:
            config_data: Configuration data to import
            
        Returns:
            True if import successful
        """
        try:
            # Validate version compatibility
            config_version = config_data.get('version', '1.0')
            if config_version != self.system_config.config_version:
                self.logger.warning(f"Configuration version mismatch: {config_version}")
            
            # Import user preferences
            if 'user_preferences' in config_data:
                prefs_data = config_data['user_preferences']
                for key, value in prefs_data.items():
                    if hasattr(self.user_preferences, key):
                        try:
                            self._validate_preference_value(key, value)
                            setattr(self.user_preferences, key, value)
                        except ConfigurationError as e:
                            self.logger.warning(f"Skipping invalid preference {key}: {str(e)}")
            
            # Import system config
            if 'system_config' in config_data:
                sys_data = config_data['system_config']
                for key, value in sys_data.items():
                    if hasattr(self.system_config, key):
                        setattr(self.system_config, key, value)
            
            # Import document type configs
            if 'document_type_configs' in config_data:
                for doc_type, config_dict in config_data['document_type_configs'].items():
                    try:
                        doc_config = DocumentTypeConfig(**config_dict)
                        self.document_type_configs[doc_type] = doc_config
                    except Exception as e:
                        self.logger.warning(f"Failed to import config for {doc_type}: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {str(e)}")
            return False
    
    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save file (uses self.config_file if None)
            
        Returns:
            True if save successful
        """
        save_path = file_path or self.config_file
        if not save_path:
            self.logger.error("No configuration file path specified")
            return False
        
        try:
            config_data = self.export_configuration()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
    def load_from_file(self, file_path: Optional[str] = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if load successful
        """
        load_path = file_path or self.config_file
        if not load_path or not os.path.exists(load_path):
            self.logger.warning(f"Configuration file not found: {load_path}")
            return False
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            success = self.import_configuration(config_data)
            if success:
                self.config_file = load_path
                self.logger.info(f"Configuration loaded from {load_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.user_preferences = UserPreferences()
        self.system_config = SystemConfig()
        self.document_type_configs = {}
        self._initialize_builtin_profiles()
        self.logger.info("Configuration reset to defaults")
    
    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Validate user preferences
        try:
            prefs = self.user_preferences
            
            if not 0.0 <= prefs.default_intensity <= 1.0:
                issues.append("default_intensity must be between 0.0 and 1.0")
            
            if not 0.0 <= prefs.quality_threshold <= 1.0:
                issues.append("quality_threshold must be between 0.0 and 1.0")
            
            if prefs.max_processing_workers < 1:
                issues.append("max_processing_workers must be at least 1")
            
            if prefs.timeout_seconds <= 0:
                issues.append("timeout_seconds must be positive")
            
            if not 0.5 <= prefs.font_size_adjustment <= 3.0:
                issues.append("font_size_adjustment must be between 0.5 and 3.0")
        
        except Exception as e:
            issues.append(f"User preferences validation error: {str(e)}")
        
        # Validate system config
        try:
            sys_config = self.system_config
            
            if sys_config.max_file_size_mb < 1:
                issues.append("max_file_size_mb must be at least 1")
            
            if sys_config.max_concurrent_processes < 1:
                issues.append("max_concurrent_processes must be at least 1")
            
            if sys_config.cache_duration_hours < 0:
                issues.append("cache_duration_hours must be non-negative")
        
        except Exception as e:
            issues.append(f"System config validation error: {str(e)}")
        
        # Validate document type configs
        for doc_type, config in self.document_type_configs.items():
            try:
                if config.intensity_override is not None:
                    if not 0.0 <= config.intensity_override <= 1.0:
                        issues.append(f"Document type '{doc_type}' has invalid intensity_override")
                
                for elem, intensity in config.custom_element_intensities.items():
                    if not 0.0 <= intensity <= 1.0:
                        issues.append(f"Document type '{doc_type}' has invalid intensity for {elem}")
            
            except Exception as e:
                issues.append(f"Document type '{doc_type}' validation error: {str(e)}")
        
        return issues
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for display.
        
        Returns:
            Configuration summary
        """
        return {
            'profile': self.user_preferences.default_profile.value,
            'output_format': self.user_preferences.preferred_output_format.value,
            'intensity': self.user_preferences.default_intensity,
            'strategy': self.user_preferences.processing_strategy.value,
            'document_types_configured': len(self.document_type_configs),
            'fallbacks_enabled': self.user_preferences.enable_fallbacks,
            'parallel_processing': self.user_preferences.enable_parallel_processing,
            'debug_mode': self.user_preferences.debug_mode
        } 