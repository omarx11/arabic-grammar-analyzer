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
    
    # Use AI for comprehensive analysis with context-aware checking
    prompt = f"""أنت محلل لغة عربية خبير. حلل النص إملائياً ونحوياً مع مراعاة السياق والمعنى الكامل.

===== النص =====
{text}
===== نهاية =====

📋 **قواعد التصحيح:**
1. اقرأ النص كاملاً أولاً وافهم المعنى والسياق العام
2. تعرف على العبارات والجمل الشائعة (مثل: السلام عليكم ورحمة الله وبركاته)
3. راجع كل كلمة إملائياً ونحوياً - لا تتخطى أي كلمة
4. إذا وجدت كلمة غريبة أو محرفة - قارنها بالسياق لتعرف الكلمة الصحيحة
5. أنواع الأخطاء الإملائية:
   • نقص "ال" التعريف: اسلام → السلام، سوق → السوق، خبز → الخبز
   • نقص أو تحريف حروف كاملة: تبرقاتا → وبركاته (الواو ناقصة والحروف محرفة)
   • التاء المربوطة (ة/ت): رحمت → رحمة
   • اسم الجلالة: اللاه → الله
   • الهمزات بجميع أشكالها: امس → أمس، ءامن → آمن، مسؤل → مسؤول
   • كلمات متصلة: ماعرفت → ما عرفت
   • حروف ناقصة: بيت → للبيت أو إلى البيت
6. أنواع الأخطاء النحوية:
   • استخدام حروف الجر الخاطئة
   • ترتيب الكلمات
   • التذكير والتأنيث
   • الضمائر
7. التشكيل والحركات الخاطئة:
   • حركات خاطئة أو غير ضرورية: خِبز → خبز أو الخبز
   • تشكيل غير صحيح على الكلمات

⚠️ قواعد مهمة:
• الأولوية للسياق - إذا كانت كلمة محرفة تماماً، استخدم السياق لمعرفة الكلمة الصحيحة
• لا تصحح الكلمة حرفياً فقط - انظر للمعنى المقصود
• راجع التشكيل والحركات - إذا كانت خاطئة أو غير ضرورية، صححها
• لا تصحح اللهجات (مثل: روحت، شفت) - هي مقبولة
• راجع الأخطاء الإملائية والنحوية معاً
• لا تترك أي كلمة دون فحص - حتى لو بدت بسيطة

📄 صيغة JSON (التزم بها تمامًا - كل حقل يجب أن يكون مكتملاً):
{{
  "errors": [
    {{
      "type": "إملائي",
      "word": "الكلمة الخاطئة",
      "correction": "التصحيح الصحيح",
      "message": "شرح مفصل وكامل للخطأ (جملة كاملة)",
      "explanation": "شرح القاعدة النحوية أو الإملائية كاملة (جملة كاملة)",
      "example": "مثال كامل على الاستخدام الصحيح (جملة كاملة)"
    }}
  ],
  "suggestions": [],
  "grammar_analysis": [],
  "score": 85,
  "overall_feedback": "ملاحظة عامة مختصرة على النص (جملة واحدة فقط - لا تكرر نصائح واضحة)"
}}"""

    try:
        # Call OpenAI API with optimized settings
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "محلل لغة عربية خبير. حلل السياق بعناية قبل التصحيح. اكتب شروحات كاملة ومفصلة - لا تختصر أبداً. كل حقل يجب أن يحتوي على جملة كاملة ومفهومة. أرجع JSON صالح كامل فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000,  # Increased to prevent truncation
            response_format={"type": "json_object"}
        )
        
        # Extract the response
        result_text = response.choices[0].message.content.strip()
        
        # Check if response was truncated
        finish_reason = response.choices[0].finish_reason
        if finish_reason == 'length':
            print("Warning: OpenAI response was truncated due to max_tokens limit")
        
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
                
                # Check and fix incomplete fields
                for error in ai_errors:
                    # Ensure all required fields are complete
                    if not error.get('message') or len(error.get('message', '').strip()) < 10:
                        print(f"Warning: Incomplete 'message' for word: {error.get('word')}")
                        error['message'] = 'يحتاج إلى تصحيح'
                    
                    if not error.get('explanation') or len(error.get('explanation', '').strip()) < 10:
                        print(f"Warning: Incomplete 'explanation' for word: {error.get('word')}")
                        error['explanation'] = 'يرجى مراجعة القاعدة النحوية أو الإملائية'
                    
                    if not error.get('example'):
                        error['example'] = f"مثال: {error.get('correction', '')}"

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
        error_message = str(e).lower()
        
        # Check if it's a quota/billing error
        if 'quota' in error_message or 'insufficient_quota' in error_message or 'billing' in error_message or 'rate_limit' in error_message:
            feedback['errors'].append({
                'type': 'quota_error',
                'message': 'نفدت رصيد API',
                'error_details': str(e)
            })
            feedback['quota_exceeded'] = True
        else:
            feedback['errors'].append({
                'type': 'api_error',
                'message': f'حدث خطأ أثناء التحليل: {str(e)}'
            })
        
        feedback['score'] = 0
        print(f"API Error: {str(e)}")
    
    return feedback
