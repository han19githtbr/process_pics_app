import base64
import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Request

from ..config.settings import Settings


def _signature(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip('=')


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        derived = hashlib.pbkdf2_hmac(
            'sha256', password.encode(),
            base64.urlsafe_b64decode(salt + '=='), int(iterations),
        )
        return hmac.compare_digest(
            base64.urlsafe_b64encode(derived).decode().rstrip('='), expected,
        )
    except (ValueError, TypeError):
        return False


def create_password_hash(password: str, iterations: int = 310000) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    salt_value = base64.urlsafe_b64encode(salt).decode().rstrip('=')
    hash_value = base64.urlsafe_b64encode(derived).decode().rstrip('=')
    return f'pbkdf2_sha256${iterations}${salt_value}${hash_value}'


def create_session_token(settings: Settings) -> str:
    expires_at = int(time.time()) + settings.AUTH_SESSION_SECONDS
    payload = f'{expires_at}'
    return f'{payload}.{_signature(payload, settings.AUTH_SECRET_KEY)}'


def is_valid_session(token: str | None, settings: Settings) -> bool:
    if not token or '.' not in token:
        return False
    expires_at, signature = token.split('.', 1)
    if not expires_at.isdigit() or int(expires_at) < int(time.time()):
        return False
    return hmac.compare_digest(signature, _signature(expires_at, settings.AUTH_SECRET_KEY))


def require_authentication(request: Request) -> None:
    settings = request.app.state.settings
    if not is_valid_session(request.cookies.get(settings.AUTH_COOKIE_NAME), settings):
        raise HTTPException(status_code=401, detail='Sessão não autenticada.')
