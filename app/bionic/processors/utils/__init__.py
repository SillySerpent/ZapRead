"""
Bionic Reading Utilities Module

This package contains modular utilities for bionic text processing.
"""

import os
import tempfile
import magic

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

def create_temp_output_path(input_path, file_type, suffix="_bionic"):
    """Create a temporary output path for processed files."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = tempfile.mkdtemp()
    
    if file_type == 'txt':
        extension = 'html'
    else:
        extension = file_type
        
    output_filename = f"{base_name}{suffix}.{extension}"
    output_path = os.path.join(temp_dir, output_filename)
    
    return temp_dir, output_path

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

# Backward compatibility exports
__all__ = [
    # Character classification
    'is_pure_letters',
    'is_pure_numbers', 
    'is_mixed_alphanumeric',
    'classify_text_type',
    'should_apply_bionic_formatting',
    
    # Math detection
    'is_mathematical_expression',
    'is_scientific_notation',
    'is_equation',
    'is_formula',
    'contains_math_symbols',
    'should_preserve_as_math',
    
    # Pattern matching
    'get_word_pattern',
    'get_math_patterns',
    'parse_text_segments',
    'split_preserving_math',
    
    # Text formatting
    'calculate_bionic_split',
    'format_bionic_text',
    'process_word_bionic',
    'create_html_bionic_word',
    
    # Main utility functions
    'debug_print',
    'process_text_bionic',
    'detect_file_type',
    'create_temp_output_path',
    'process_text_html',
    'create_html_template'
] 