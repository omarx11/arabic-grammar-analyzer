"""
Grammar Checking Module
Handles Arabic grammar and spelling analysis using OpenAI
"""
from openai import OpenAI
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_sentence_for_word(text, word):
    """Extract the sentence containing a specific word"""
    sentences = re.split(r'[.!?،؛]', text)
    for sentence in sentences:
        if word in sentence:
            return sentence.strip()
    return word

def analyze_arabic_text(text):
    """Analyze Arabic text for grammar and spelling errors"""
    
    feedback = {
        'word_count': 0,
        'sentence_count': 0,
        'errors': [],
        'suggestions': [],
        'grammar_analysis': [],
        'score': 0
    }
    
    # Basic validation
    text = text.strip()
    if not text:
        feedback['errors'].append({
            'type': 'empty',
            'message': 'رجاءً أدخل نصًّا للتحليل.'
        })
        return feedback
    
    # Count basic stats
    sentences = re.split(r'[.!?،؛]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    feedback['sentence_count'] = len(sentences)
    
    words = text.split()
    feedback['word_count'] = len(words)
    
    # Use AI for comprehensive analysis with optimized few-shot learning
    prompt = f"""أنت محلل لغة عربية خبير. افحص النص وسجل الأخطاء الإملائية والنحوية الواضحة فقط.

===== النص =====
{text}
===== نهاية =====

⚡ **قواعد أساسية:**
1. ⛔ لا تصحح الكلمات العامية إلى الفصحى (روحت، رحت، شلون، زين، بس، حلو، يلا، شوي، وين ← كلها مقبولة)
2. صحح فقط الأخطاء الإملائية الحقيقية
3. لا تضع أخطاء على كلمات صحيحة (كلكم، كلهم ← صحيحة)

📋 **أخطاء تحتاج تصحيح:**
• نقص "ال": اسلام→السلام، سوق(محدد)→السوق، بيت(محدد)→البيت
• تاء مربوطة/مفتوحة: ورحمت→ورحمة، جماعه→جماعة
• اسم الجلالة: اللاه→الله
• كلمات خاطئة: تبرقاتا→وبركاته، اشللونكن→شلونكن
• همزة: امس→أمس
• كلمات متصلة: ماعرفت→ما عرفت
• ضمائر: عليكن→عليكم (للمذكر)

🎯 **أمثلة سريعة:**

✓ "اسلام عليكن" → أخطاء: اسلام(السلام)، عليكن(عليكم)
✓ "ورحمت اللاه تبرقاتا" → أخطاء: ورحمت(ورحمة)، اللاه(الله)، تبرقاتا(وبركاته)
✓ "اشللونكن يا جماعه كلكم" → أخطاء: اشللونكن(شلونكن)، جماعه(جماعة) | ✓كلكم صحيح
✓ "امس روحت سوق" → أخطاء: امس(أمس)، سوق(السوق) | ✓روحت صحيح(عامية)
✓ "بس ماعرفت زين" → أخطاء: ماعرفت(ما عرفت) | ✓بس وزين صحيحة(عامية)

⚠️ مهم: أرجع JSON صالح فقط - لا نص قبله أو بعده!

📄 صيغة JSON (التزم بها تمامًا):
{{
  "errors": [
    {{
      "type": "إملائي",
      "word": "الكلمة الخاطئة",
      "sentence": "الجملة الكاملة",
      "correction": "التصحيح",
      "message": "شرح الخطأ",
      "explanation": "شرح القاعدة",
      "example": "مثال على الاستخدام الصحيح"
    }}
  ],
  "suggestions": [],
  "grammar_analysis": [],
  "score": 85,
  "overall_feedback": "ملاحظات عامة"
}}"""

    try:
        # Call OpenAI API with optimized settings
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "محلل لغة عربية خبير. قواعد: 1) لا تصحح العامية للفصحى (روحت،شلون،زين،بس=مقبولة) 2) صحح الأخطاء الإملائية فقط 3) كلكم/كلهم صحيحة 4) تجنب False Positives. أرجع JSON صالح فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # Extract the response
        result_text = response.choices[0].message.content.strip()
        
        # Clean JSON from markdown code blocks and other formatting
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Remove any text before the first { and after the last }
        if '{' in result_text and '}' in result_text:
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            result_text = result_text[start_idx:end_idx]
        
        try:
            analysis = json.loads(result_text)
            
            ai_errors = []
            if 'errors' in analysis and isinstance(analysis['errors'], list):
                ai_errors = analysis['errors']

            # Update feedback with AI errors only
            feedback['errors'] = ai_errors
            
            if 'suggestions' in analysis and isinstance(analysis['suggestions'], list):
                feedback['suggestions'] = analysis['suggestions']
            
            if 'grammar_analysis' in analysis and isinstance(analysis['grammar_analysis'], list):
                feedback['grammar_analysis'] = analysis['grammar_analysis'][:20]
            
            if 'overall_feedback' in analysis and isinstance(analysis['overall_feedback'], str):
                feedback['overall_feedback'] = analysis['overall_feedback']
            
            if 'score' in analysis and isinstance(analysis['score'], (int, float)):
                feedback['score'] = int(analysis['score'])
            else:
                feedback['score'] = max(0, 100 - len(feedback['errors']) * 15 - len(feedback['suggestions']) * 5)
        
        except json.JSONDecodeError as e:
            # Log the error for debugging
            print(f"JSON Parse Error: {str(e)}")
            print(f"Raw response: {result_text[:500]}")  # Print first 500 chars
            
            feedback['errors'].append({
                'type': 'parse_error',
                'message': f'حدث خطأ في تحليل النتائج: {str(e)}'
            })
            feedback['score'] = 0
    
    except Exception as e:
        feedback['errors'].append({
            'type': 'api_error',
            'message': f'حدث خطأ أثناء التحليل: {str(e)}'
        })
        feedback['score'] = 0
    
    return feedback
