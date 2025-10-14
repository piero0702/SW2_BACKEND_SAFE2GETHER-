from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import logging
from app.config import settings
from app.controllers.users_controller import router as users_router
from app.controllers.reportes_controller import router as reportes_router
from app.controllers.adjunto_controller import router as adjuntos_router
from app.controllers.auth_controller import router as auth_router

# Basic logging to stdout to capture debug logs from clients/repos
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API MVC con FastAPI + Supabase (PostgREST)",
)

# CORS - permitir orígenes durante desarrollo (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para desarrollo; en producción restringir a orígenes confiables
    allow_credentials=True,
    # declarar explícitamente OPTIONS y otros métodos
    allow_methods=["OPTIONS", "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(users_router)
app.include_router(reportes_router)
app.include_router(auth_router)
app.include_router(adjuntos_router)

# Opcional: health-check
@app.get("/health")
async def health():
    return {"status": "ok"}


# Fallback global OPTIONS handler para preflight (evita 405 si alguna ruta no responde a OPTIONS)
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return PlainTextResponse('', status_code=200)
