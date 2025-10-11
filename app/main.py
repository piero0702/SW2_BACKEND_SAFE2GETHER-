from fastapi import FastAPI
import logging
from app.config import settings
from app.controllers.users_controller import router as users_router
from app.controllers.reportes_controller import router as reportes_router

# Basic logging to stdout to capture debug logs from clients/repos
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API MVC con FastAPI + Supabase (PostgREST)",
)

app.include_router(users_router)
app.include_router(reportes_router)

# Opcional: health-check
@app.get("/health")
async def health():
    return {"status": "ok"}
