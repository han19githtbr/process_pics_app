import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')


def _default_collection_name() -> str:
    """Use uma coleção separada em produção para não misturar os registros locais e de produção."""
    return 'processed_images_prod' if (os.getenv('ENVIRONMENT') or '').strip().lower() == 'production' else 'processed_images'


def _parse_allowed_origins(raw_value: str | None) -> List[str]:
    """Normaliza a lista de origens permitidas para uso em produção."""
    if not raw_value:
        return ['http://localhost:5173', 'http://localhost:5174']

    origins = [origin.strip() for origin in raw_value.split(',')]
    return [origin for origin in origins if origin]


class Settings:
    """Configurações da aplicação."""

    # Ambiente
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip().lower()
    DEBUG = os.getenv('DEBUG', 'true').strip().lower() == 'true'

    # Servidor
    PORT = int(os.getenv('PORT') or 8000)
    HOST = (os.getenv('HOST', '0.0.0.0') or '0.0.0.0').strip()

    # CORS
    ALLOWED_ORIGINS: List[str] = _parse_allowed_origins(
        os.getenv('ALLOWED_ORIGINS')
    )

    # OpenCV
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 1800))

    # MongoDB Atlas
    MONGODB_URI = (os.getenv('MONGODB_URI') or '').strip()
    MONGODB_DB_NAME = (os.getenv('MONGODB_DB_NAME') or 'pattern_checker').strip()
    MONGODB_COLLECTION_NAME = (os.getenv('MONGODB_COLLECTION_NAME') or _default_collection_name()).strip()

    # Performance
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'false').strip().lower() == 'true'

    # Autenticação: somente o hash da senha deve ser armazenado no ambiente.
    AUTH_EMAIL = (os.getenv('AUTH_EMAIL') or '').strip().lower()
    AUTH_PASSWORD_HASH = (os.getenv('AUTH_PASSWORD_HASH') or '').strip()
    AUTH_SECRET_KEY = (os.getenv('AUTH_SECRET_KEY') or '').strip()
    AUTH_COOKIE_NAME = 'pattern_checker_session'
    AUTH_SESSION_SECONDS = int(os.getenv('AUTH_SESSION_SECONDS', 28800))
    AUTH_COOKIE_SECURE = os.getenv('AUTH_COOKIE_SECURE', 'false').strip().lower() == 'true'
    AUTH_COOKIE_SAMESITE = os.getenv(
        'AUTH_COOKIE_SAMESITE',
        'none' if ENVIRONMENT == 'production' else 'lax',
    ).strip().lower()
