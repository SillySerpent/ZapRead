import os
import re
import tempfile
import magic

# Import from new modular system
from .utils.character_classifier import should_apply_bionic_formatting
from .utils.math_detector import should_preserve_as_math
from .utils.text_formatter import process_text_bionic_enhanced, apply_bionic_formatting_to_text
from .utils.pattern_matcher import split_preserving_math

# Debug settings
DEBUG = False  # Set to False for production use

def debug_print(*args, **kwargs):
    """
    Print debug information only if DEBUG is enabled.
    """
    if DEBUG:
        print(*args, **kwargs)

def process_text_bionic(text):
    """
    Process text to create bionic reading format with bold prefixes.
    Enhanced version with proper math and character handling.
    
    Args:
        text (str): The text to process.
        
    Returns:
        tuple: (original_text, bold_part, regular_part) for reconstruction
    """
    # Use the enhanced processing function
    return process_text_bionic_enhanced(text)

def detect_file_type(file_path):
    """
    Detect the file type of a given file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        str: The detected file type (txt, pdf, docx, or unknown).
    """
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
            # Fallback to extension-based detection
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
        # Fallback to extension-based detection
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
    """
    Create a temporary output path for processed files.
    
    Args:
        input_path (str): Path to the input file.
        file_type (str): Type of the file (pdf, docx, txt).
        suffix (str): Suffix to add to the filename.
        
    Returns:
        tuple: (temp_dir, output_path)
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = tempfile.mkdtemp()
    
    if file_type == 'txt':
        extension = 'html'  # Text files are converted to HTML
    else:
        extension = file_type
        
    output_filename = f"{base_name}{suffix}.{extension}"
    output_path = os.path.join(temp_dir, output_filename)
    
    return temp_dir, output_path

def process_text_html(text):
    """
    Process text for HTML bionic reading format.
    Enhanced version with mathematical content preservation.
    
    Args:
        text (str): The text to process.
        
    Returns:
        str: HTML formatted text with bionic reading.
    """
    if not text:
        return ""
    
    # Use the enhanced text processing with math preservation
    return apply_bionic_formatting_to_text(text, output_format='html')

def create_html_template(title, content):
    """
    Create a complete HTML document with bionic reading styling.
    
    Args:
        title (str): Title for the HTML document.
        content (str): Processed content to include.
        
    Returns:
        str: Complete HTML document.
    """
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