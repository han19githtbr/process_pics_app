import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


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

    # Performance
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'false').strip().lower() == 'true'
