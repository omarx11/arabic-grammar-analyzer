"""
Cache Manager Module
Implements caching for API responses to reduce costs and improve speed
"""
import hashlib
import json
import os
from datetime import datetime, timedelta

# Try to get cache dir from config, fallback to default
try:
    from config import get_config
    config = get_config(os.getenv('FLASK_ENV', 'production'))
    CACHE_DIR = config.CACHE_DIR if hasattr(config, 'CACHE_DIR') else os.path.join('/tmp', 'cache')
    CACHE_DURATION_HOURS = config.CACHE_DURATION_HOURS if hasattr(config, 'CACHE_DURATION_HOURS') else 24
except:
    CACHE_DIR = os.path.join('/tmp', 'cache')
    CACHE_DURATION_HOURS = 24

def init_cache():
    """Initialize cache directory"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except Exception as e:
        print(f"Cache init warning: {e}")

def get_cache_key(text):
    """Generate a unique cache key for text"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_cached_analysis(text):
    """
    Get cached analysis if available and not expired
    
    Args:
        text: The text to analyze
        
    Returns:
        dict or None: Cached analysis or None if not found/expired
    """
    try:
        init_cache()
        cache_key = get_cache_key(text)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=CACHE_DURATION_HOURS):
                # Cache expired, delete it
                os.remove(cache_file)
                return None
            
            return cache_data['analysis']
            
        except Exception:
            return None
    except Exception:
        return None  # Fail gracefully on Vercel

def save_to_cache(text, analysis):
    """
    Save analysis to cache
    
    Args:
        text: The analyzed text
        analysis: Analysis result to cache
    """
    try:
        init_cache()
        cache_key = get_cache_key(text)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'text': text[:100],  # Store snippet for reference
            'analysis': analysis
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Silently fail if caching doesn't work
    except Exception:
        pass  # Fail gracefully on Vercel

def clear_cache():
    """Clear all cached analyses"""
    try:
        init_cache()
        if not os.path.exists(CACHE_DIR):
            return
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(CACHE_DIR, filename))
                except Exception:
                    pass  # Continue even if one file fails
    except Exception as e:
        print(f"Clear cache error: {e}")

def get_cache_stats():
    """Get cache statistics"""
    try:
        init_cache()
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
        
        total_size = sum(
            os.path.getsize(os.path.join(CACHE_DIR, f)) 
            for f in cache_files
        )
        
        return {
            'count': len(cache_files),
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2)
        }
    except Exception as e:
        print(f"Cache stats error: {e}")
        return {
            'count': 0,
            'size_bytes': 0,
            'size_mb': 0
        }
