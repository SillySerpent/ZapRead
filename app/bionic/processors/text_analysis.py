"""
Text Analysis and Bionic Formatting for Advanced PDF Processing

Provides intelligent text analysis and bionic reading formatting with
configurable algorithms and linguistic analysis capabilities.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
import unicodedata

from ..core.config import BionicConfig


logger = logging.getLogger(__name__)


class TextType(Enum):
    """Types of text content for different processing strategies."""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TITLE = "title"
    CAPTION = "caption"
    QUOTE = "quote"
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    FOOTER = "footer"
    HEADER = "header"


class BionicAlgorithm(Enum):
    """Different bionic reading algorithms."""
    STANDARD = "standard"  # First half of words
    ADAPTIVE = "adaptive"  # Varies by word length
    LINGUISTIC = "linguistic"  # Based on syllable structure
    FREQUENCY = "frequency"  # Based on word frequency
    MIXED = "mixed"  # Combination approach


class TextAnalyzer:
    """
    Advanced text analyzer for bionic reading preparation.
    
    Analyzes text content to determine optimal bionic formatting
    strategies based on text type, language, and structure.
    """
    
    def __init__(self, config: BionicConfig):
        """
        Initialize text analyzer.
        
        Args:
            config: Configuration object with analysis settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Word frequency data (simplified - in production, use actual language models)
        self.common_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
            'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
            'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
            'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their'
        }
        
        # Sentence ending patterns
        self.sentence_endings = re.compile(r'[.!?]+\s*')
        
        # Word boundary patterns
        self.word_pattern = re.compile(r'\b\w+\b')
        
    def analyze_text(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze text content for optimal bionic formatting.
        
        Args:
            text: Text content to analyze
            context: Optional context information (font, size, position, etc.)
            
        Returns:
            Analysis results with formatting recommendations
        """
        if not text or not text.strip():
            return {
                'text_type': TextType.PARAGRAPH,
                'algorithm': BionicAlgorithm.STANDARD,
                'confidence': 0.0,
                'word_count': 0,
                'should_process': False,
                'recommendations': {}
            }
        
        analysis = {
            'original_text': text,
            'cleaned_text': self._clean_text(text),
            'word_count': 0,
            'sentence_count': 0,
            'avg_word_length': 0.0,
            'complexity_score': 0.0,
            'text_type': TextType.PARAGRAPH,
            'algorithm': BionicAlgorithm.STANDARD,
            'confidence': 0.0,
            'should_process': True,
            'recommendations': {}
        }
        
        try:
            # Basic text statistics
            words = self._extract_words(analysis['cleaned_text'])
            analysis['word_count'] = len(words)
            analysis['sentence_count'] = len(self.sentence_endings.split(text))
            
            if words:
                analysis['avg_word_length'] = sum(len(word) for word in words) / len(words)
            
            # Determine text type based on context and content
            analysis['text_type'] = self._classify_text_type(text, context)
            
            # Calculate complexity score
            analysis['complexity_score'] = self._calculate_complexity(words, text)
            
            # Recommend processing algorithm
            algorithm_result = self._recommend_algorithm(analysis, context)
            analysis['algorithm'] = algorithm_result['algorithm']
            analysis['confidence'] = algorithm_result['confidence']
            
            # Determine if text should be processed
            analysis['should_process'] = self._should_process_text(analysis)
            
            # Generate processing recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
        except Exception as e:
            self.logger.warning(f"Text analysis failed: {e}")
            analysis['should_process'] = False
        
        return analysis
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis."""
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text."""
        words = self.word_pattern.findall(text.lower())
        return [word for word in words if len(word) > 0]
    
    def _classify_text_type(self, text: str, context: Optional[Dict] = None) -> TextType:
        """Classify text type based on content and context."""
        text_lower = text.lower().strip()
        
        # Use context if available
        if context:
            font_size = context.get('font_size', 12)
            font_flags = context.get('font_flags', 0)
            
            # Large font size suggests heading
            if font_size > 16:
                return TextType.HEADING
            elif font_size > 14:
                return TextType.TITLE
            
            # Bold text might be heading
            if font_flags & 16:  # Bold flag
                if len(text.split()) <= 10:
                    return TextType.HEADING
        
        # Content-based classification
        if len(text) < 50 and not text.endswith('.'):
            return TextType.HEADING
        
        if text.startswith('•') or text.startswith('-') or re.match(r'^\d+\.', text):
            return TextType.LIST_ITEM
        
        if text.startswith('"') and text.endswith('"'):
            return TextType.QUOTE
        
        if len(text.split()) < 20:
            return TextType.CAPTION
        
        return TextType.PARAGRAPH
    
    def _calculate_complexity(self, words: List[str], text: str) -> float:
        """Calculate text complexity score (0-1)."""
        if not words:
            return 0.0
        
        factors = []
        
        # Average word length factor
        avg_length = sum(len(word) for word in words) / len(words)
        length_factor = min(avg_length / 8.0, 1.0)  # Normalize to 0-1
        factors.append(length_factor)
        
        # Uncommon words factor
        uncommon_count = sum(1 for word in words if word not in self.common_words)
        uncommon_factor = uncommon_count / len(words) if words else 0
        factors.append(uncommon_factor)
        
        # Sentence length factor
        sentences = self.sentence_endings.split(text)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            sentence_factor = min(avg_sentence_length / 20.0, 1.0)  # Normalize to 0-1
            factors.append(sentence_factor)
        
        # Special characters factor
        special_chars = len(re.findall(r'[^\w\s.,!?;:]', text))
        special_factor = min(special_chars / len(text), 0.3) if text else 0
        factors.append(special_factor)
        
        # Calculate weighted average
        weights = [0.3, 0.3, 0.3, 0.1]
        complexity = sum(f * w for f, w in zip(factors, weights))
        
        return min(complexity, 1.0)
    
    def _recommend_algorithm(self, analysis: Dict, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Recommend bionic reading algorithm based on analysis."""
        text_type = analysis['text_type']
        complexity = analysis['complexity_score']
        word_count = analysis['word_count']
        
        confidence = 0.8  # Default confidence
        
        # Algorithm selection logic
        if text_type in [TextType.HEADING, TextType.TITLE]:
            algorithm = BionicAlgorithm.STANDARD
            confidence = 0.9
        elif text_type == TextType.LIST_ITEM:
            algorithm = BionicAlgorithm.ADAPTIVE
            confidence = 0.8
        elif complexity > 0.7:
            algorithm = BionicAlgorithm.LINGUISTIC
            confidence = 0.7
        elif word_count > 50:
            algorithm = BionicAlgorithm.MIXED
            confidence = 0.8
        else:
            algorithm = BionicAlgorithm.STANDARD
            confidence = 0.8
        
        # Adjust based on configuration
        config_algorithm = getattr(self.config, 'bionic_algorithm', None)
        if config_algorithm and isinstance(config_algorithm, BionicAlgorithm):
            algorithm = config_algorithm
            confidence = 0.9
        
        return {
            'algorithm': algorithm,
            'confidence': confidence,
            'reason': f"Selected {algorithm.value} for {text_type.value} with complexity {complexity:.2f}"
        }
    
    def _should_process_text(self, analysis: Dict) -> bool:
        """Determine if text should be processed for bionic reading."""
        # Skip very short text
        if analysis['word_count'] < 2:
            return False
        
        # Skip text that's mostly numbers or special characters
        text = analysis['cleaned_text']
        if len(re.findall(r'\w', text)) / len(text) < 0.5:
            return False
        
        # Skip if text is mostly uppercase (might be an acronym)
        if text.isupper() and len(text) < 20:
            return False
        
        return True
    
    def _generate_recommendations(self, analysis: Dict) -> Dict[str, Any]:
        """Generate processing recommendations."""
        recommendations = {
            'intensity': 'medium',
            'preserve_formatting': True,
            'word_threshold': 3,
            'special_handling': []
        }
        
        text_type = analysis['text_type']
        complexity = analysis['complexity_score']
        
        # Adjust intensity based on text type
        if text_type in [TextType.HEADING, TextType.TITLE]:
            recommendations['intensity'] = 'high'
        elif complexity > 0.7:
            recommendations['intensity'] = 'low'
        elif analysis['word_count'] > 100:
            recommendations['intensity'] = 'medium'
        
        # Special handling recommendations
        if text_type == TextType.QUOTE:
            recommendations['special_handling'].append('preserve_quotes')
        
        if analysis['word_count'] > 200:
            recommendations['special_handling'].append('progressive_intensity')
        
        return recommendations


class BionicFormatter:
    """
    Advanced bionic text formatter with multiple algorithms.
    
    Applies bionic reading formatting to text using various algorithms
    optimized for different content types and reading preferences.
    """
    
    def __init__(self, config: BionicConfig):
        """
        Initialize bionic formatter.
        
        Args:
            config: Configuration object with formatting settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.text_analyzer = TextAnalyzer(config)
        
        # Formatting settings
        self.intensity = getattr(config, 'bionic_intensity', 0.5)
        self.min_word_length = getattr(config, 'min_word_length', 3)
        self.preserve_case = getattr(config, 'preserve_case', True)
        
        # HTML/markup settings
        self.bold_tag_open = '<b>'
        self.bold_tag_close = '</b>'
        
        # Syllable patterns (simplified)
        self.vowels = 'aeiouAEIOU'
        self.consonant_clusters = ['th', 'ch', 'sh', 'ph', 'wh', 'ck', 'ng']
    
    def format_text(self, text: str, algorithm: Optional[BionicAlgorithm] = None,
                   context: Optional[Dict] = None) -> str:
        """
        Format text for bionic reading.
        
        Args:
            text: Text to format
            algorithm: Specific algorithm to use (optional)
            context: Additional context for formatting decisions
            
        Returns:
            Formatted text with bionic reading markup
        """
        if not text or not text.strip():
            return text
        
        try:
            # Analyze text if algorithm not specified
            if algorithm is None:
                analysis = self.text_analyzer.analyze_text(text, context)
                if not analysis['should_process']:
                    return text
                algorithm = analysis['algorithm']
            
            # Apply formatting based on algorithm
            if algorithm == BionicAlgorithm.STANDARD:
                return self._format_standard(text)
            elif algorithm == BionicAlgorithm.ADAPTIVE:
                return self._format_adaptive(text)
            elif algorithm == BionicAlgorithm.LINGUISTIC:
                return self._format_linguistic(text)
            elif algorithm == BionicAlgorithm.FREQUENCY:
                return self._format_frequency(text)
            elif algorithm == BionicAlgorithm.MIXED:
                return self._format_mixed(text)
            else:
                return self._format_standard(text)
                
        except Exception as e:
            self.logger.warning(f"Text formatting failed: {e}")
            return text
    
    def _format_standard(self, text: str) -> str:
        """Standard bionic formatting - bold first half of words."""
        def format_word(match):
            word = match.group(0)
            if len(word) < self.min_word_length:
                return word
            
            split_point = max(1, len(word) // 2)
            bold_part = word[:split_point]
            regular_part = word[split_point:]
            
            return f"{self.bold_tag_open}{bold_part}{self.bold_tag_close}{regular_part}"
        
        return re.sub(r'\b\w+\b', format_word, text)
    
    def _format_adaptive(self, text: str) -> str:
        """Adaptive formatting - varies bold portion by word length."""
        def format_word(match):
            word = match.group(0)
            if len(word) < self.min_word_length:
                return word
            
            # Adaptive split based on word length
            if len(word) <= 3:
                split_point = 1
            elif len(word) <= 5:
                split_point = 2
            elif len(word) <= 8:
                split_point = len(word) // 2
            else:
                split_point = max(3, int(len(word) * 0.4))
            
            bold_part = word[:split_point]
            regular_part = word[split_point:]
            
            return f"{self.bold_tag_open}{bold_part}{self.bold_tag_close}{regular_part}"
        
        return re.sub(r'\b\w+\b', format_word, text)
    
    def _format_linguistic(self, text: str) -> str:
        """Linguistic formatting - based on syllable structure."""
        def format_word(match):
            word = match.group(0)
            if len(word) < self.min_word_length:
                return word
            
            # Find syllable break
            split_point = self._find_syllable_break(word)
            
            bold_part = word[:split_point]
            regular_part = word[split_point:]
            
            return f"{self.bold_tag_open}{bold_part}{self.bold_tag_close}{regular_part}"
        
        return re.sub(r'\b\w+\b', format_word, text)
    
    def _format_frequency(self, text: str) -> str:
        """Frequency-based formatting - more bold for common words."""
        def format_word(match):
            word = match.group(0)
            if len(word) < self.min_word_length:
                return word
            
            # Check if word is common
            is_common = word.lower() in self.text_analyzer.common_words
            
            if is_common:
                # More bold for common words
                split_point = max(1, int(len(word) * 0.6))
            else:
                # Less bold for uncommon words
                split_point = max(1, int(len(word) * 0.3))
            
            bold_part = word[:split_point]
            regular_part = word[split_point:]
            
            return f"{self.bold_tag_open}{bold_part}{self.bold_tag_close}{regular_part}"
        
        return re.sub(r'\b\w+\b', format_word, text)
    
    def _format_mixed(self, text: str) -> str:
        """Mixed approach combining multiple strategies."""
        def format_word(match):
            word = match.group(0)
            if len(word) < self.min_word_length:
                return word
            
            # Use different strategies based on word characteristics
            word_lower = word.lower()
            
            if word_lower in self.text_analyzer.common_words:
                # Frequency-based for common words
                split_point = max(1, int(len(word) * 0.6))
            elif len(word) > 8:
                # Linguistic for long words
                split_point = self._find_syllable_break(word)
            else:
                # Adaptive for medium words
                split_point = max(1, len(word) // 2)
            
            bold_part = word[:split_point]
            regular_part = word[split_point:]
            
            return f"{self.bold_tag_open}{bold_part}{self.bold_tag_close}{regular_part}"
        
        return re.sub(r'\b\w+\b', format_word, text)
    
    def _find_syllable_break(self, word: str) -> int:
        """Find optimal syllable break point in word."""
        if len(word) <= 3:
            return 1
        
        word_lower = word.lower()
        
        # Look for consonant clusters
        for i, cluster in enumerate(self.consonant_clusters):
            if cluster in word_lower:
                pos = word_lower.find(cluster)
                if pos > 0 and pos < len(word) - 1:
                    return pos + 1
        
        # Simple vowel-consonant pattern
        for i in range(1, len(word) - 1):
            if word_lower[i] in self.vowels and word_lower[i + 1] not in self.vowels:
                return i + 1
        
        # Fallback to middle
        return len(word) // 2
    
    def format_paragraph(self, text: str, preserve_whitespace: bool = True) -> str:
        """Format entire paragraph while preserving structure."""
        if preserve_whitespace:
            # Split by sentences and format each
            sentences = self.sentence_endings.split(text)
            formatted_sentences = []
            
            for sentence in sentences:
                if sentence.strip():
                    formatted_sentences.append(self.format_text(sentence.strip()))
                else:
                    formatted_sentences.append(sentence)
            
            return '. '.join(formatted_sentences)
        else:
            return self.format_text(text)
    
    def remove_formatting(self, formatted_text: str) -> str:
        """Remove bionic formatting from text."""
        # Remove HTML bold tags
        text = re.sub(r'<b>(.*?)</b>', r'\1', formatted_text)
        return text
    
    def get_formatting_stats(self, original_text: str, formatted_text: str) -> Dict[str, Any]:
        """Get statistics about formatting applied."""
        original_words = len(re.findall(r'\b\w+\b', original_text))
        bold_spans = len(re.findall(r'<b>.*?</b>', formatted_text))
        
        return {
            'original_words': original_words,
            'formatted_words': bold_spans,
            'formatting_ratio': bold_spans / original_words if original_words > 0 else 0,
            'original_length': len(original_text),
            'formatted_length': len(formatted_text),
            'size_increase': len(formatted_text) - len(original_text)
        } 