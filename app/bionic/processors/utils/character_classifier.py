"""
Character Classification Utilities for Bionic Reading

This module provides functions to classify text content and determine
if bionic formatting should be applied based on character types.
"""

import re


def is_pure_letters(text):
    """
    Check if text contains only alphabetic characters.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains only letters, False otherwise
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    return clean_text.isalpha()


def is_pure_numbers(text):
    """
    Check if text contains only numeric characters (including decimals).
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text is purely numeric, False otherwise
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    
    # Handle basic numbers with optional decimal point
    if re.match(r'^\d+\.?\d*$', clean_text):
        return True
    
    # Handle negative numbers
    if re.match(r'^-\d+\.?\d*$', clean_text):
        return True
    
    return False


def is_mixed_alphanumeric(text):
    """
    Check if text contains both letters and numbers.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains both letters and numbers
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    has_letters = any(c.isalpha() for c in clean_text)
    has_numbers = any(c.isdigit() for c in clean_text)
    
    return has_letters and has_numbers


def classify_text_type(text):
    """
    Classify text into categories for processing decisions.
    
    Args:
        text (str): Text to classify
        
    Returns:
        str: One of 'letters', 'numbers', 'mixed', 'punctuation', 'empty'
    """
    if not text or not text.strip():
        return 'empty'
    
    clean_text = text.strip()
    
    if is_pure_letters(clean_text):
        return 'letters'
    elif is_pure_numbers(clean_text):
        return 'numbers'
    elif is_mixed_alphanumeric(clean_text):
        return 'mixed'
    else:
        # Check if mostly punctuation
        punctuation_count = sum(1 for c in clean_text if not c.isalnum() and not c.isspace())
        if punctuation_count > len(clean_text) / 2:
            return 'punctuation'
        else:
            return 'mixed'


def should_apply_bionic_formatting(text):
    """
    Determine if bionic formatting should be applied to the given text.
    
    Args:
        text (str): Text to evaluate
        
    Returns:
        bool: True if bionic formatting should be applied, False otherwise
    """
    if not text or not text.strip():
        return False
    
    text_type = classify_text_type(text)
    
    # Only apply bionic formatting to pure letter words
    if text_type == 'letters':
        return True
    
    # For mixed content, check if it's predominantly letters
    if text_type == 'mixed':
        clean_text = text.strip()
        letter_count = sum(1 for c in clean_text if c.isalpha())
        total_chars = len(clean_text)
        
        # Apply bionic formatting if more than 70% letters
        return letter_count / total_chars > 0.7
    
    # Don't apply to numbers, punctuation, or empty text
    return False


def get_letter_ratio(text):
    """
    Calculate the ratio of letters to total characters in text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        float: Ratio of letters (0.0 to 1.0)
    """
    if not text or not text.strip():
        return 0.0
    
    clean_text = text.strip()
    if not clean_text:
        return 0.0
    
    letter_count = sum(1 for c in clean_text if c.isalpha())
    return letter_count / len(clean_text)


def is_likely_word(text):
    """
    Determine if text is likely a regular word that should get bionic formatting.
    
    Args:
        text (str): Text to evaluate
        
    Returns:
        bool: True if text appears to be a regular word
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    
    # Must have at least one letter
    if not any(c.isalpha() for c in clean_text):
        return False
    
    # Check letter ratio - should be mostly letters
    letter_ratio = get_letter_ratio(clean_text)
    
    # Words should be at least 70% letters
    return letter_ratio >= 0.7 