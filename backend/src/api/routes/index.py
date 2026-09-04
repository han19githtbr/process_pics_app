from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from ..handlers.letter_segmenter_handler import LetterSegmenterHandler
from ..auth import require_authentication
from ..handlers.auth_handler import login, logout, session_status

router = APIRouter()
handler = LetterSegmenterHandler()


@router.post('/auth/login')
async def auth_login(request: Request, response: Response):
    return await login(request, response)


@router.post('/auth/logout')
async def auth_logout(request: Request, response: Response):
    return logout(request, response)


@router.get('/auth/session')
async def auth_session(request: Request):
    return session_status(request)


auth_dependency = Depends(require_authentication)


@router.post("/segment")
async def segment(request: Request, _auth=auth_dependency):
    """Endpoint para segmentação de letras."""
    data = await request.json()
    result, status_code = handler.handle_segment(data)
    return JSONResponse(content=result, status_code=status_code)


@router.post("/compare")
async def compare(request: Request, _auth=auth_dependency):
    """Compara duas imagens para verificar semelhança de conteúdo."""
    data = await request.json()
    result, status_code = handler.handle_compare(data)
    return JSONResponse(content=result, status_code=status_code)


@router.get("/history")
async def list_history(_auth=auth_dependency):
    """Lista o histórico de imagens processadas persistidas."""
    return {"items": handler.list_history(limit=20)}


@router.get("/history/search")
async def search_history(q: str = "", _auth=auth_dependency):
    """Busca itens do histórico salvo pelo nome do arquivo ou transcrição."""
    return {"items": handler.search_history(query=q, limit=20)}


@router.post("/history/save")
async def save_history(request: Request, _auth=auth_dependency):
    """Salva manualmente uma imagem processada e suas letras no histórico."""
    data = await request.json()
    result, status_code = handler.save_history_item(data)
    return JSONResponse(content=result, status_code=status_code)


@router.get("/history/{item_id}")
async def get_history_item(item_id: str, _auth=auth_dependency):
    """Retorna uma imagem processada específica do histórico."""
    item = handler.get_history_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado no histórico.')
    return item


@router.delete("/history")
async def clear_history(_auth=auth_dependency):
    """Limpa todo o histórico de processamentos no banco de dados."""
    result, status_code = handler.clear_history()
    return JSONResponse(content=result, status_code=status_code)


@router.delete("/history/{item_id}")
async def delete_history_item(item_id: str, _auth=auth_dependency):
    """Remove um item específico do histórico no banco de dados."""
    result, status_code = handler.delete_history_item(item_id)
    return JSONResponse(content=result, status_code=status_code)


@router.options("/segment")
async def segment_options():
    """Responde a requisições OPTIONS (CORS)."""
    return {}


@router.options("/compare")
async def compare_options():
    """Responde a requisições OPTIONS para comparação."""
    return {}


@router.options("/history")
async def history_options():
    """Responde a requisições OPTIONS para o histórico."""
    return {}


@router.options("/history/{item_id}")
async def history_item_options(item_id: str):
    """Responde a requisições OPTIONS para item individual do histórico."""
    return {}


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "letter-segmenter"}
