"""
Text Validator Module
Validates that text contains only Arabic characters
"""
import re

def is_arabic_text(text):
    """
    Check if text contains only Arabic characters, numbers, and basic punctuation.
    Returns (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "النصّ فارغ."
    
    # Remove whitespace, numbers, and common punctuation marks
    text_to_check = re.sub(r'[\s\d\n\r\t.,،؛:؟!?()\"\'،۔\u061B\u061F\u060C\u061E-]+', '', text)
    
    # Arabic Unicode ranges:
    # \u0600-\u06FF: Arabic
    # \u0750-\u077F: Arabic Supplement
    # \u08A0-\u08FF: Arabic Extended-A
    # \uFB50-\uFDFF: Arabic Presentation Forms-A
    # \uFE70-\uFEFF: Arabic Presentation Forms-B
    
    # Check if there are any non-Arabic characters
    non_arabic = re.findall(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text_to_check)
    
    if non_arabic:
        # Get unique non-Arabic characters found
        unique_chars = list(set(non_arabic))
        chars_str = ', '.join([f"'{c}'" for c in unique_chars[:5]])  # Show first 5
        
        return False, f"النصّ يحتوي على أحرف غير عربية: {chars_str}. يُسمح بالنصّ العربي فقط."
    
    return True, None

def validate_arabic_only(text):
    """
    Validate text and return error response if invalid.
    Returns None if valid, or error dict if invalid.
    """
    is_valid, error_msg = is_arabic_text(text)
    
    if not is_valid:
        return {
            'error': 'Only Arabic text is allowed',
            'error_ar': error_msg,
            'is_valid': False
        }
    
    return None
