from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import os
import io
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from config import get_config

# Import modules
from modules.auth import verify_password, login_required, is_logged_in, get_current_teacher
from modules.grammar_checker import analyze_arabic_text
from modules.ocr_processor import extract_text_from_image, is_image_file
from modules.pdf_generator import generate_pdf_report
from modules.database import save_analysis, get_analysis_history, get_analysis_by_id, delete_analysis, add_student, get_students, delete_student, get_student_analyses, get_analysis_by_share_id, toggle_analysis_public

from modules.cache_manager import get_cached_analysis, save_to_cache, get_cache_stats, clear_cache
from modules.text_validator import validate_arabic_only

# Load environment variables
load_dotenv()

# Get environment and configuration
env = os.getenv('FLASK_ENV', 'production')
config = get_config(env)

app = Flask(__name__)
app.config.from_object(config)

# Configure session security
app.config['SESSION_COOKIE_SECURE'] = not config.DEBUG  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Ensure upload directory exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception:
    pass  # Fail silently if directory creation fails

# Initialize database on startup
from modules.database import init_db, USE_POSTGRES
try:
    init_db()
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    print(f"✓ Database initialized ({db_type})")
except Exception as e:
    print(f"Database initialization: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ===== Error Handlers =====

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('error.html', message='عذرًا، الصفحة غير موجودة'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    # Log the error for debugging
    import traceback
    print(f"500 Error: {error}")
    print(traceback.format_exc())
    
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', message='عذرًا، حدث خطأ في الخادم'), 500

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return jsonify({'error': 'الملف كبير جدًّا. الحد الأقصى 16MB'}), 413


# ===== Authentication Routes =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Teacher login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '')
        password = data.get('password', '')
        
        if verify_password(username, password):
            session['teacher_id'] = username
            if request.is_json:
                return jsonify({'success': True, 'message': 'تم تسجيل الدخول بنجاح.'})
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'اسم المستخدم أو كلمة المرور غير صحيحة.'}), 401
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error')
            return render_template('login.html')
    
    # If already logged in, redirect to main page
    if is_logged_in():
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout current teacher"""
    session.pop('teacher_id', None)
    flash('تم تسجيل الخروج بنجاح.', 'success')
    return redirect(url_for('login'))


# ===== Main Routes =====

@app.route('/')
@login_required
def index():
    """Render the main page (requires login)"""
    teacher_id = get_current_teacher()
    return render_template('index.html', teacher_id=teacher_id)


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """API endpoint to analyze Arabic text (requires login)"""
    data = request.get_json()
    text = data.get('text', '').strip()
    student_name = data.get('student_name', 'غير معروف').strip()
    use_cache = data.get('use_cache', True)
    
    if not text:
        return jsonify({
            'error': 'No text provided',
            'error_ar': 'لم يتم إدخال نصّ.'
        }), 400
    
    # Validate Arabic text only
    validation_error = validate_arabic_only(text)
    if validation_error:
        return jsonify(validation_error), 400
    
    # Check cache first
    if use_cache:
        cached_result = get_cached_analysis(text)
        if cached_result:
            # Still save to database even if cached
            teacher_id = get_current_teacher()
            analysis_id, share_id = save_analysis(teacher_id, student_name, text, cached_result)
            cached_result['analysis_id'] = analysis_id
            cached_result['share_id'] = share_id
            cached_result['is_public'] = False
            cached_result['from_cache'] = True
            return jsonify(cached_result)
    
    # Perform analysis using OpenAI
    feedback = analyze_arabic_text(text)
    
    # Save to cache
    if use_cache:
        save_to_cache(text, feedback)
    
    # Save to database
    teacher_id = get_current_teacher()
    analysis_id, share_id = save_analysis(teacher_id, student_name, text, feedback)
    feedback['analysis_id'] = analysis_id
    feedback['share_id'] = share_id
    feedback['is_public'] = False  # New analyses are private by default
    
    return jsonify(feedback)


@app.route('/ocr', methods=['POST'])
@login_required
def ocr_upload():
    """Extract text from uploaded image"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'لم تُرفَع صورة.'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'لم يُختَر ملف.'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Extract text from image
            result = extract_text_from_image(file)
            
            # Validate extracted text is Arabic only
            if result.get('success') and result.get('text'):
                validation_error = validate_arabic_only(result['text'])
                if validation_error:
                    return jsonify({
                        'success': False,
                        'error': validation_error['error_ar']
                    }), 400
            
            return jsonify(result)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'حدث خطأ أثناء معالجة الصورة: {str(e)}'
            }), 500
    
    return jsonify({'success': False, 'error': 'نوع الملف غير مدعوم.'}), 400


@app.route('/history')
@login_required
def history():
    """Get analysis history for current teacher"""
    teacher_id = get_current_teacher()
    limit = request.args.get('limit', 50, type=int)
    
    history = get_analysis_history(teacher_id, limit)
    return jsonify({'history': history})


@app.route('/history/<int:analysis_id>')
@login_required
def get_analysis(analysis_id):
    """Get specific analysis by ID"""
    analysis = get_analysis_by_id(analysis_id)
    
    if analysis:
        return jsonify(analysis)
    
    return jsonify({'error': 'التحليل غير موجود.'}), 404


