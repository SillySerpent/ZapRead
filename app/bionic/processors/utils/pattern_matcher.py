"""
Pattern Matching Utilities for Bionic Reading

This module provides regex patterns and text parsing functions that can
properly handle mathematical content and improve text segmentation.
"""

import re
from .math_detector import should_preserve_as_math


def get_word_pattern():
    """
    Get the regex pattern for matching words (letters only).
    
    Returns:
        str: Compiled regex pattern for letter-only words
    """
    # Only match sequences of letters (no digits)
    return r'\b[a-zA-Z]+\b'


def get_math_patterns():
    """
    Get regex patterns for detecting mathematical expressions.
    
    Returns:
        dict: Dictionary of compiled regex patterns for different math types
    """
    return {
        'scientific_notation': re.compile(r'\d+\.?\d*[eE][+-]?\d+|\d+\.?\d*×10[⁻⁺]?\d+'),
        'equations': re.compile(r'[a-zA-Z0-9\s]+=[a-zA-Z0-9\s+\-*/^()]+'),
        'formulas': re.compile(r'[a-zA-Z]+\([^)]+\)|[a-zA-Z]+_\d+|[a-zA-Z]+\^\d+'),
        'units': re.compile(r'\d+\.?\d*\s*[a-zA-Z]+/?[a-zA-Z]*'),
        'percentages': re.compile(r'\d+\.?\d*%'),
        'degrees': re.compile(r'\d+\.?\d*°[CF]?')
    }


def parse_text_segments(text):
    """
    Parse text into segments, identifying words, spaces, punctuation, and math.
    
    Args:
        text (str): Text to parse
        
    Returns:
        list: List of tuples (segment_text, segment_type)
              segment_type can be: 'word', 'math', 'space', 'punctuation'
    """
    if not text:
        return []
    
    segments = []
    
    # Use regex to find all segments (words, spaces, punctuation)
    pattern = r'(\b[a-zA-Z]+\b|\s+|[^\w\s]+|\b\d+\.?\d*\b|\b\w+\b)'
    matches = re.finditer(pattern, text)
    
    for match in matches:
        segment = match.group()
        
        if not segment:
            continue
        
        # Classify the segment
        if segment.isspace():
            segment_type = 'space'
        elif should_preserve_as_math(segment):
            segment_type = 'math'
        elif re.match(r'^[a-zA-Z]+$', segment):
            segment_type = 'word'
        elif re.match(r'^\d+\.?\d*$', segment):
            segment_type = 'number'
        else:
            segment_type = 'punctuation'
        
        segments.append((segment, segment_type))
    
    return segments


def split_preserving_math(text):
    """
    Split text into words and non-words while preserving mathematical expressions.
    
    Args:
        text (str): Text to split
        
    Returns:
        list: List of tuples (text, is_word, is_math)
    """
    if not text:
        return []
    
    result = []
    
    # Enhanced pattern that captures mathematical expressions as complete units
    # This pattern looks for:
    # 1. Mathematical expressions with equations (word=word, E=mc², etc.)
    # 2. Numbers with units (25kg, 100m/s, etc.)
    # 3. Scientific notation (1.23e-4, 2.5E+10, etc.)
    # 4. Mathematical functions (sin(x), log(n), etc.)
    # 5. Letter-only words
    # 6. Plain numbers
    # 7. Whitespace
    # 8. Other characters/punctuation
    pattern = r'([a-zA-Z]+=[a-zA-Z0-9²³⁴⁵⁶⁷⁸⁹⁰±]+|\d+\.?\d*[a-zA-Z]+(?:/[a-zA-Z]+)?|\d+\.?\d*[eE][+-]?\d+|[a-zA-Z]+\([^)]*\)|\b[a-zA-Z]+\b|\b\d+\.?\d*\b|\s+|[^\w\s]+)'
    
    matches = re.finditer(pattern, text)
    
    for match in matches:
        segment = match.group()
        
        if not segment:
            continue
        
        # Determine if this is a word that should get bionic formatting
        is_word = bool(re.match(r'^[a-zA-Z]+$', segment))
        is_math = should_preserve_as_math(segment)
        
        result.append((segment, is_word, is_math))
    
    return result


def extract_words_only(text):
    """
    Extract only letter-based words from text, ignoring numbers and punctuation.
    
    Args:
        text (str): Text to process
        
    Returns:
        list: List of letter-only words
    """
    if not text:
        return []
    
    # Match only sequences of letters
    word_pattern = re.compile(r'\b[a-zA-Z]+\b')
    return word_pattern.findall(text)


def find_word_boundaries(text):
    """
    Find boundaries of letter-based words in text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        list: List of tuples (start, end, word) for each word
    """
    if not text:
        return []
    
    boundaries = []
    word_pattern = re.compile(r'\b[a-zA-Z]+\b')
    
    for match in word_pattern.finditer(text):
        start, end = match.span()
        word = match.group()
        boundaries.append((start, end, word))
    
    return boundaries


def is_punctuation_only(text):
    """
    Check if text contains only punctuation and whitespace.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text is only punctuation/whitespace
    """
    if not text:
        return True
    
    # Remove whitespace and check if remaining chars are all punctuation
    clean_text = text.strip()
    if not clean_text:
        return True
    
    return all(not c.isalnum() for c in clean_text)


def split_on_word_boundaries(text):
    """
    Split text on word boundaries while preserving all content.
    
    Args:
        text (str): Text to split
        
    Returns:
        list: List of text segments maintaining original order
    """
    if not text:
        return []
    
    segments = []
    last_end = 0
    
    # Find all letter-word boundaries
    word_pattern = re.compile(r'\b[a-zA-Z]+\b')
    
    for match in word_pattern.finditer(text):
        start, end = match.span()
        
        # Add any text before this word
        if start > last_end:
            segments.append(text[last_end:start])
        
        # Add the word itself
        segments.append(text[start:end])
        last_end = end
    
    # Add any remaining text after the last word
    if last_end < len(text):
        segments.append(text[last_end:])
    
    return [seg for seg in segments if seg]  # Remove empty segments


def create_enhanced_word_regex():
    """
    Create an enhanced regex for word detection that handles edge cases.
    
    Returns:
        re.Pattern: Compiled regex pattern
    """
    # Pattern explanation:
    # \b[a-zA-Z]+\b - word boundaries with letters only
    # This excludes numbers, mixed alphanumeric, and punctuation
    return re.compile(r'\b[a-zA-Z]+\b')


def validate_word_for_bionic(word):
    """
    Validate if a word is suitable for bionic processing.
    
    Args:
        word (str): Word to validate
        
    Returns:
        bool: True if word should receive bionic formatting
    """
    if not word or not word.strip():
        return False
    
    clean_word = word.strip()
    
    # Must be at least 1 character
    if len(clean_word) < 1:
        return False
    
    # Must contain only letters
    if not clean_word.isalpha():
        return False
    
    # Must not be mathematical content
    if should_preserve_as_math(clean_word):
        return False
    
    return True 