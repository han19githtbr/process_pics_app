from fastapi import APIRouter, Request
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

@router.options("/segment")
async def segment_options():
    """Responde a requisições OPTIONS (CORS)."""
    return {}

@router.options("/compare")
async def compare_options():
    """Responde a requisições OPTIONS para comparação."""
    return {}

@router.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "letter-segmenter"}