@app.route('/history/<int:analysis_id>/delete', methods=['POST'])
@login_required
def delete_analysis_route(analysis_id):
    """Delete an analysis"""
    teacher_id = get_current_teacher()
    success = delete_analysis(analysis_id, teacher_id)
    
    if success:
        return jsonify({'success': True, 'message': 'تم الحذف بنجاح.'})
    
    return jsonify({'success': False, 'error': 'تعذّر الحذف.'}), 400


@app.route('/export/pdf/<int:analysis_id>')
@login_required
def export_pdf(analysis_id):
    """Export analysis as PDF"""
    analysis = get_analysis_by_id(analysis_id)
    
    if not analysis:
        return jsonify({'error': 'التحليل غير موجود.'}), 404
    
    pdf_buffer = generate_pdf_report(
        analysis['student_name'],
        analysis['original_text'],
        analysis['analysis_result']
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"analysis_{analysis_id}.pdf"
    )





@app.route('/cache/stats')
@login_required
def cache_statistics():
    """Get cache statistics"""
    stats = get_cache_stats()
    return jsonify(stats)


@app.route('/cache/clear', methods=['POST'])
@login_required
def clear_cache_route():
    """Clear all cache"""
    clear_cache()
    return jsonify({'success': True, 'message': 'تم مسح الذاكرة المؤقّتة.'})


@app.route('/students', methods=['GET'])
@login_required
def get_students_list():
    """Get list of all students for current teacher"""
    teacher_id = get_current_teacher()
    students = get_students(teacher_id)
    return jsonify({'students': students})


@app.route('/students/add', methods=['POST'])
@login_required
def add_student_route():
    """Add a new student"""
    teacher_id = get_current_teacher()
    data = request.get_json()
    student_name = data.get('name', '').strip()
    
    if not student_name:
        return jsonify({'success': False, 'error': 'اسم الطالب مطلوب.'}), 400
    
    # Validate that student name is Arabic
    validation_error = validate_arabic_only(student_name)
    if validation_error:
            return jsonify({'success': False, 'error': 'يجب أن يكون اسم الطالب بالعربية فقط.'}), 400
    
    student_id = add_student(teacher_id, student_name)
    
    if student_id:
        return jsonify({'success': True, 'student_id': student_id, 'message': 'تمّت إضافة الطالب بنجاح.'})
    else:
        return jsonify({'success': False, 'error': 'الطالب موجود بالفعل.'}), 400


@app.route('/students/<student_name>/analyses')
@login_required
def get_student_analyses_route(student_name):
    """Get all analyses for a specific student"""
    teacher_id = get_current_teacher()
    limit = request.args.get('limit', 50, type=int)
    
    analyses = get_student_analyses(teacher_id, student_name, limit)
    return jsonify({'analyses': analyses, 'student_name': student_name})


@app.route('/students/<student_name>/delete', methods=['POST'])
@login_required
def delete_student_route(student_name):
    """Delete a student and all their analyses"""
    teacher_id = get_current_teacher()
    
    success = delete_student(teacher_id, student_name)
    
    if success:
        return jsonify({'success': True, 'message': 'تم حذف الطالب وجميع تحليلاته بنجاح.'})
    else:
        return jsonify({'success': False, 'error': 'تعذّر حذف الطالب.'}), 400


@app.route('/analysis/<int:analysis_id>/toggle-public', methods=['POST'])
@login_required
def toggle_public(analysis_id):
    """Toggle public/private status of an analysis"""
    teacher_id = get_current_teacher()
    new_status = toggle_analysis_public(analysis_id, teacher_id)
    
    if new_status is not None:
        return jsonify({
            'success': True,
            'is_public': new_status,
            'message': 'تم تحديث حالة المشاركة بنجاح.'
        })
    
    return jsonify({'success': False, 'error': 'تعذّر تحديث الحالة.'}), 400


@app.route('/share/<share_id>')
def view_shared_analysis(share_id):
    """View a shared analysis (public access, no login required)"""
    analysis = get_analysis_by_share_id(share_id)
    
    if not analysis:
        return render_template('error.html', message='التحليل غير موجود.'), 404
    
    if not analysis['is_public']:
        return render_template('error.html', message='هذا التحليل غير متاح للمشاركة.'), 403
    
    return render_template('shared_analysis.html', analysis=analysis, share_id=share_id)


@app.route('/health')
def health():
    """Health check endpoint"""
    health_status = {
        'status': 'ok',
        'database': 'unknown',
        'environment': env
    }
    
    # Check database connectivity
    try:
        from modules.database import get_db_connection, USE_POSTGRES
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('SELECT 1')
        else:
            cursor.execute('SELECT 1')
        
        cursor.close()
        conn.close()
        health_status['database'] = 'connected'
        health_status['database_type'] = 'PostgreSQL' if USE_POSTGRES else 'SQLite'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)


if __name__ == '__main__':
    # Run with configuration from environment
    port = int(os.getenv('PORT', 5000))
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=port
    )
