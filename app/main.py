# //sw2_backend_safe2gether/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import httpx
import os
import logging

from app.config import settings
from app.controllers.users_controller import router as users_router
from app.controllers.reportes_controller import router as reportes_router
from app.controllers.auth_controller import router as auth_router

# Basic logging to stdout to capture debug logs from clients/repos
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API MVC con FastAPI + Supabase (PostgREST)",
)

# CORS - permitir orígenes durante desarrollo (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Solo para dev. En prod restringe orígenes confiables.
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(users_router)
app.include_router(reportes_router)
app.include_router(auth_router)

# ==============================
# Health-check
# ==============================
@app.get("/health")
async def health():
    return {"status": "ok"}

# Fallback global OPTIONS handler para preflight (evita 405 si alguna ruta no responde a OPTIONS)
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return PlainTextResponse("", status_code=200)

# ==============================
# Proxy Google Places Autocomplete
# ==============================
# Lee la key desde variables de entorno o desde settings si lo tienes configurado allí
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", getattr(settings, "GOOGLE_MAPS_API_KEY", ""))

@app.get("/places/autocomplete")
async def places_autocomplete(
    q: str = Query(..., min_length=1, description="Texto a autocompletar"),
    country: str = Query("pe", min_length=2, max_length=2, description="Código de país ISO2"),
):
    """
    Proxy para Google Places Autocomplete.
    Evita CORS en Flutter Web y protege la API key en el backend.
    """
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key not configured")

    params = {
        "input": q,
        "types": "address",
        "components": f"country:{country}",
        "key": GOOGLE_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                params=params,
            )
        # Si Google responde error HTTP (no 2xx)
        r.raise_for_status()

        data = r.json()
        status = data.get("status", "UNKNOWN")
        if status != "OK":
            # Devuelve igual el cuerpo para depurar en el front
            logger.warning("Places error: %s - %s", status, data.get("error_message"))
        return data

    except httpx.HTTPError as e:
        logger.exception("Upstream Google Places error: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
