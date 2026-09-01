from fastapi import Request
from fastapi.responses import JSONResponse

async def error_handler(request: Request, call_next):
    """Middleware para tratamento de erros."""
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                'error': 'Erro interno do servidor',
                'message': str(e)
            }
        )