from fastapi import HTTPException, status
from typing import Any
import os
from datetime import datetime, timedelta
import secrets
from app.repositories.users_repository import UsersRepository
from app.models.user import UserCreate, UserOut, UserUpdate
from app.clients.supabase_client import SupabaseClient

# 🔐 Almacenamiento temporal de tokens de reset
# En producción, migrar a Redis o tabla en BD
_reset_tokens = {}


class UsersService:
    def __init__(self, repo: UsersRepository | None = None):
        self.repo = repo or UsersRepository()

    async def list_users(self) -> list[UserOut]:
        rows = await self.repo.list_users()
        return [UserOut(**row) for row in rows]

    async def create_user(self, payload: UserCreate) -> UserOut:
        # 1) Validación de duplicado (case-insensitive)
        existing = await self.repo.get_by_username_ci(payload.user)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario '{payload.user}' ya existe."
            )

        # 2) Crear - sanitizar payload para enviar solo columnas válidas a Supabase
        allowed = {"user", "email", "psswd"}
        raw = payload.model_dump()  # pydantic v2
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        created = await self.repo.create_user(sanitized)
        return UserOut(**created)

    async def get_user(self, user_id: int) -> UserOut:
        row = await self.repo.get_by_id(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserOut(**row)

    async def update_user(self, user_id: int, payload: UserUpdate | UserCreate) -> UserOut:
        # sanitize incoming model (UserUpdate may have None fields)
        allowed = {"user", "email", "psswd"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        updated = await self.repo.update_user(user_id, sanitized)
        # repo may return a list when Prefer=return=representation is used
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            updated = updated[0]

        return UserOut(**updated)

    async def delete_user(self, user_id: int) -> dict:
        deleted_count = await self.repo.delete_user(user_id)
        return {"deleted": deleted_count}

    async def authenticate(self, username: str, psswd: str) -> dict:
        # Buscar usuario (case-insensitive)
        rows = await self.repo.get_by_username_ci(username)
        user_row = rows[0] if isinstance(rows, list) and rows else None
        if not user_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        stored = user_row.get("psswd")
        # Simple password compare (replace with secure compare + hashing)
        if stored is None or stored != psswd:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # Crear token HMAC simple (no dependencia externa)
        import time, hmac, hashlib, base64
        secret = hashlib.sha256(str(time.time()).encode()).hexdigest()
        payload = f"{user_row.get('id')}:{user_row.get('user')}:{int(time.time())}"
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(payload.encode() + b"." + sig).decode()

        return {"access_token": token, "token_type": "bearer", "user": user_row}

    def __init__(self, repo: UsersRepository | None = None):
        self.repo = repo or UsersRepository()
        self.supabase = SupabaseClient()  # 🆕 Cliente de Supabase

    # 🆕 ====================================================================
    # MÉTODOS PARA RECUPERACIÓN DE CONTRASEÑA
    # ====================================================================

    async def request_password_reset(self, email: str) -> dict:
        """
        Solicita un reset de contraseña usando Supabase para enviar el email.
        
        Supabase enviará automáticamente un email con un link de confirmación.
        """
        try:
            # 1. Buscar usuario por email
            user = await self.repo.get_by_email(email)
            
            base_message = "Si el email existe, recibirás instrucciones para recuperar tu contraseña"
            
            if not user:
                # Usuario no existe, pero retornamos mensaje genérico
                return {"message": base_message}
            
            # 2. Generar token único
            token = secrets.token_urlsafe(32)
            
            # 3. Guardar token con metadata y expiración
            _reset_tokens[token] = {
                "user_id": user["id"],
                "email": email,
                "username": user.get("user", ""),
                "created_at": datetime.now(),
                "expires": datetime.now() + timedelta(hours=1)
            }
            
            # 4. Construir link de recuperación usando FRONTEND_URL (si está configurada)
            #    - Define FRONTEND_URL en app/settings.env, por ejemplo:
            #      FRONTEND_URL=http://localhost:61804
            frontend = os.getenv('FRONTEND_URL', 'http://localhost:52802').rstrip('/')
            reset_link = f"{frontend}/#/password-reset?token={token}"
            
            # 5. 📧 ENVIAR EMAIL CON SUPABASE
            try:
                # Usar Supabase para enviar email personalizado
                from app.services.email_service import send_password_reset_email
                await send_password_reset_email(
                    to_email=email,
                    username=user.get("user", "Usuario"),
                    reset_link=reset_link
                )
                print(f"✅ Email enviado exitosamente a {email}")
            except Exception as e:
                print(f"⚠️ Error enviando email: {str(e)}")
                # Continuar aunque falle el email (para debugging)
            
            # 6. Log para desarrollo
            print(f"\n{'='*60}")
            print(f"🔑 RECUPERACIÓN DE CONTRASEÑA")
            print(f"{'='*60}")
            print(f"📧 Email: {email}")
            print(f"👤 Usuario: {user.get('user', 'N/A')}")
            print(f"🔐 Token: {token}")
            print(f"🔗 Link: {reset_link}")
            print(f"⏰ Expira: {_reset_tokens[token]['expires'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            
            return {
                "message": base_message,
                # En desarrollo, también retornar el token para facilitar testing
                "token": token,
                "reset_link": reset_link,
                "expires_in_seconds": 3600
            }
            
        except Exception as e:
            print(f"❌ Error en request_password_reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la solicitud"
            )

    async def validate_reset_token(self, token: str) -> dict:
        """
        Valida si un token de reset es válido y no ha expirado.
        
        Raises:
            HTTPException 400: Si el token es inválido o expiró
        """
        # Verificar que el token existe
        if token not in _reset_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado"
            )
        
        token_data = _reset_tokens[token]
        
        # Verificar expiración
        if datetime.now() > token_data["expires"]:
            # Limpiar token expirado
            del _reset_tokens[token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expirado. Solicita uno nuevo."
            )
        
        # Token válido
        return {
            "valid": True,
            "email": token_data["email"],
            "user_id": token_data["user_id"],
            "username": token_data.get("username", ""),
            "expires_at": token_data["expires"].isoformat()
        }

    async def reset_password_with_token(self, token: str, new_password: str) -> dict:
        """
        Resetea la contraseña usando un token válido.
        
        Pasos:
        1. Valida el token
        2. Actualiza la contraseña en la BD
        3. Elimina el token usado (un solo uso)
        
        Raises:
            HTTPException 400: Si el token es inválido o la contraseña no cumple requisitos
            HTTPException 500: Si falla la actualización en la BD
        """
        try:
            # 1. Validar token (lanza HTTPException si es inválido)
            token_data = await self.validate_reset_token(token)
            user_id = token_data["user_id"]
            
            # 2. Validar contraseña (mínimo 6 caracteres)
            if not new_password or len(new_password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La contraseña debe tener al menos 6 caracteres"
                )
            
            # 3. Actualizar contraseña en la BD
            await self.repo.update_password(
                user_id=user_id,
                new_password=new_password
            )
            
            # 4. Eliminar token usado (un solo uso)
            del _reset_tokens[token]
            
            # 5. Log de éxito
            print(f"✅ Contraseña actualizada para usuario ID: {user_id}")
            
            return {
                "message": "Contraseña actualizada exitosamente",
                "success": True
            }
            
        except HTTPException:
            # Re-lanzar excepciones HTTP tal cual
            raise
        except Exception as e:
            # Errores inesperados
            print(f"❌ Error en reset_password_with_token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al resetear la contraseña"
            )

    async def cleanup_expired_tokens(self) -> int:
        """
        Limpia tokens expirados del almacenamiento.
        
        Útil para ejecutar periódicamente (ej: cada hora con un cron job).
        Retorna la cantidad de tokens eliminados.
        """
        now = datetime.now()
        expired_tokens = [
            token for token, data in _reset_tokens.items()
            if data["expires"] < now
        ]
        
        for token in expired_tokens:
            del _reset_tokens[token]
        
        if expired_tokens:
            print(f"🧹 Limpiados {len(expired_tokens)} tokens expirados")
        
        return len(expired_tokens)

    async def get_active_reset_tokens_count(self) -> int:
        """
        Retorna la cantidad de tokens activos (para debugging).
        """
        return len(_reset_tokens)

    async def get_users_by_ids(self, ids: list[int]) -> list[UserOut]:
        rows = await self.repo.get_by_ids(ids)
        return [UserOut(**row) for row in rows]