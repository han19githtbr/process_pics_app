import re

from fastapi import HTTPException, Request, Response

from ..auth import create_session_token, is_valid_session, verify_password


EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


async def login(request: Request, response: Response):
    data = await request.json()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail='Informe um e-mail válido.')

    settings = request.app.state.settings
    if not hmac_compare(email, settings.AUTH_EMAIL) or not verify_password(password, settings.AUTH_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail='E-mail ou senha incorretos.')

    response.set_cookie(
        settings.AUTH_COOKIE_NAME,
        create_session_token(settings),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.AUTH_SESSION_SECONDS,
    )
    return {'authenticated': True, 'role': 'admin'}


def hmac_compare(first: str, second: str) -> bool:
    import hmac
    return hmac.compare_digest(first.encode(), second.encode())


def logout(request: Request, response: Response):
    response.delete_cookie(request.app.state.settings.AUTH_COOKIE_NAME)
    return {'authenticated': False}


def session_status(request: Request):
    settings = request.app.state.settings
    return {'authenticated': is_valid_session(request.cookies.get(settings.AUTH_COOKIE_NAME), settings)}
