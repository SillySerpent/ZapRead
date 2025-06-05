"""
Bionic Reading Utilities - Modernized System

Provides enhanced bionic reading utilities with intelligent document analysis,
configurable intensity management, multi-format output, and robust processing.
"""

import os
import tempfile
import magic
from typing import List, Tuple

from .character_classifier import (
    is_pure_letters,
    is_pure_numbers,
    is_mixed_alphanumeric,
    classify_text_type,
    should_apply_bionic_formatting
)

from .math_detector import (
    is_mathematical_expression,
    is_scientific_notation,
    is_equation,
    is_formula,
    contains_math_symbols,
    should_preserve_as_math
)

from .pattern_matcher import (
    get_word_pattern,
    get_math_patterns,
    parse_text_segments,
    split_preserving_math
)

from .text_formatter import (
    calculate_bionic_split,
    format_bionic_text,
    process_word_bionic,
    create_html_bionic_word,
    process_text_bionic_enhanced,
    apply_bionic_formatting_to_text
)

from .document_analyzer import DocumentAnalyzer, DocumentElement
from .intensity_manager import IntensityManager, ReadingProfile, IntensityLevel
from .output_formatter import OutputFormatterManager, OutputFormat, FormattingStyle
from .processing_pipeline import ProcessingPipeline, ProcessingConfig, ProcessingStrategy

# Debug settings
DEBUG = False

def debug_print(*args, **kwargs):
    """Print debug information only if DEBUG is enabled."""
    if DEBUG:
        print(*args, **kwargs)

def process_text_bionic(text):
    """Process text to create bionic reading format with bold prefixes."""
    return process_text_bionic_enhanced(text)

def detect_file_type(file_path):
    """Detect the file type of a given file."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        if file_type == 'text/plain':
            return 'txt'
        elif file_type == 'application/pdf':
            return 'pdf'
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                           'application/msword']:
            return 'docx'
        else:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.txt':
                return 'txt'
            elif ext == '.pdf':
                return 'pdf'
            elif ext in ['.docx', '.doc']:
                return 'docx'
            else:
                return 'unknown'
    except Exception:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            return 'txt'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.docx', '.doc']:
            return 'docx'
        else:
            return 'unknown'

def create_output_path(input_path, file_type, suffix="_bionic"):
    """Create an output path for processed files in the same directory as the input file."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    input_dir = os.path.dirname(input_path)
    
    if file_type == 'txt':
        extension = 'html'
    else:
        extension = file_type
        
    output_filename = f"{base_name}{suffix}.{extension}"
    output_path = os.path.join(input_dir, output_filename)
    
    return output_path

def process_text_html(text):
    """Process text for HTML bionic reading format."""
    if not text:
        return ""
    return apply_bionic_formatting_to_text(text, output_format='html')

def create_html_template(title, content):
    """Create a complete HTML document with bionic reading styling."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bionic Reading - {title}</title>
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
            color: #333;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        strong {{
            font-weight: bold;
            color: #2c3e50;
        }}
        pre {{
            white-space: pre-wrap;
            font-family: inherit;
            margin: 0;
        }}
        .math-content {{
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            color: #495057;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 0.8rem;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bionic Reading Format</h1>
        <h2>Original file: {title}</h2>
        {content}
        <div class="footer">
            <p>Processed with ZapRead Bionic Reading - Enhanced with Math Preservation</p>
        </div>
    </div>
</body>
</html>"""

# Legacy support - simple text formatting function
def apply_bionic_formatting_to_text(text: str, intensity: float = 0.4) -> str:
    """
    Apply bionic formatting to text (legacy compatibility function).
    
    Args:
        text: Text to format
        intensity: Bionic intensity (0.0 to 1.0)
        
    Returns:
        Formatted text with bionic reading enhancement
    """
    try:
        # Use the modern system for better results
        formatter = OutputFormatterManager()
        return formatter.format_text(text, intensity, OutputFormat.PLAIN_TEXT)
    except Exception:
        # Fallback to simple implementation
        import re
        
        if intensity <= 0 or not text.strip():
            return text
        
        words = re.findall(r'\b\w+\b|\W+', text)
        formatted_words = []
        
        for word in words:
            if re.match(r'\b\w+\b', word) and len(word) > 1:
                # Calculate characters to emphasize
                chars_to_emphasize = max(1, int(len(word) * intensity))
                
                # Create emphasis with uppercase
                emphasized_part = word[:chars_to_emphasize].upper()
                rest_part = word[chars_to_emphasize:]
                
                formatted_word = emphasized_part + rest_part
                formatted_words.append(formatted_word)
            else:
                formatted_words.append(word)
        
        return ''.join(formatted_words)


