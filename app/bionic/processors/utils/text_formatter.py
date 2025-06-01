"""
Text Formatting Utilities for Bionic Reading

This module contains the core bionic text formatting logic with improved
character handling and robust formatting functions.
"""

from .character_classifier import should_apply_bionic_formatting, is_likely_word
from .math_detector import should_preserve_as_math


def calculate_bionic_split(word):
    """
    Calculate how many characters should be bold in a word for bionic reading.
    
    Args:
        word (str): The word to analyze
        
    Returns:
        int: Number of characters to make bold
    """
    if not word or not word.strip():
        return 0
    
    clean_word = word.strip()
    word_length = len(clean_word)
    
    if word_length <= 1:
        return 1
    elif word_length <= 3:
        return 1
    elif word_length <= 6:
        return 2
    elif word_length <= 9:
        return 3
    else:
        return min(4, word_length // 2)


def process_word_bionic(word):
    """
    Process a single word for bionic reading format.
    
    Args:
        word (str): The word to process
        
    Returns:
        tuple: (original_word, bold_part, regular_part)
    """
    if not word or not word.strip():
        return word, "", ""
    
    clean_word = word.strip()
    
    # Check if this word should receive bionic formatting
    if not should_apply_bionic_formatting(clean_word):
        return clean_word, "", clean_word
    
    # Check if this is mathematical content that should be preserved
    if should_preserve_as_math(clean_word):
        return clean_word, "", clean_word
    
    # Calculate the split point
    bold_length = calculate_bionic_split(clean_word)
    
    # Split the word
    bold_part = clean_word[:bold_length]
    regular_part = clean_word[bold_length:]
    
    return clean_word, bold_part, regular_part


def format_bionic_text(word, bold_part, regular_part):
    """
    Format a word with bionic reading styling for plain text.
    
    Args:
        word (str): Original word
        bold_part (str): Part to be bolded
        regular_part (str): Regular part
        
    Returns:
        str: Formatted text (for plain text, just returns the original)
    """
    # For plain text, we can't really show bold, so return original
    return word


def create_html_bionic_word(word, bold_part, regular_part):
    """
    Create HTML formatted bionic word with proper styling.
    
    Args:
        word (str): Original word
        bold_part (str): Part to be bolded
        regular_part (str): Regular part
        
    Returns:
        str: HTML formatted word
    """
    if not bold_part and not regular_part:
        return word
    
    if bold_part and regular_part:
        return f'<strong>{bold_part}</strong>{regular_part}'
    elif bold_part:
        return f'<strong>{bold_part}</strong>'
    else:
        return word


def process_text_bionic_enhanced(text):
    """
    Enhanced version of bionic text processing with better character handling.
    
    Args:
        text (str): The text to process
        
    Returns:
        tuple: (original_text, bold_part, regular_part)
    """
    if not text or not text.strip():
        return text, "", ""
    
    clean_text = text.strip()
    
    # Use enhanced character classification
    if not should_apply_bionic_formatting(clean_text):
        return clean_text, "", clean_text
    
    # Check for mathematical content
    if should_preserve_as_math(clean_text):
        return clean_text, "", clean_text
    
    # Check if this is likely a regular word
    if not is_likely_word(clean_text):
        return clean_text, "", clean_text
    
    # Process as regular word
    _, bold_part, regular_part = process_word_bionic(clean_text)
    return clean_text, bold_part, regular_part


def apply_bionic_formatting_to_text(text, output_format='html'):
    """
    Apply bionic formatting to a complete text string.
    
    Args:
        text (str): Text to process
        output_format (str): 'html' or 'plain'
        
    Returns:
        str: Formatted text
    """
    if not text:
        return text
    
    # Import here to avoid circular imports
    from .pattern_matcher import split_preserving_math
    
    result = []
    segments = split_preserving_math(text)
    
    for segment, is_word, is_math in segments:
        if is_word and not is_math:
            # Process word for bionic reading
            _, bold_part, regular_part = process_word_bionic(segment)
            
            if output_format == 'html':
                formatted_word = create_html_bionic_word(segment, bold_part, regular_part)
                result.append(formatted_word)
            else:
                result.append(segment)  # Plain text, keep original
        else:
            # Keep segment as-is (math, punctuation, spaces)
            result.append(segment)
    
    return ''.join(result)


def validate_bionic_formatting(original, bold_part, regular_part):
    """
    Validate that bionic formatting was applied correctly.
    
    Args:
        original (str): Original word
        bold_part (str): Bold part
        regular_part (str): Regular part
        
    Returns:
        bool: True if formatting is valid
    """
    if not original:
        return True
    
    # Check if parts reconstruct the original
    reconstructed = (bold_part or "") + (regular_part or "")
    return reconstructed == original.strip()


def get_bionic_statistics(text):
    """
    Get statistics about bionic formatting applied to text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        dict: Statistics about the formatting
    """
    if not text:
        return {
            'total_segments': 0,
            'words_processed': 0,
            'words_preserved': 0,
            'math_segments': 0
        }
    
    from .pattern_matcher import split_preserving_math
    
    segments = split_preserving_math(text)
    
    total_segments = len(segments)
    words_processed = 0
    words_preserved = 0
    math_segments = 0
    
    for segment, is_word, is_math in segments:
        if is_math:
            math_segments += 1
        elif is_word:
            if should_apply_bionic_formatting(segment):
                words_processed += 1
            else:
                words_preserved += 1
    
    return {
        'total_segments': total_segments,
        'words_processed': words_processed,
        'words_preserved': words_preserved,
        'math_segments': math_segments
    } 