# pylint: skip-file
"""
Servidor principal da API de segmentação de letras.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Usar imports relativos
from .config.settings import Settings
from .api.routes import router
from .api.middleware.error_handler import error_handler

settings = Settings()

# Criar aplicação FastAPI
app = FastAPI(
    title="Letter Segmenter API",
    description="API para segmentação de letras em imagens",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de erro
app.middleware("http")(error_handler)

# Incluir rotas com prefixo /api
app.include_router(router, prefix="/api")

# Rota raiz
@app.get("/")
async def root():
    """Rota raiz da API."""
    return {
        "service": "Letter Segmenter API",
        "version": "1.0.0",
        "status": "ok"
    }

# Rota health check (fora do /api)
@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "letter-segmenter"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
