"""
Document Structure Analyzer for Bionic Reading

Intelligent analysis of document hierarchy and structure to enable
context-aware bionic processing with appropriate intensity levels.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class DocumentElement(Enum):
    """Types of document elements for targeted processing."""
    HEADING = "heading"
    PARAGRAPH = "paragraph" 
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    CAPTION = "caption"
    QUOTE = "quote"
    CODE = "code"
    TECHNICAL_TERM = "technical_term"
    MATH_CONTENT = "math_content"
    REFERENCE = "reference"


class DocumentAnalyzer:
    """
    Analyzes document structure and content for intelligent bionic processing.
    """
    
    def __init__(self):
        """Initialize the document analyzer."""
        self.heading_patterns = [
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
            r'^\d+\.?\s+[A-Z]',   # Numbered headings
            r'^[A-Z][^.!?]*$',    # Title case without ending punctuation
        ]
        
        self.list_patterns = [
            r'^\s*[-•·]\s+',      # Bullet points
            r'^\s*\d+[\.\)]\s+',  # Numbered lists
            r'^\s*[a-zA-Z][\.\)]\s+',  # Lettered lists
        ]
        
        self.technical_patterns = [
            r'\b[A-Z]{2,}\b',     # Acronyms
            r'\b\w+\(\w*\)\b',    # Function calls
            r'\b\d+[a-zA-Z]+\b',  # Units (5kg, 10mph)
        ]
        
        self.quote_patterns = [
            r'^["\'].*["\']$',    # Quoted text
            r'^\s*>\s+',          # Markdown quotes
        ]
    
    def analyze_text_element(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a text element to determine its type and processing requirements.
        
        Args:
            text: Text to analyze
            context: Optional context information (font size, position, etc.)
            
        Returns:
            Analysis result with element type and processing recommendations
        """
        if not text or not text.strip():
            return {
                'element_type': DocumentElement.PARAGRAPH,
                'bionic_intensity': 0.0,
                'preserve_formatting': True,
                'should_process': False
            }
        
        clean_text = text.strip()
        element_type = self._classify_element(clean_text, context)
        
        return {
            'element_type': element_type,
            'bionic_intensity': self._get_intensity_for_element(element_type),
            'preserve_formatting': self._should_preserve_formatting(element_type),
            'should_process': self._should_process_element(element_type, clean_text),
            'special_handling': self._get_special_handling(element_type),
            'font_weight_multiplier': self._get_font_weight_multiplier(element_type)
        }
    
    def _classify_element(self, text: str, context: Optional[Dict] = None) -> DocumentElement:
        """
        Classify the type of document element.
        
        Args:
            text: Text to classify
            context: Optional context (font size, formatting, etc.)
            
        Returns:
            Classified document element type
        """
        # Check context clues first
        if context:
            font_size = context.get('font_size', 12)
            is_bold = context.get('is_bold', False)
            
            # Large font usually indicates heading
            if font_size > 16 or (font_size > 14 and is_bold):
                return DocumentElement.HEADING
        
        # Pattern-based classification
        for pattern in self.heading_patterns:
            if re.match(pattern, text):
                return DocumentElement.HEADING
        
        for pattern in self.list_patterns:
            if re.match(pattern, text):
                return DocumentElement.LIST_ITEM
        
        for pattern in self.quote_patterns:
            if re.match(pattern, text):
                return DocumentElement.QUOTE
        
        # Technical content detection
        if any(re.search(pattern, text) for pattern in self.technical_patterns):
            return DocumentElement.TECHNICAL_TERM
        
        # Math content detection
        if self._contains_math(text):
            return DocumentElement.MATH_CONTENT
        
        # Code detection
        if self._is_code_like(text):
            return DocumentElement.CODE
        
        # Table cell detection (short, structured text)
        if len(text) < 50 and '\t' in text:
            return DocumentElement.TABLE_CELL
        
        # Caption detection (often starts with Figure, Table, etc.)
        if re.match(r'^(Figure|Table|Chart|Diagram|Image)\s+\d+', text, re.IGNORECASE):
            return DocumentElement.CAPTION
        
        # Default to paragraph
        return DocumentElement.PARAGRAPH
    
    def _get_intensity_for_element(self, element_type: DocumentElement) -> float:
        """
        Get bionic intensity level for element type.
        
        Args:
            element_type: Type of document element
            
        Returns:
            Intensity level (0.0 to 1.0)
        """
        intensity_map = {
            DocumentElement.HEADING: 0.6,          # High visibility for headings
            DocumentElement.PARAGRAPH: 0.4,        # Optimal reading for body text
            DocumentElement.LIST_ITEM: 0.45,       # Slightly higher for lists
            DocumentElement.TABLE_CELL: 0.3,       # Subtle for tables
            DocumentElement.CAPTION: 0.3,          # Subtle for captions
            DocumentElement.QUOTE: 0.35,           # Moderate for quotes
            DocumentElement.CODE: 0.0,             # No processing for code
            DocumentElement.TECHNICAL_TERM: 0.0,   # Preserve technical terms
            DocumentElement.MATH_CONTENT: 0.0,     # Preserve math
            DocumentElement.REFERENCE: 0.2,        # Minimal for references
        }
        
        return intensity_map.get(element_type, 0.4)
    
    def _should_preserve_formatting(self, element_type: DocumentElement) -> bool:
        """
        Determine if original formatting should be preserved.
        
        Args:
            element_type: Type of document element
            
        Returns:
            True if formatting should be preserved
        """
        preserve_types = {
            DocumentElement.CODE,
            DocumentElement.TECHNICAL_TERM,
            DocumentElement.MATH_CONTENT,
            DocumentElement.TABLE_CELL
        }
        
        return element_type in preserve_types
    
    def _should_process_element(self, element_type: DocumentElement, text: str) -> bool:
        """
        Determine if element should receive bionic processing.
        
        Args:
            element_type: Type of document element
            text: Element text content
            
        Returns:
            True if element should be processed
        """
        # Don't process these types
        no_process_types = {
            DocumentElement.CODE,
            DocumentElement.TECHNICAL_TERM,
            DocumentElement.MATH_CONTENT
        }
        
        if element_type in no_process_types:
            return False
        
        # Don't process very short text
        if len(text.strip()) < 3:
            return False
        
        return True
    
    def _get_special_handling(self, element_type: DocumentElement) -> List[str]:
        """
        Get special handling requirements for element type.
        
        Args:
            element_type: Type of document element
            
        Returns:
            List of special handling requirements
        """
        handling_map = {
            DocumentElement.HEADING: ['preserve_case', 'increase_contrast'],
            DocumentElement.CODE: ['preserve_spacing', 'monospace_font'],
            DocumentElement.MATH_CONTENT: ['preserve_exactly', 'math_font'],
            DocumentElement.TABLE_CELL: ['preserve_alignment', 'minimal_changes'],
            DocumentElement.TECHNICAL_TERM: ['preserve_exactly'],
            DocumentElement.QUOTE: ['preserve_quotes', 'italic_emphasis'],
        }
        
        return handling_map.get(element_type, [])
    
    def _get_font_weight_multiplier(self, element_type: DocumentElement) -> float:
        """
        Get font weight multiplier for bionic formatting.
        
        Args:
            element_type: Type of document element
            
        Returns:
            Font weight multiplier (1.0 = normal)
        """
        weight_map = {
            DocumentElement.HEADING: 1.2,     # Bolder for headings
            DocumentElement.PARAGRAPH: 1.0,   # Normal for body text
            DocumentElement.LIST_ITEM: 1.0,   # Normal for lists
            DocumentElement.CAPTION: 0.9,     # Lighter for captions
            DocumentElement.QUOTE: 0.95,      # Slightly lighter for quotes
            DocumentElement.TABLE_CELL: 0.9,  # Lighter for tables
        }
        
        return weight_map.get(element_type, 1.0)
    
    def _contains_math(self, text: str) -> bool:
        """Check if text contains mathematical content."""
        math_patterns = [
            r'[=<>±∑∫∏√∞]',           # Math symbols
            r'\d+\s*[+\-*/]\s*\d+',   # Simple equations
            r'[a-zA-Z]\^?\d+',        # Variables with exponents
            r'\([^)]*[+\-*/][^)]*\)', # Expressions in parentheses
        ]
        
        return any(re.search(pattern, text) for pattern in math_patterns)
    
    def _is_code_like(self, text: str) -> bool:
        """Check if text appears to be code."""
        code_indicators = [
            r'\{.*\}',               # Curly braces
            r'function\s*\(',        # Function definitions
            r'if\s*\(',              # Conditional statements
            r'[a-zA-Z_]\w*\(\)',     # Function calls
            r'[<>]=?|!=|==',         # Comparison operators
        ]
        
        return any(re.search(pattern, text) for pattern in code_indicators)
    
    def analyze_document_structure(self, text_elements: List[Dict]) -> Dict[str, Any]:
        """
        Analyze overall document structure.
        
        Args:
            text_elements: List of text elements with content and metadata
            
        Returns:
            Document structure analysis
        """
        element_types = []
        total_elements = len(text_elements)
        
        for element in text_elements:
            text = element.get('text', '')
            context = element.get('context', {})
            analysis = self.analyze_text_element(text, context)
            element_types.append(analysis['element_type'])
        
        # Calculate document statistics
        type_counts = {}
        for element_type in element_types:
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        
        return {
            'total_elements': total_elements,
            'element_type_distribution': type_counts,
            'has_headings': DocumentElement.HEADING in element_types,
            'has_lists': DocumentElement.LIST_ITEM in element_types,
            'has_technical_content': DocumentElement.TECHNICAL_TERM in element_types,
            'has_math': DocumentElement.MATH_CONTENT in element_types,
            'recommended_processing': self._recommend_document_processing(type_counts),
            'complexity_score': self._calculate_complexity_score(type_counts, total_elements)
        }
    
    def _recommend_document_processing(self, type_counts: Dict) -> Dict[str, Any]:
        """
        Recommend processing approach based on document composition.
        
        Args:
            type_counts: Count of each element type
            
        Returns:
            Processing recommendations
        """
        total_elements = sum(type_counts.values())
        
        # Calculate ratios
        technical_ratio = (
            type_counts.get(DocumentElement.TECHNICAL_TERM, 0) + 
            type_counts.get(DocumentElement.MATH_CONTENT, 0) + 
            type_counts.get(DocumentElement.CODE, 0)
        ) / max(total_elements, 1)
        
        structured_ratio = (
            type_counts.get(DocumentElement.HEADING, 0) + 
            type_counts.get(DocumentElement.LIST_ITEM, 0) + 
            type_counts.get(DocumentElement.TABLE_CELL, 0)
        ) / max(total_elements, 1)
        
        return {
            'use_conservative_processing': technical_ratio > 0.3,
            'preserve_structure': structured_ratio > 0.2,
            'apply_smart_intensity': True,
            'recommended_intensity': self._calculate_recommended_intensity(technical_ratio),
            'special_modes': self._get_recommended_modes(type_counts)
        }
    
    def _calculate_complexity_score(self, type_counts: Dict, total_elements: int) -> float:
        """
        Calculate document complexity score.
        
        Args:
            type_counts: Count of each element type
            total_elements: Total number of elements
            
        Returns:
            Complexity score (0.0 to 1.0)
        """
        if total_elements == 0:
            return 0.0
        
        # Weight different element types
        complexity_weights = {
            DocumentElement.HEADING: 0.1,
            DocumentElement.PARAGRAPH: 0.2,
            DocumentElement.LIST_ITEM: 0.3,
            DocumentElement.TABLE_CELL: 0.4,
            DocumentElement.TECHNICAL_TERM: 0.8,
            DocumentElement.MATH_CONTENT: 0.9,
            DocumentElement.CODE: 1.0,
        }
        
        weighted_sum = sum(
            type_counts.get(element_type, 0) * weight
            for element_type, weight in complexity_weights.items()
        )
        
        return min(weighted_sum / total_elements, 1.0)
    
    def _calculate_recommended_intensity(self, technical_ratio: float) -> float:
        """
        Calculate recommended bionic intensity based on technical content ratio.
        
        Args:
            technical_ratio: Ratio of technical content in document
            
        Returns:
            Recommended intensity (0.0 to 1.0)
        """
        if technical_ratio > 0.5:
            return 0.2  # Very conservative for technical documents
        elif technical_ratio > 0.3:
            return 0.3  # Conservative for semi-technical documents
        elif technical_ratio > 0.1:
            return 0.4  # Standard for mixed documents
        else:
            return 0.5  # Full intensity for general documents
    
    def _get_recommended_modes(self, type_counts: Dict) -> List[str]:
        """
        Get recommended processing modes based on document content.
        
        Args:
            type_counts: Count of each element type
            
        Returns:
            List of recommended processing modes
        """
        modes = []
        
        if type_counts.get(DocumentElement.MATH_CONTENT, 0) > 0:
            modes.append('math_preservation')
        
        if type_counts.get(DocumentElement.CODE, 0) > 0:
            modes.append('code_preservation')
        
        if type_counts.get(DocumentElement.TABLE_CELL, 0) > 0:
            modes.append('table_aware')
        
        if type_counts.get(DocumentElement.HEADING, 0) > 0:
            modes.append('heading_enhancement')
        
        if not modes:
            modes.append('standard_processing')
        
        return modes 