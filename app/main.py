from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# ⚠️ CRÍTICO: Cargar settings.env desde app/
env_path = Path(__file__).parent / 'settings.env'
print(f"\n🔍 Cargando variables desde: {env_path}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"   ✅ Archivo encontrado y cargado")
else:
    print(f"   ❌ ERROR: {env_path} no existe")

# Verificar carga de variables
print("\n" + "=" * 60)
print("🔧 VERIFICACIÓN DE VARIABLES DE ENTORNO")
print("=" * 60)
print(f"✅ SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NO CONFIGURADA')[:50]}...")
print(f"✅ SUPABASE_ANON_KEY: {'Configurada ✓' if os.getenv('SUPABASE_ANON_KEY') else '❌ NO CONFIGURADA'}")
print(f"✅ SENDGRID_API_KEY: {'Configurada ✓' if os.getenv('SENDGRID_API_KEY') else '❌ NO CONFIGURADA'}")
print(f"✅ GOOGLE_MAPS_API_KEY: {'Configurada ✓' if os.getenv('GOOGLE_MAPS_API_KEY') else '❌ NO CONFIGURADA'}")
print("=" * 60 + "\n")

# Ahora importar después de cargar .env
from app.config import settings
from app.controllers.users_controller import router as users_router
from app.controllers.reportes_controller import router as reportes_router
from app.controllers.adjunto_controller import router as adjuntos_router
from app.controllers.reacciones_controller import router as reacciones_router
from app.controllers.comentarios_controller import router as comentarios_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.notas_comunidad_controller import router as notas_comunidad_router
from app.controllers.seguidores_controller import router as seguidores_router

# Basic logging to stdout to capture debug logs from clients/repos
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API MVC con FastAPI + Supabase (PostgREST)",
)

# GZip para comprimir respuestas JSON grandes
app.add_middleware(GZipMiddleware, minimum_size=1024)

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
app.include_router(reacciones_router)
app.include_router(comentarios_router)
app.include_router(notas_comunidad_router)
app.include_router(seguidores_router)

# Health check con verificación de servicios
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": {
            "supabase": "configured" if os.getenv("SUPABASE_URL") else "missing",
            "sendgrid": "configured" if os.getenv("SENDGRID_API_KEY") else "missing",
            "google_maps": "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "missing"
        }
    }

# Endpoint de prueba para SendGrid
@app.get("/test-sendgrid")
async def test_sendgrid():
    """Verifica configuración de SendGrid"""
    api_key = os.getenv("SENDGRID_API_KEY")
    
    if not api_key:
        return {
            "configured": False,
            "error": "SENDGRID_API_KEY no encontrada"
        }
    
    return {
        "configured": True,
        "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}",
        "length": len(api_key),
        "format_valid": api_key.startswith("SG.")
    }

# Fallback global OPTIONS handler para preflight (evita 405 si alguna ruta no responde a OPTIONS)
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return PlainTextResponse('', status_code=200)