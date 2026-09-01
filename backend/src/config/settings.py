import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configurações da aplicação."""
    
    # Ambiente
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Servidor
    PORT = int(os.getenv('PORT', 8000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        'ALLOWED_ORIGINS',
        'http://localhost:5173,http://localhost:5174'
    ).split(',')
    
    # OpenCV
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 1800))
    
    # Performance
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'false').lower() == 'true'