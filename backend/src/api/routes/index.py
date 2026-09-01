from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from ..handlers.letter_segmenter_handler import LetterSegmenterHandler

router = APIRouter()
handler = LetterSegmenterHandler()


@router.post("/segment")
async def segment(request: Request):
    """Endpoint para segmentação de letras."""
    data = await request.json()
    result, status_code = handler.handle_segment(data)
    return JSONResponse(content=result, status_code=status_code)


@router.post("/compare")
async def compare(request: Request):
    """Compara duas imagens para verificar semelhança de conteúdo."""
    data = await request.json()
    result, status_code = handler.handle_compare(data)
    return JSONResponse(content=result, status_code=status_code)


@router.get("/history")
async def list_history():
    """Lista o histórico de imagens processadas persistidas."""
    return {"items": handler.list_history(limit=20)}


@router.get("/history/{item_id}")
async def get_history_item(item_id: str):
    """Retorna uma imagem processada específica do histórico."""
    item = handler.get_history_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Registro não encontrado no histórico.')
    return item


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


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "letter-segmenter"}
