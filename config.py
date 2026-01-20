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
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    # Database
    DB_PATH = os.path.join('data', 'analysis_history.db')
    
    # Cache
    CACHE_DIR = os.path.join('data', 'cache')
    CACHE_DURATION_HOURS = 24
    
    # Production settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

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
