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
from app.controllers.places_controller import router as places_router
from app.controllers.areas_interes_controller import router as areas_interes_router

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
app.include_router(places_router)
app.include_router(areas_interes_router)

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

# Endpoint para enviar alertas de riesgo manualmente (útil para testing)
@app.post("/alertas/enviar-ahora")
async def enviar_alertas_manual():
    """
    Endpoint manual para enviar alertas de riesgo a todas las áreas activas.
    En producción, esto debería ser un cron job o tarea programada.
    """
    from app.services.areas_interes_service import AreasInteresService
    from app.services.email_service import send_risk_alert_email
    from app.repositories.users_repository import UsersRepository
    from datetime import datetime
    
    areas_service = AreasInteresService()
    users_repo = UsersRepository()
    
    try:
        # Obtener todas las áreas activas
        areas_repo = areas_service.repo
        areas_activas = await areas_repo.list_active_areas()
        
        alertas_enviadas = 0
        errores = []
        
        for area in areas_activas:
            try:
                area_id = area.get("id")
                user_id = area.get("user_id")
                frecuencia = area.get("frecuencia_notificacion", "semanal")
                ultima_notif = area.get("ultima_notificacion")
                
                # Verificar si debe enviar según frecuencia
                debe_enviar = False
                dias_analisis = 7  # Por defecto semanal
                
                if frecuencia == "diario":
                    dias_analisis = 1
                    # Enviar si no hay notificación previa o fue hace más de 1 día
                    if not ultima_notif:
                        debe_enviar = True
                    else:
                        try:
                            ultima_fecha = datetime.fromisoformat(ultima_notif.replace('Z', '+00:00'))
                            if (datetime.now(ultima_fecha.tzinfo) - ultima_fecha).days >= 1:
                                debe_enviar = True
                        except:
                            debe_enviar = True
                else:  # semanal
                    dias_analisis = 7
                    if not ultima_notif:
                        debe_enviar = True
                    else:
                        try:
                            ultima_fecha = datetime.fromisoformat(ultima_notif.replace('Z', '+00:00'))
                            if (datetime.now(ultima_fecha.tzinfo) - ultima_fecha).days >= 7:
                                debe_enviar = True
                        except:
                            debe_enviar = True
                
                if not debe_enviar:
                    continue
                
                # Calcular nivel de riesgo
                riesgo = await areas_service.calcular_nivel_riesgo(area_id, dias_analisis)
                
                # Obtener email del usuario
                user = await users_repo.get_by_id(user_id)
                if not user or not user.get("email"):
                    continue
                
                # Enviar email
                enviado = await send_risk_alert_email(
                    to_email=user["email"],
                    username=user.get("user", "Usuario"),
                    area_nombre=riesgo["area_nombre"],
                    nivel_peligro=riesgo["nivel_peligro"],
                    total_reportes=riesgo["total_reportes"],
                    tipos_delitos=riesgo["tipos_delitos"],
                    dias_analisis=dias_analisis
                )
                
                if enviado:
                    # Actualizar timestamp de última notificación
                    await areas_repo.update_area(area_id, {
                        "ultima_notificacion": datetime.now().isoformat()
                    })
                    alertas_enviadas += 1
                
            except Exception as e:
                errores.append({"area_id": area.get("id"), "error": str(e)})
        
        return {
            "success": True,
            "alertas_enviadas": alertas_enviadas,
            "errores": errores,
            "total_areas_procesadas": len(areas_activas)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Fallback global OPTIONS handler para preflight (evita 405 si alguna ruta no responde a OPTIONS)
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return PlainTextResponse('', status_code=200)