def get_bionic_word_parts(text: str, intensity: float = 0.4) -> List[Tuple[str, bool]]:
    """
    Get word parts for PDF processing with separate bold and regular parts.
    Fixed to properly respect user intensity settings.
    
    Args:
        text: Text to process
        intensity: Bionic intensity (0.0 to 1.0)
        
    Returns:
        List of tuples: [(text_part, is_bold), ...]
    """
    import re
    
    if intensity <= 0 or not text.strip():
        return [(text, False)]
    
    # Clamp intensity to valid range
    intensity = max(0.0, min(1.0, intensity))
    
    # Split text into words and non-words (spaces, punctuation)
    tokens = re.findall(r'\b\w+\b|\W+', text)
    parts = []
    
    for token in tokens:
        if re.match(r'\b\w+\b', token) and len(token) > 1:
            # Calculate characters to emphasize based on intensity
            # Use a more sophisticated calculation that respects user settings
            if intensity <= 0.3:
                # Low intensity: only first character for most words
                chars_to_emphasize = 1 if len(token) >= 3 else 0
            elif intensity <= 0.5:
                # Medium intensity: balanced approach
                chars_to_emphasize = max(1, int(len(token) * 0.4))
            elif intensity <= 0.7:
                # High intensity: more characters emphasized
                chars_to_emphasize = max(1, int(len(token) * 0.6))
            else:
                # Very high intensity: emphasize more for better effect
                chars_to_emphasize = max(2, int(len(token) * 0.7))
            
            # Ensure we don't emphasize the entire word
            chars_to_emphasize = min(chars_to_emphasize, len(token) - 1)
            
            # Split word into bold and regular parts
            if chars_to_emphasize > 0:
                bold_part = token[:chars_to_emphasize]
                regular_part = token[chars_to_emphasize:]
                
                if bold_part:
                    parts.append((bold_part, True))
                if regular_part:
                    parts.append((regular_part, False))
            else:
                # No bolding for very short words or very low intensity
                parts.append((token, False))
        else:
            # Keep spaces, punctuation, short words as-is
            parts.append((token, False))
    
    return parts


# Enhanced bionic processor function
def process_text_with_bionic_reading(text: str, 
                                   config: dict = None,
                                   output_format: str = "plain_text") -> dict:
    """
    Process text with enhanced bionic reading capabilities.
    
    Args:
        text: Text to process
        config: Processing configuration
        output_format: Desired output format
        
    Returns:
        Processing result dictionary
    """
    try:
        # Initialize pipeline with config
        pipeline_config = ProcessingConfig()
        
        if config:
            # Apply configuration overrides
            if 'intensity' in config:
                pipeline_config.default_intensity = config['intensity']
            if 'profile' in config:
                try:
                    pipeline_config.reading_profile = ReadingProfile(config['profile'])
                except ValueError:
                    pass
            if 'strategy' in config:
                try:
                    pipeline_config.strategy = ProcessingStrategy(config['strategy'])
                except ValueError:
                    pass
        
        # Set output format
        try:
            pipeline_config.output_format = OutputFormat(output_format)
        except ValueError:
            pipeline_config.output_format = OutputFormat.PLAIN_TEXT
        
        # Process text
        pipeline = ProcessingPipeline(pipeline_config)
        result = pipeline.process_text(text)
        
        return {
            'success': result.success,
            'output': result.output,
            'metadata': result.metadata,
            'warnings': result.warnings or [],
            'errors': result.errors or [],
            'processing_time': result.processing_time,
            'quality_score': result.quality_score
        }
        
    except Exception as e:
        # Fallback to simple processing
        return {
            'success': True,
            'output': apply_bionic_formatting_to_text(text),
            'metadata': {'fallback_used': True},
            'warnings': [],
            'errors': [f"Advanced processing failed: {str(e)}"],
            'processing_time': 0.0,
            'quality_score': 0.5
        }


# Export main classes and functions
__all__ = [
    'DocumentAnalyzer',
    'DocumentElement', 
    'IntensityManager',
    'ReadingProfile',
    'IntensityLevel',
    'OutputFormatterManager',
    'OutputFormat',
    'FormattingStyle',
    'ProcessingPipeline',
    'ProcessingConfig',
    'ProcessingStrategy',
    'apply_bionic_formatting_to_text',
    'get_bionic_word_parts',
    'process_text_with_bionic_reading'
] 