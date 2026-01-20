"""
OCR Processing Module
Handles image-to-text conversion for Arabic text using OpenAI Vision API
"""
import os
import base64
import io
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_text_from_image(image_file):
    """
    Extract Arabic text from an image file using OpenAI Vision API
    
    Args:
        image_file: File object or bytes
        
    Returns:
        dict: Contains 'text' and 'success' status
    """
    try:
        # Read image and convert to base64
        if isinstance(image_file, bytes):
            image_bytes = image_file
        else:
            image_file.seek(0)
            image_bytes = image_file.read()
        
        # Encode to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Determine image type
        image_type = "image/jpeg"  # default
        if image_bytes[:4] == b'\x89PNG':
            image_type = "image/png"
        
        # Call OpenAI Vision API to extract text
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "استخرج النصّ العربي من هذه الصورة فقط. لا تُضِف أيّ تعليقاتٍ أو شروحات. أعد النصّ الموجود في الصورة فقط."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Extract the text from response
        extracted_text = response.choices[0].message.content.strip()
        
        if not extracted_text:
            return {
                'success': False,
                'text': '',
                'error': 'لم يُكتشَف أيّ نصّ في الصورة.'
            }
        
        return {
            'success': True,
            'text': extracted_text,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'حدث خطأ أثناء معالجة الصورة: {str(e)}'
        }

def is_image_file(filename):
    """Check if file is a valid image"""
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)
