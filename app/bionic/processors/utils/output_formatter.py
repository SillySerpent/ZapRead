"""
Multi-Format Output System for Bionic Reading

Provides various output formats while maintaining document structure and integrity.
Supports HTML, Markdown, plain text, and structured data formats.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
import re
import html
import json
from abc import ABC, abstractmethod


class OutputFormat(Enum):
    """Supported output formats."""
    PLAIN_TEXT = "plain_text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    STRUCTURED = "structured"


class FormattingStyle(Enum):
    """HTML/CSS formatting styles for bionic text."""
    BOLD = "bold"
    SEMI_BOLD = "semi_bold"
    COLOR_HIGHLIGHT = "color_highlight"
    UNDERLINE = "underline"
    BACKGROUND = "background"
    CUSTOM = "custom"


class BaseFormatter(ABC):
    """Base class for output formatters."""
    
    @abstractmethod
    def format_bionic_text(self, text: str, intensity: float, metadata: Dict[str, Any]) -> str:
        """Format text with bionic reading enhancement."""
        pass
    
    @abstractmethod
    def format_document(self, elements: List[Dict], metadata: Dict[str, Any]) -> str:
        """Format entire document."""
        pass


class PlainTextFormatter(BaseFormatter):
    """Plain text formatter with minimal visual enhancement."""
    
    def format_bionic_text(self, text: str, intensity: float, metadata: Dict[str, Any]) -> str:
        """
        Format text for plain text output with uppercase emphasis.
        
        Args:
            text: Text to format
            intensity: Bionic intensity (0.0 to 1.0)
            metadata: Element metadata
            
        Returns:
            Formatted plain text
        """
        if intensity <= 0 or not text.strip():
            return text
        
        words = self._split_words_safely(text)
        formatted_words = []
        
        for word_info in words:
            word = word_info['word']
            is_word = word_info['is_word']
            
            if is_word and len(word) > 1:
                # Calculate how many characters to emphasize
                chars_to_emphasize = max(1, int(len(word) * intensity))
                
                # Create emphasis with uppercase
                emphasized_part = word[:chars_to_emphasize].upper()
                rest_part = word[chars_to_emphasize:]
                
                formatted_word = emphasized_part + rest_part
                formatted_words.append(formatted_word)
            else:
                formatted_words.append(word)
        
        return ''.join(formatted_words)
    
    def format_document(self, elements: List[Dict], metadata: Dict[str, Any]) -> str:
        """
        Format entire document as plain text.
        
        Args:
            elements: List of document elements
            metadata: Document metadata
            
        Returns:
            Formatted plain text document
        """
        formatted_lines = []
        
        for element in elements:
            text = element.get('text', '')
            element_type = element.get('element_type', 'paragraph')
            intensity = element.get('intensity', 0.4)
            element_metadata = element.get('metadata', {})
            
            # Format the text
            formatted_text = self.format_bionic_text(text, intensity, element_metadata)
            
            # Add structural markers for plain text
            if element_type == 'heading':
                level = element_metadata.get('level', 1)
                prefix = '#' * level + ' '
                formatted_lines.append(prefix + formatted_text)
            elif element_type == 'list_item':
                formatted_lines.append('• ' + formatted_text)
            elif element_type == 'quote':
                formatted_lines.append('> ' + formatted_text)
            else:
                formatted_lines.append(formatted_text)
            
            formatted_lines.append('')  # Add spacing
        
        return '\n'.join(formatted_lines).strip()
    
    def _split_words_safely(self, text: str) -> List[Dict]:
        """Split text into words while preserving non-word characters."""
        pattern = r'(\b\w+\b)|([^\w\s]+|\s+)'
        matches = re.finditer(pattern, text)
        
        result = []
        for match in matches:
            word = match.group()
            is_word = bool(match.group(1))  # Group 1 is word characters
            result.append({'word': word, 'is_word': is_word})
        
        return result


class HTMLFormatter(BaseFormatter):
    """HTML formatter with CSS styling for bionic reading."""
    
    def __init__(self, style: FormattingStyle = FormattingStyle.BOLD, custom_css: Optional[str] = None):
        """
        Initialize HTML formatter.
        
        Args:
            style: Formatting style to use
            custom_css: Custom CSS for bionic text
        """
        self.style = style
        self.custom_css = custom_css
        self.css_classes = self._generate_css_classes()
    
    def format_bionic_text(self, text: str, intensity: float, metadata: Dict[str, Any]) -> str:
        """
        Format text with HTML/CSS bionic enhancement.
        
        Args:
            text: Text to format
            intensity: Bionic intensity (0.0 to 1.0)
            metadata: Element metadata
            
        Returns:
            HTML formatted text
        """
        if intensity <= 0 or not text.strip():
            return html.escape(text)
        
        words = self._split_words_safely(text)
        formatted_words = []
        
        for word_info in words:
            word = word_info['word']
            is_word = word_info['is_word']
            
            if is_word and len(word) > 1:
                # Calculate characters to emphasize
                chars_to_emphasize = max(1, int(len(word) * intensity))
                
                # Create HTML spans
                emphasized_part = html.escape(word[:chars_to_emphasize])
                rest_part = html.escape(word[chars_to_emphasize:])
                
                # Apply CSS class based on intensity
                css_class = self._get_css_class_for_intensity(intensity)
                
                formatted_word = f'<span class="{css_class}">{emphasized_part}</span>{rest_part}'
                formatted_words.append(formatted_word)
            else:
                formatted_words.append(html.escape(word))
        
        return ''.join(formatted_words)
    
    def format_document(self, elements: List[Dict], metadata: Dict[str, Any]) -> str:
        """
        Format entire document as HTML.
        
        Args:
            elements: List of document elements
            metadata: Document metadata
            
        Returns:
            Complete HTML document
        """
        title = metadata.get('title', 'Bionic Reading Document')
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            f'    <title>{html.escape(title)}</title>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <style>',
            self._get_document_css(),
            '    </style>',
            '</head>',
            '<body>',
            f'    <div class="bionic-document">',
        ]
        
        for element in elements:
            text = element.get('text', '')
            element_type = element.get('element_type', 'paragraph')
            intensity = element.get('intensity', 0.4)
            element_metadata = element.get('metadata', {})
            
            # Format the text
            formatted_text = self.format_bionic_text(text, intensity, element_metadata)
            
            # Wrap in appropriate HTML tags
            html_element = self._wrap_in_html_element(formatted_text, element_type, element_metadata)
            html_parts.append(f'        {html_element}')
        
        html_parts.extend([
            '    </div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _generate_css_classes(self) -> Dict[str, str]:
        """Generate CSS classes for different intensity levels."""
        if self.custom_css:
            return {'bionic': self.custom_css}
        
        base_styles = {
            FormattingStyle.BOLD: 'font-weight: bold;',
            FormattingStyle.SEMI_BOLD: 'font-weight: 600;',
            FormattingStyle.COLOR_HIGHLIGHT: 'color: #2563eb; font-weight: 500;',
            FormattingStyle.UNDERLINE: 'text-decoration: underline; font-weight: 500;',
            FormattingStyle.BACKGROUND: 'background-color: #dbeafe; padding: 0 1px;',
        }
        
        return {
            'bionic-low': base_styles.get(self.style, base_styles[FormattingStyle.BOLD]).replace('bold', '500'),
            'bionic-medium': base_styles.get(self.style, base_styles[FormattingStyle.BOLD]),
            'bionic-high': base_styles.get(self.style, base_styles[FormattingStyle.BOLD]).replace('500', '700').replace('bold', '800'),
        }
    
    def _get_css_class_for_intensity(self, intensity: float) -> str:
        """Get appropriate CSS class for intensity level."""
        if intensity < 0.3:
            return 'bionic-low'
        elif intensity < 0.6:
            return 'bionic-medium'
        else:
            return 'bionic-high'
    
    def _get_document_css(self) -> str:
        """Generate complete CSS for the document."""
        css_rules = []
        
        # Base document styles
        css_rules.append('''
        .bionic-document {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        ''')
        
        # Bionic reading styles
        for class_name, style in self.css_classes.items():
            css_rules.append(f'.{class_name} {{ {style} }}')
        
        # Element-specific styles
        css_rules.append('''
        .bionic-document h1, .bionic-document h2, .bionic-document h3,
        .bionic-document h4, .bionic-document h5, .bionic-document h6 {
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        
        .bionic-document p {
            margin-bottom: 1em;
        }
        
        .bionic-document ul, .bionic-document ol {
            margin-bottom: 1em;
            padding-left: 2em;
        }
        
        .bionic-document blockquote {
            border-left: 4px solid #ddd;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
        }
        
        .bionic-document table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        
        .bionic-document td, .bionic-document th {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        ''')
        
        return '\n'.join(css_rules)
    
    def _wrap_in_html_element(self, formatted_text: str, element_type: str, metadata: Dict) -> str:
        """Wrap formatted text in appropriate HTML element."""
        if element_type == 'heading':
            level = min(6, max(1, metadata.get('level', 1)))
            return f'<h{level}>{formatted_text}</h{level}>'
        elif element_type == 'paragraph':
            return f'<p>{formatted_text}</p>'
        elif element_type == 'list_item':
            return f'<li>{formatted_text}</li>'
        elif element_type == 'quote':
            return f'<blockquote>{formatted_text}</blockquote>'
        elif element_type == 'table_cell':
            return f'<td>{formatted_text}</td>'
        elif element_type == 'code':
            return f'<code>{formatted_text}</code>'
        else:
            return f'<div>{formatted_text}</div>'
    
    def _split_words_safely(self, text: str) -> List[Dict]:
        """Split text into words while preserving HTML structure."""
        # More sophisticated word splitting that handles existing HTML
        pattern = r'(\b\w+\b)|([^\w\s]+|\s+)'
        matches = re.finditer(pattern, text)
        
        result = []
        for match in matches:
            word = match.group()
            is_word = bool(match.group(1))
            result.append({'word': word, 'is_word': is_word})
        
        return result


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter with bionic reading enhancement."""
    
    def format_bionic_text(self, text: str, intensity: float, metadata: Dict[str, Any]) -> str:
        """
        Format text with Markdown bionic enhancement.
        
        Args:
            text: Text to format
            intensity: Bionic intensity (0.0 to 1.0)
            metadata: Element metadata
            
        Returns:
            Markdown formatted text
        """
        if intensity <= 0 or not text.strip():
            return text
        
        words = self._split_words_safely(text)
        formatted_words = []
        
        for word_info in words:
            word = word_info['word']
            is_word = word_info['is_word']
            
            if is_word and len(word) > 1:
                # Calculate characters to emphasize
                chars_to_emphasize = max(1, int(len(word) * intensity))
                
                # Use bold markdown for emphasis
                emphasized_part = word[:chars_to_emphasize]
                rest_part = word[chars_to_emphasize:]
                
                formatted_word = f'**{emphasized_part}**{rest_part}'
                formatted_words.append(formatted_word)
            else:
                formatted_words.append(word)
        
        return ''.join(formatted_words)
    
    def format_document(self, elements: List[Dict], metadata: Dict[str, Any]) -> str:
        """
        Format entire document as Markdown.
        
        Args:
            elements: List of document elements
            metadata: Document metadata
            
        Returns:
            Markdown formatted document
        """
        markdown_lines = []
        
        # Add title if available
        title = metadata.get('title')
        if title:
            markdown_lines.append(f'# {title}')
            markdown_lines.append('')
        
        for element in elements:
            text = element.get('text', '')
            element_type = element.get('element_type', 'paragraph')
            intensity = element.get('intensity', 0.4)
            element_metadata = element.get('metadata', {})
            
            # Format the text
            formatted_text = self.format_bionic_text(text, intensity, element_metadata)
            
            # Add Markdown formatting based on element type
            if element_type == 'heading':
                level = element_metadata.get('level', 1)
                prefix = '#' * level + ' '
                markdown_lines.append(prefix + formatted_text)
            elif element_type == 'list_item':
                markdown_lines.append(f'- {formatted_text}')
            elif element_type == 'quote':
                markdown_lines.append(f'> {formatted_text}')
            elif element_type == 'code':
                markdown_lines.append(f'`{text}`')  # Don't apply bionic to code
            else:
                markdown_lines.append(formatted_text)
            
            markdown_lines.append('')  # Add spacing
        
        return '\n'.join(markdown_lines).strip()
    
    def _split_words_safely(self, text: str) -> List[Dict]:
        """Split text into words while preserving Markdown structure."""
        pattern = r'(\b\w+\b)|([^\w\s]+|\s+)'
        matches = re.finditer(pattern, text)
        
        result = []
        for match in matches:
            word = match.group()
            is_word = bool(match.group(1))
            result.append({'word': word, 'is_word': is_word})
        
        return result


