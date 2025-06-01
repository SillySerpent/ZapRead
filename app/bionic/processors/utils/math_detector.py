"""
Mathematical Expression Detection for Bionic Reading

This module provides functions to detect mathematical expressions, equations,
formulas, and scientific notation that should be preserved without bionic formatting.
"""

import re


# Mathematical symbols that indicate mathematical content
MATH_SYMBOLS = {
    # Basic arithmetic
    '+', '-', '*', '/', '=', '^',
    # Comparison operators
    '<', '>', '≤', '≥', '≠', '≈', '∼',
    # Mathematical constants and symbols (remove single 'e' to avoid false positives)
    'π', '∞', '∑', '∏', '∫', '∂', '∇', '∆',
    # Set theory
    '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∅',
    # Logic
    '∧', '∨', '¬', '→', '↔', '∀', '∃',
    # Other mathematical symbols
    '±', '∓', '×', '÷', '√', '∝', '°', '%',
    # Superscript numbers (common in equations)
    '⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹',
    # Subscript numbers
    '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉'
}

# Mathematical function names that indicate formulas
MATH_FUNCTIONS = {
    'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
    'log', 'ln', 'exp', 'sqrt', 'abs', 'min', 'max',
    'sum', 'prod', 'lim', 'int', 'diff', 'grad',
    'det', 'tr', 'rank', 'dim'
}


def contains_math_symbols(text):
    """
    Check if text contains mathematical symbols.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains mathematical symbols
    """
    if not text:
        return False
    
    return any(symbol in text for symbol in MATH_SYMBOLS)


def is_scientific_notation(text):
    """
    Check if text represents scientific notation.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text is in scientific notation format
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    
    # Pattern for scientific notation: 1.23e-4, 2.5E+10, 1.0×10⁻⁶
    scientific_patterns = [
        r'^\d+\.?\d*[eE][+-]?\d+$',           # 1.23e-4, 2.5E+10
        r'^\d+\.?\d*×10[⁻⁺]?\d+$',           # 1.0×10⁻⁶
        r'^\d+\.?\d*\*10\^[+-]?\d+$',        # 1.0*10^-6
        r'^\d+\.?\d*\s*×\s*10\^[+-]?\d+$',   # 1.0 × 10^-6
    ]
    
    return any(re.match(pattern, clean_text) for pattern in scientific_patterns)


def is_equation(text):
    """
    Check if text represents a mathematical equation.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text appears to be an equation
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    
    # Must contain an equals sign
    if '=' not in clean_text:
        return False
    
    # Common equation patterns
    equation_patterns = [
        r'[a-zA-Z0-9]+\s*=\s*[a-zA-Z0-9]',     # a = b, x = 5
        r'[a-zA-Z]+\^?\d*\s*[+\-*/]\s*[a-zA-Z]+\^?\d*\s*=',  # x² + y² =
        r'[a-zA-Z]+\([a-zA-Z,\s]+\)\s*=',      # f(x) =
        r'\w+\s*=\s*\w+[+\-*/]\w+',            # y = mx + b
    ]
    
    # Check for equation patterns or mathematical symbols
    has_equation_pattern = any(re.search(pattern, clean_text) for pattern in equation_patterns)
    has_math_symbols = contains_math_symbols(clean_text)
    
    return has_equation_pattern or has_math_symbols


def is_formula(text):
    """
    Check if text represents a mathematical formula.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text appears to be a formula
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip().lower()
    
    # Check for mathematical function names (but only as complete words)
    has_math_function = any(re.search(rf'\b{func}\b', clean_text) for func in MATH_FUNCTIONS)
    
    # Check for formula patterns
    formula_patterns = [
        r'[a-zA-Z]+\([^)]+\)',                  # f(x), sin(θ)
        r'\d*[a-zA-Z]+\^?\d*[+\-*/]\d*[a-zA-Z]+\^?\d*',  # ax² + bx + c
        r'[a-zA-Z]+_\d+',                       # x_1, y_2 (subscripts)
        r'[a-zA-Z]+\^\d+',                      # x², y³ (superscripts)
    ]
    
    has_formula_pattern = any(re.search(pattern, text) for pattern in formula_patterns)
    has_math_symbols = contains_math_symbols(text)
    
    # Only return True if we have clear mathematical indicators
    return has_math_function or has_formula_pattern or has_math_symbols


def is_mathematical_expression(text):
    """
    Check if text represents any kind of mathematical expression.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text is a mathematical expression
    """
    if not text or not text.strip():
        return False
    
    return (is_scientific_notation(text) or 
            is_equation(text) or 
            is_formula(text) or 
            contains_math_symbols(text))


def is_unit_with_number(text):
    """
    Check if text is a number with a unit (e.g., 25kg, 100m/s).
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text is a number with unit
    """
    if not text or not text.strip():
        return False
    
    clean_text = text.strip()
    
    # Common units patterns
    unit_patterns = [
        r'^\d+\.?\d*[a-zA-Z]+$',                # 25kg, 3.14m
        r'^\d+\.?\d*\s*[a-zA-Z]+$',             # 25 kg, 3.14 m
        r'^\d+\.?\d*[a-zA-Z]+/[a-zA-Z]+$',      # 100m/s, 60km/h
        r'^\d+\.?\d*\s*[a-zA-Z]+/[a-zA-Z]+$',   # 100 m/s, 60 km/h
        r'^\d+\.?\d*%$',                        # 25%, 100%
        r'^\d+\.?\d*°[CF]?$',                   # 25°C, 100°F, 45°
    ]
    
    return any(re.match(pattern, clean_text) for pattern in unit_patterns)


def should_preserve_as_math(text):
    """
    Determine if text should be preserved without bionic formatting due to mathematical content.
    
    Args:
        text (str): Text to evaluate
        
    Returns:
        bool: True if text should be preserved as-is
    """
    if not text or not text.strip():
        return False
    
    return (is_mathematical_expression(text) or 
            is_unit_with_number(text) or
            is_scientific_notation(text))


def extract_math_segments(text):
    """
    Extract mathematical segments from text while preserving their positions.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        list: List of tuples (start, end, is_math) indicating segments
    """
    if not text:
        return []
    
    segments = []
    words = re.finditer(r'\S+', text)
    
    for match in words:
        word = match.group()
        start, end = match.span()
        is_math = should_preserve_as_math(word)
        segments.append((start, end, is_math, word))
    
    return segments 