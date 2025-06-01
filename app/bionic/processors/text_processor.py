import os
import re
from .utils import process_text_html, create_html_template, create_output_path, debug_print

def create_bionic_text_file(input_path):
    """
    Create a bionic reading text file using HTML formatting.
    
    Args:
        input_path (str): Path to the input text file.
        
    Returns:
        str: Path to the output HTML file.
    """
    try:
        # Read the text file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create output path
        output_path = create_output_path(input_path, 'txt')
        
        # Process content for HTML output
        html_content = _process_content_for_html(content)
        
        # Create complete HTML document
        html_document = create_html_template(
            os.path.basename(input_path), 
            html_content
        )
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_document)
        
        debug_print(f"Text file processed successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing text file: {e}")
        raise

def _process_content_for_html(content):
    """
    Process text content and format it appropriately for HTML display.
    Enhanced to preserve mathematical content.
    
    Args:
        content (str): Raw text content.
        
    Returns:
        str: HTML formatted content.
    """
    html_content = ""
    
    # Improved paragraph detection:
    # 1. Split by double newline (traditional paragraphs)
    # 2. Also handle single newline content with proper line breaks
    
    # First try to detect if this is a paragraph-based text or line-by-line text
    if content.count('\n\n') > 0:
        # This is likely a paragraph-based document
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Handle any single line breaks within paragraphs
                lines = paragraph.strip().split('\n')
                if len(lines) > 1:
                    # Paragraph has internal line breaks
                    processed_lines = [process_text_html(line) for line in lines if line.strip()]
                    html_content += f"        <p>{processed_lines[0]}"
                    for line in processed_lines[1:]:
                        html_content += f"<br>\n        {line}"
                    html_content += "</p>\n"
                else:
                    # Simple paragraph
                    processed_paragraph = process_text_html(paragraph.strip())
                    html_content += f"        <p>{processed_paragraph}</p>\n"
    else:
        # This is likely a line-by-line document
        lines = content.split('\n')
        if len(lines) > 1:
            html_content += "        <pre>\n"
            for line in lines:
                if line.strip():
                    processed_line = process_text_html(line)
                    html_content += f"        {processed_line}\n"
                else:
                    html_content += "\n"
            html_content += "        </pre>\n"
        else:
            # Single line document
            processed_content = process_text_html(content.strip())
            html_content += f"        <p>{processed_content}</p>\n"
    
    return html_content

def process_text_file(input_path):
    """
    Main entry point for text file processing.
    
    Args:
        input_path (str): Path to the input text file.
        
    Returns:
        dict: Processing result with success status and output path.
    """
    try:
        output_path = create_bionic_text_file(input_path)
        return {
            'success': True,
            'output_path': output_path,
            'file_type': 'txt'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_type': 'txt'
        } 