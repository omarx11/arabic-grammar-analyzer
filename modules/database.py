"""
Database Module
Handles storage of analysis history using PostgreSQL (production) or SQLite (development)
"""
import sqlite3
import json
from datetime import datetime
import os
import uuid

# Try to get DB configuration from config
try:
    from config import get_config
    config = get_config(os.getenv('FLASK_ENV', 'production'))
    DATABASE_URL = getattr(config, 'DATABASE_URL', None)
    DB_PATH = getattr(config, 'DB_PATH', os.path.join('/tmp', 'analysis_history.db'))
except:
    DATABASE_URL = os.getenv('DATABASE_URL')
    DB_PATH = os.path.join('/tmp', 'analysis_history.db')

# Import PostgreSQL driver if DATABASE_URL is set
USE_POSTGRES = DATABASE_URL is not None
if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("Warning: psycopg2 not installed, falling back to SQLite")
        USE_POSTGRES = False

def get_db_connection():
    """Get database connection based on environment"""
    if USE_POSTGRES and DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database with required tables"""
    try:
        if USE_POSTGRES:
            # PostgreSQL initialization
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create analyses table with PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id SERIAL PRIMARY KEY,
                    share_id TEXT UNIQUE NOT NULL,
                    teacher_id TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    analysis_result TEXT NOT NULL,
                    score INTEGER,
                    error_count INTEGER,
                    word_count INTEGER,
                    is_public INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    teacher_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(teacher_id, name)
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
        else:
            # SQLite initialization
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create analyses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    share_id TEXT UNIQUE NOT NULL,
                    teacher_id TEXT NOT NULL,
                    student_name TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    analysis_result TEXT NOT NULL,
                    score INTEGER,
                    error_count INTEGER,
                    word_count INTEGER,
                    is_public INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(teacher_id, name)
                )
            ''')
            
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

def save_analysis(teacher_id, student_name, text, analysis_result):
    """Save an analysis to the database"""
    try:
        init_db()  # Ensure DB exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique share ID
        share_id = str(uuid.uuid4()).replace('-', '')[:16]
        
        if USE_POSTGRES:
            # PostgreSQL syntax with RETURNING
            cursor.execute('''
                INSERT INTO analyses 
                (share_id, teacher_id, student_name, original_text, analysis_result, score, error_count, word_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                share_id,
                teacher_id,
                student_name,
                text,
                json.dumps(analysis_result, ensure_ascii=False),
                analysis_result.get('score', 0),
                len(analysis_result.get('errors', [])),
                analysis_result.get('word_count', 0)
            ))
            analysis_id = cursor.fetchone()['id']
        else:
            # SQLite syntax
            cursor.execute('''
                INSERT INTO analyses 
                (share_id, teacher_id, student_name, original_text, analysis_result, score, error_count, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                share_id,
                teacher_id,
                student_name,
                text,
                json.dumps(analysis_result, ensure_ascii=False),
                analysis_result.get('score', 0),
                len(analysis_result.get('errors', [])),
                analysis_result.get('word_count', 0)
            ))
            analysis_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return analysis_id, share_id
    except Exception as e:
        print(f"Database save error: {e}")
        import traceback
        traceback.print_exc()
        # Return dummy values if DB fails
        return 0, str(uuid.uuid4()).replace('-', '')[:16]

def get_analysis_history(teacher_id, limit=50):
    """Get analysis history for all teachers (showing teacher name)"""
    try:
        init_db()  # Ensure DB exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all analyses from all teachers, not filtered by teacher_id
        if USE_POSTGRES:
            cursor.execute('''
                SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT %s
            ''', (limit,))
            rows = cursor.fetchall()
        else:
            cursor.execute('''
                SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        history = []
        if USE_POSTGRES:
            # PostgreSQL returns dict rows
            for row in rows:
                history.append({
                    'id': row['id'],
                    'share_id': row['share_id'],
                    'teacher_name': row['teacher_id'],
                    'student_name': row['student_name'],
                    'score': row['score'],
                    'error_count': row['error_count'],
                    'word_count': row['word_count'],
                    'is_public': bool(row['is_public']),
                    'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
                })
        else:
            # SQLite returns tuple rows
            for row in rows:
                history.append({
                    'id': row[0],
                    'share_id': row[1],
                    'teacher_name': row[2],
                    'student_name': row[3],
                    'score': row[4],
                    'error_count': row[5],
                    'word_count': row[6],
                    'is_public': bool(row[7]),
                    'created_at': row[8]
                })
        
        return history
    except Exception as e:
        print(f"Database read error: {e}")
        import traceback
        traceback.print_exc()
        return []  # Return empty list if DB fails

def get_analysis_by_id(analysis_id):
    """Get a specific analysis by ID"""
    try:
        init_db()  # Ensure DB exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                SELECT student_name, original_text, analysis_result, created_at
                FROM analyses
                WHERE id = %s
            ''', (analysis_id,))
            row = cursor.fetchone()
        else:
            cursor.execute('''
                SELECT student_name, original_text, analysis_result, created_at
                FROM analyses
                WHERE id = ?
            ''', (analysis_id,))
            row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            if USE_POSTGRES:
                return {
                    'student_name': row['student_name'],
                    'original_text': row['original_text'],
                    'analysis_result': json.loads(row['analysis_result']),
                    'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
                }
            else:
                return {
                    'student_name': row[0],
                    'original_text': row[1],
                    'analysis_result': json.loads(row[2]),
                    'created_at': row[3]
                }
        return None
    except Exception as e:
        print(f"Database read error: {e}")
        import traceback
        traceback.print_exc()
        return None

def delete_analysis(analysis_id, teacher_id):
    """Delete an analysis (with permission check)"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                DELETE FROM analyses
                WHERE id = %s AND teacher_id = %s
            ''', (analysis_id, teacher_id))
        else:
            cursor.execute('''
                DELETE FROM analyses
                WHERE id = ? AND teacher_id = ?
            ''', (analysis_id, teacher_id))
        
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        return deleted
    except Exception as e:
        print(f"Database delete error: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_student(teacher_id, student_name):
    """Add a new student for a teacher"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if USE_POSTGRES:
                cursor.execute('''
                    INSERT INTO students (teacher_id, name)
                    VALUES (%s, %s)
                    RETURNING id
                ''', (teacher_id, student_name))
                student_id = cursor.fetchone()['id']
            else:
                cursor.execute('''
                    INSERT INTO students (teacher_id, name)
                    VALUES (?, ?)
                ''', (teacher_id, student_name))
                student_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            conn.close()
            return student_id
        except Exception as integrity_error:
            # Student already exists
            cursor.close()
            conn.close()
            return None
    except Exception as e:
        print(f"Database add student error: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_students(teacher_id):
    """Get all students from all teachers"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all unique students from all teachers
        cursor.execute('''
            SELECT DISTINCT name
            FROM students
            ORDER BY name ASC
        ''')
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        students = []
        if USE_POSTGRES:
            for row in rows:
                students.append({'name': row['name']})
        else:
            for row in rows:
                students.append({'name': row[0]})
        
        return students
    except Exception as e:
        print(f"Database get students error: {e}")
        import traceback
        traceback.print_exc()
        return []

def delete_student(teacher_id, student_name):
    """Delete a student and all their analyses"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if USE_POSTGRES:
                # Delete all analyses for this student
                cursor.execute('''
                    DELETE FROM analyses
                    WHERE teacher_id = %s AND student_name = %s
                ''', (teacher_id, student_name))
                
                # Delete the student
                cursor.execute('''
                    DELETE FROM students
                    WHERE teacher_id = %s AND name = %s
                ''', (teacher_id, student_name))
            else:
                # Delete all analyses for this student
                cursor.execute('''
                    DELETE FROM analyses
                    WHERE teacher_id = ? AND student_name = ?
                ''', (teacher_id, student_name))
                
                # Delete the student
                cursor.execute('''
                    DELETE FROM students
                    WHERE teacher_id = ? AND name = ?
                ''', (teacher_id, student_name))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            conn.close()
            return deleted
        except Exception:
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"Database delete student error: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_student_analyses(teacher_id, student_name, limit=50):
    """Get all analyses for a specific student from all teachers"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get analyses for this student from all teachers
        if USE_POSTGRES:
            cursor.execute('''
                SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
                FROM analyses
                WHERE student_name = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (student_name, limit))
        else:
            cursor.execute('''
                SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
                FROM analyses
                WHERE student_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (student_name, limit))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        if USE_POSTGRES:
            for row in rows:
                history.append({
                    'id': row['id'],
                    'share_id': row['share_id'],
                    'teacher_name': row['teacher_id'],
                    'student_name': row['student_name'],
                    'score': row['score'],
                    'error_count': row['error_count'],
                    'word_count': row['word_count'],
                    'is_public': bool(row['is_public']),
                    'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
                })
        else:
            for row in rows:
                history.append({
                    'id': row[0],
                    'share_id': row[1],
                    'teacher_name': row[2],
                    'student_name': row[3],
                    'score': row[4],
                    'error_count': row[5],
                    'word_count': row[6],
                    'is_public': row[7],
                    'created_at': row[8]
                })
        
        return history
    except Exception as e:
        print(f"Database get student analyses error: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_analysis_by_share_id(share_id):
    """Get a specific analysis by share ID (for public sharing)"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if USE_POSTGRES:
            cursor.execute('''
                SELECT student_name, original_text, analysis_result, created_at, is_public, share_id
                FROM analyses
                WHERE share_id = %s
            ''', (share_id,))
            row = cursor.fetchone()
        else:
            cursor.execute('''
                SELECT student_name, original_text, analysis_result, created_at, is_public, share_id
                FROM analyses
                WHERE share_id = ?
            ''', (share_id,))
            row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            if USE_POSTGRES:
                return {
                    'student_name': row['student_name'],
                    'original_text': row['original_text'],
                    'analysis_result': json.loads(row['analysis_result']),
                    'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at']),
                    'is_public': row['is_public'],
                    'share_id': row['share_id']
                }
            else:
                return {
                    'student_name': row[0],
                    'original_text': row[1],
                    'analysis_result': json.loads(row[2]),
                    'created_at': row[3],
                    'is_public': row[4],
                    'share_id': row[5]
                }
        
        return None
    except Exception as e:
        print(f"Database get analysis by share ID error: {e}")
        import traceback
        traceback.print_exc()
        return None

def toggle_analysis_public(analysis_id, teacher_id):
    """Toggle the public status of an analysis"""
    try:
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if analysis belongs to teacher
        if USE_POSTGRES:
            cursor.execute('SELECT is_public FROM analyses WHERE id = %s AND teacher_id = %s', (analysis_id, teacher_id))
            row = cursor.fetchone()
        else:
            cursor.execute('SELECT is_public FROM analyses WHERE id = ? AND teacher_id = ?', (analysis_id, teacher_id))
            row = cursor.fetchone()
        
        if row:
            if USE_POSTGRES:
                current_status = row['is_public']
                new_status = 0 if current_status else 1
                cursor.execute('UPDATE analyses SET is_public = %s WHERE id = %s', (new_status, analysis_id))
            else:
                current_status = row[0]
                new_status = 0 if current_status else 1
                cursor.execute('UPDATE analyses SET is_public = ? WHERE id = ?', (new_status, analysis_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return bool(new_status)
        
        cursor.close()
        conn.close()
        return None
    except Exception as e:
        print(f"Database toggle public error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Initialize database on module import
init_db()
