"""
Teacher Authentication Module
Handles login/logout functionality to ensure only teachers access the app
"""
from functools import wraps
from flask import session, redirect, url_for, flash
import hashlib
import sqlite3
import os

# Try to get DB path from config, fallback to /tmp for Vercel
try:
    from config import get_config
    config = get_config(os.getenv('FLASK_ENV', 'production'))
    DB_PATH = os.path.join(config.DB_PATH.replace('analysis_history.db', ''), 'auth.db') if hasattr(config, 'DB_PATH') else os.path.join('/tmp', 'auth.db')
except:
    DB_PATH = os.path.join('/tmp', 'auth.db')

# Hardcoded credentials for Vercel (since DB won't persist)
HARDCODED_USERS = {
    'sultan': hashlib.sha256('1234'.encode()).hexdigest(),
    'teacher1': hashlib.sha256('1234'.encode()).hexdigest(),
}

def init_auth_db():
    """Initialize authentication database"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create teachers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default admin accounts if they don't exist
        admin_password_hash = hashlib.sha256('1234'.encode()).hexdigest()
        
        # Check and create sultan account
        cursor.execute('SELECT COUNT(*) FROM teachers WHERE username = ?', ('sultan',))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO teachers (username, password_hash) VALUES (?, ?)',
                ('sultan', admin_password_hash)
            )
        
        # Check and create teacher1 account
        cursor.execute('SELECT COUNT(*) FROM teachers WHERE username = ?', ('teacher1',))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO teachers (username, password_hash) VALUES (?, ?)',
                ('teacher1', admin_password_hash)
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Auth DB init warning: {e}")
        # On Vercel, this might fail but we have hardcoded fallback

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    """Verify username and password against database"""
    # Try hardcoded users first (for Vercel where DB might not work)
    password_hash = hash_password(password)
    if username in HARDCODED_USERS and HARDCODED_USERS[username] == password_hash:
        return True
    
    # Try database as fallback
    try:
        init_auth_db()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT password_hash FROM teachers WHERE username = ?',
            (username,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_hash = result[0]
            return stored_hash == password_hash
        
        return False
    except Exception as e:
        print(f"Auth verify error: {e}")
        # If DB fails, fall back to hardcoded check (already done above)
        return False

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_id' not in session:
            flash('يرجى تسجيل الدخول أولًا.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_logged_in():
    """Check if user is logged in"""
    return 'teacher_id' in session

def get_current_teacher():
    """Get current logged in teacher username"""
    return session.get('teacher_id')
