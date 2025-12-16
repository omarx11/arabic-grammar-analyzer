from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def analyze_arabic_text(text):
    """Analyze Arabic text using OpenAI GPT-3.5"""
    
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
            'message': 'الرجاء إدخال نص للتحليل',
            'message_en': 'Please enter text to analyze'
        })
        return feedback
    
    # Count basic stats
    sentences = re.split(r'[.!?،؛]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    feedback['sentence_count'] = len(sentences)
    
    words = text.split()
    feedback['word_count'] = len(words)
    
    # Create prompt for GPT
    prompt = f"""أنت خبير في اللغة العربية والنحو. قم بتحليل النص العربي التالي وقدم تقريراً مفصلاً مع شرح كل خطأ وكيفية تصحيحه.

النص:
{text}

يرجى تقديم التحليل بصيغة JSON التالية بالضبط:
{{
  "errors": [
    {{
      "type": "نوع الخطأ (نحوي/إملائي/همزة/حركات/أسلوبي)",
      "word": "الكلمة الخاطئة",
      "sentence": "الجملة الكاملة التي تحتوي على الخطأ",
      "correction": "التصحيح المقترح",
      "message": "شرح الخطأ بالتفصيل بالعربية",
      "message_en": "Detailed error explanation in English",
      "explanation": "شرح لماذا هذا خطأ والقاعدة النحوية المتعلقة به",
      "example": "مثال على الاستخدام الصحيح"
    }}
  ],
  "suggestions": [
    {{
      "type": "نوع الاقتراح",
      "message": "الاقتراح بالعربية مع شرح السبب",
      "message_en": "Suggestion with explanation in English",
      "improvement": "كيفية التحسين بالتفصيل"
    }}
  ],
  "grammar_analysis": [
    {{"word": "الكلمة", "lemma": "الجذر أو الأصل", "pos": "نوع الكلمة بالعربية (اسم/فعل/حرف/صفة/ظرف)"}}
  ],
  "score": عدد من 0 إلى 100,
  "overall_feedback": "ملاحظات عامة على النص وكيفية تحسينه"
}}

تعليمات مهمة:
1. **الأخطاء النحوية**: مثل أخطاء الإعراب، التذكير والتأنيث، الأفعال والفاعل، إلخ
2. **الأخطاء الإملائية**: أخطاء الكتابة والإملاء
3. **أخطاء الهمزة**: همزة القطع والوصل، الهمزة المتطرفة والمتوسطة (أ إ آ ء ئ ؤ)
4. **الحركات (التشكيل)**: أخطاء في الفتحة والكسرة والضمة والسكون والتنوين
5. **الأخطاء الأسلوبية**: تكرار، جمل طويلة، ركاكة في التعبير

لكل خطأ:
- اذكر الجملة الكاملة التي تحتوي على الخطأ
- اذكر الكلمة الخاطئة بالضبط
- اذكر التصحيح الصحيح
- اشرح لماذا هو خطأ والقاعدة النحوية
- أعط مثالاً على الاستخدام الصحيح

تأكد من أن الإخراج بصيغة JSON صحيحة فقط بدون نص إضافي قبل أو بعد JSON"""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت معلم لغة عربية خبير في النحو والإملاء. تقوم بتحليل النصوص العربية وتقديم ملاحظات دقيقة ومفيدة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Extract the response
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON from the response
        # Sometimes GPT adds markdown code blocks, so we need to clean it
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        try:
            analysis = json.loads(result_text)
            
            # Update feedback with AI analysis
            if 'errors' in analysis and isinstance(analysis['errors'], list):
                feedback['errors'] = analysis['errors']
            
            if 'suggestions' in analysis and isinstance(analysis['suggestions'], list):
                feedback['suggestions'] = analysis['suggestions']
            
            if 'grammar_analysis' in analysis and isinstance(analysis['grammar_analysis'], list):
                # Limit to first 20 words to avoid overwhelming the UI
                feedback['grammar_analysis'] = analysis['grammar_analysis'][:20]
            
            if 'overall_feedback' in analysis and isinstance(analysis['overall_feedback'], str):
                feedback['overall_feedback'] = analysis['overall_feedback']
            
            if 'score' in analysis and isinstance(analysis['score'], (int, float)):
                feedback['score'] = int(analysis['score'])
            else:
                # Calculate fallback score
                feedback['score'] = max(0, 100 - len(feedback['errors']) * 15 - len(feedback['suggestions']) * 5)
        
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create a simple feedback based on the text response
            feedback['suggestions'].append({
                'type': 'analysis',
                'message': 'تم التحليل بنجاح',
                'message_en': 'Analysis completed'
            })
            feedback['score'] = 75
            
            # Try to extract some basic analysis from the response text
            if 'خطأ' in result_text or 'error' in result_text.lower():
                feedback['errors'].append({
                    'type': 'general',
                    'message': 'تم اكتشاف بعض الملاحظات على النص',
                    'message_en': 'Some issues were detected in the text'
                })
    
    except Exception as e:
        # Handle API errors
        feedback['errors'].append({
            'type': 'api_error',
            'message': f'حدث خطأ في التحليل: {str(e)}',
            'message_en': f'Analysis error: {str(e)}'
        })
        feedback['score'] = 0
    
    return feedback


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """API endpoint to analyze Arabic text"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({
            'error': 'No text provided',
            'error_ar': 'لم يتم إدخال نص'
        }), 400
    
    # Perform analysis using OpenAI
    feedback = analyze_arabic_text(text)
    
    return jsonify(feedback)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
