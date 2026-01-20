"""
Database Module
Handles storage of analysis history using SQLite
"""
import sqlite3
import json
from datetime import datetime
import os
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'analysis_history.db')

def init_db():
    """Initialize the database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
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

def save_analysis(teacher_id, student_name, text, analysis_result):
    """Save an analysis to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate unique share ID
    share_id = str(uuid.uuid4()).replace('-', '')[:16]
    
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
    
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    
    return analysis_id, share_id

def get_analysis_history(teacher_id, limit=50):
    """Get analysis history for all teachers (showing teacher name)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all analyses from all teachers, not filtered by teacher_id
    cursor.execute('''
        SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
        FROM analyses
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'share_id': row[1],
            'teacher_name': row[2],  # Add teacher name
            'student_name': row[3],
            'score': row[4],
            'error_count': row[5],
            'word_count': row[6],
            'is_public': bool(row[7]),  # Convert to proper boolean
            'created_at': row[8]
        })
    
    return history

def get_analysis_by_id(analysis_id):
    """Get a specific analysis by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_name, original_text, analysis_result, created_at
        FROM analyses
        WHERE id = ?
    ''', (analysis_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'student_name': row[0],
            'original_text': row[1],
            'analysis_result': json.loads(row[2]),
            'created_at': row[3]
        }
    
    return None

def delete_analysis(analysis_id, teacher_id):
    """Delete an analysis (with permission check)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM analyses
        WHERE id = ? AND teacher_id = ?
    ''', (analysis_id, teacher_id))
    
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    return deleted

def add_student(teacher_id, student_name):
    """Add a new student for a teacher"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO students (teacher_id, name)
            VALUES (?, ?)
        ''', (teacher_id, student_name))
        
        conn.commit()
        student_id = cursor.lastrowid
        conn.close()
        return student_id
    except sqlite3.IntegrityError:
        # Student already exists
        conn.close()
        return None

def get_students(teacher_id):
    """Get all students from all teachers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all unique students from all teachers
    cursor.execute('''
        SELECT DISTINCT name
        FROM students
        ORDER BY name ASC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    students = []
    for row in rows:
        students.append({
            'name': row[0]
        })
    
    return students

def delete_student(teacher_id, student_name):
    """Delete a student and all their analyses"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
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
        conn.close()
        return deleted
    except Exception:
        conn.close()
        return False

def get_student_analyses(teacher_id, student_name, limit=50):
    """Get all analyses for a specific student from all teachers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get analyses for this student from all teachers
    cursor.execute('''
        SELECT id, share_id, teacher_id, student_name, score, error_count, word_count, is_public, created_at
        FROM analyses
        WHERE student_name = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (student_name, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row[0],
            'share_id': row[1],
            'teacher_name': row[2],  # Add teacher name
            'student_name': row[3],
            'score': row[4],
            'error_count': row[5],
            'word_count': row[6],
            'is_public': row[7],
            'created_at': row[8]
        })
    
    return history

def get_analysis_by_share_id(share_id):
    """Get a specific analysis by share ID (for public sharing)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_name, original_text, analysis_result, created_at, is_public, share_id
        FROM analyses
        WHERE share_id = ?
    ''', (share_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'student_name': row[0],
            'original_text': row[1],
            'analysis_result': json.loads(row[2]),
            'created_at': row[3],
            'is_public': row[4],
            'share_id': row[5]
        }
    
    return None

def toggle_analysis_public(analysis_id, teacher_id):
    """Toggle the public status of an analysis"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First check if analysis belongs to teacher
    cursor.execute('SELECT is_public FROM analyses WHERE id = ? AND teacher_id = ?', (analysis_id, teacher_id))
    row = cursor.fetchone()
    
    if row:
        current_status = row[0]
        new_status = 0 if current_status else 1
        cursor.execute('UPDATE analyses SET is_public = ? WHERE id = ?', (new_status, analysis_id))
        conn.commit()
        conn.close()
        return bool(new_status)
    
    conn.close()
    return None

# Initialize database on module import
init_db()
