#//sw2_backend_safe2gether/app/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl

BASE_DIR = Path(__file__).resolve().parent  # .../app
ENV_PATH = BASE_DIR / "settings.env"        # coloca settings.env al lado de config.py

class Settings(BaseSettings):
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_ANON_KEY: str
    SUPABASE_TABLE: str = "Usuarios"
    APP_TITLE: str = "Proxy API"
    APP_VERSION: str = "1.0.0"

    # 👇 NUEVO: agrega la key de Google
    GOOGLE_MAPS_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variables extra si las hubiera
    )

settings = Settings()
