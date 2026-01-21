"""
Configuration Module
Centralized configuration for production deployment
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'arabic-grammar-secret-key-2024')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Flask settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Upload settings
    UPLOAD_FOLDER = '/tmp/uploads'  # Use /tmp for Vercel serverless
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    # Database - PostgreSQL for production, SQLite for local
    DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string for production
    DB_PATH = os.path.join('/tmp', 'analysis_history.db')  # SQLite fallback (not persistent on Vercel!)
    
    # Cache
    CACHE_DIR = os.path.join('/tmp', 'cache')  # Use /tmp for Vercel
    CACHE_DURATION_HOURS = 24
    
    # Vercel/Production settings
    DEBUG = False
    TESTING = False
    IS_VERCEL = os.getenv('VERCEL', False)  # Detect if running on Vercel

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    UPLOAD_FOLDER = 'uploads'  # Local folder for development
    DB_PATH = os.path.join('data', 'analysis_history.db')  # Local SQLite DB
    DATABASE_URL = None  # Force SQLite for local development
    CACHE_DIR = os.path.join('data', 'cache')  # Local cache

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Add any production-specific settings here

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}

def get_config(env='production'):
    """Get configuration based on environment"""
    return config.get(env, config['default'])