class JSONFormatter(BaseFormatter):
    """JSON formatter for structured bionic reading data."""
    
    def format_bionic_text(self, text: str, intensity: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format text as structured JSON data.
        
        Args:
            text: Text to format
            intensity: Bionic intensity (0.0 to 1.0)
            metadata: Element metadata
            
        Returns:
            JSON structure with bionic data
        """
        if intensity <= 0 or not text.strip():
            return {
                'original_text': text,
                'bionic_text': text,
                'words': [],
                'intensity': intensity,
                'processed': False
            }
        
        words = self._split_words_safely(text)
        bionic_words = []
        formatted_parts = []
        
        for word_info in words:
            word = word_info['word']
            is_word = word_info['is_word']
            
            if is_word and len(word) > 1:
                chars_to_emphasize = max(1, int(len(word) * intensity))
                emphasized_part = word[:chars_to_emphasize]
                rest_part = word[chars_to_emphasize:]
                
                word_data = {
                    'original': word,
                    'emphasized': emphasized_part,
                    'rest': rest_part,
                    'intensity': intensity,
                    'position': len(bionic_words)
                }
                bionic_words.append(word_data)
                formatted_parts.append(emphasized_part.upper() + rest_part)
            else:
                formatted_parts.append(word)
        
        return {
            'original_text': text,
            'bionic_text': ''.join(formatted_parts),
            'words': bionic_words,
            'intensity': intensity,
            'processed': True,
            'word_count': len([w for w in words if w['is_word']]),
            'metadata': metadata
        }
    
    def format_document(self, elements: List[Dict], metadata: Dict[str, Any]) -> str:
        """
        Format entire document as JSON.
        
        Args:
            elements: List of document elements
            metadata: Document metadata
            
        Returns:
            JSON formatted document
        """
        document_data = {
            'metadata': metadata,
            'processing_info': {
                'total_elements': len(elements),
                'processed_elements': 0,
                'average_intensity': 0.0
            },
            'elements': []
        }
        
        total_intensity = 0
        processed_count = 0
        
        for i, element in enumerate(elements):
            text = element.get('text', '')
            element_type = element.get('element_type', 'paragraph')
            intensity = element.get('intensity', 0.4)
            element_metadata = element.get('metadata', {})
            
            # Format the text
            formatted_data = self.format_bionic_text(text, intensity, element_metadata)
            
            element_data = {
                'index': i,
                'type': element_type,
                'bionic_data': formatted_data,
                'metadata': element_metadata
            }
            
            document_data['elements'].append(element_data)
            
            if formatted_data['processed']:
                processed_count += 1
                total_intensity += intensity
        
        # Update processing info
        document_data['processing_info']['processed_elements'] = processed_count
        if processed_count > 0:
            document_data['processing_info']['average_intensity'] = total_intensity / processed_count
        
        return json.dumps(document_data, indent=2, ensure_ascii=False)
    
    def _split_words_safely(self, text: str) -> List[Dict]:
        """Split text into words for JSON processing."""
        pattern = r'(\b\w+\b)|([^\w\s]+|\s+)'
        matches = re.finditer(pattern, text)
        
        result = []
        for match in matches:
            word = match.group()
            is_word = bool(match.group(1))
            result.append({'word': word, 'is_word': is_word})
        
        return result


class OutputFormatterManager:
    """
    Manages multiple output formatters and provides unified interface.
    """
    
    def __init__(self):
        """Initialize the formatter manager."""
        self.formatters = {
            OutputFormat.PLAIN_TEXT: PlainTextFormatter(),
            OutputFormat.HTML: HTMLFormatter(),
            OutputFormat.MARKDOWN: MarkdownFormatter(),
            OutputFormat.JSON: JSONFormatter(),
        }
    
    def format_text(self, text: str, intensity: float, output_format: OutputFormat,
                   metadata: Optional[Dict[str, Any]] = None) -> Union[str, Dict]:
        """
        Format text in specified output format.
        
        Args:
            text: Text to format
            intensity: Bionic intensity (0.0 to 1.0)
            output_format: Desired output format
            metadata: Optional metadata
            
        Returns:
            Formatted text in specified format
        """
        if output_format not in self.formatters:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        formatter = self.formatters[output_format]
        return formatter.format_bionic_text(text, intensity, metadata or {})
    
    def format_document(self, elements: List[Dict], output_format: OutputFormat,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Format entire document in specified format.
        
        Args:
            elements: List of document elements
            output_format: Desired output format
            metadata: Document metadata
            
        Returns:
            Formatted document
        """
        if output_format not in self.formatters:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        formatter = self.formatters[output_format]
        return formatter.format_document(elements, metadata or {})
    
    def get_supported_formats(self) -> List[OutputFormat]:
        """
        Get list of supported output formats.
        
        Returns:
            List of supported formats
        """
        return list(self.formatters.keys())
    
    def set_html_style(self, style: FormattingStyle, custom_css: Optional[str] = None):
        """
        Configure HTML formatter style.
        
        Args:
            style: Formatting style to use
            custom_css: Optional custom CSS
        """
        self.formatters[OutputFormat.HTML] = HTMLFormatter(style, custom_css)
    
    def add_custom_formatter(self, format_name: str, formatter: BaseFormatter):
        """
        Add custom formatter.
        
        Args:
            format_name: Name for the custom format
            formatter: Custom formatter instance
        """
        # Convert string to enum if needed
        try:
            format_enum = OutputFormat(format_name)
        except ValueError:
            # Create dynamic enum member (not recommended for production)
            format_enum = format_name
        
        self.formatters[format_enum] = formatter 