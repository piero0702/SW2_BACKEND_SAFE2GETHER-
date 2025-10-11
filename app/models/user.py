from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    user: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    psswd: str | None = None

class UserOut(BaseModel):
    id: int | None = None
    user: str
    email: str | None = None
    psswd: str | None = None


class UserUpdate(BaseModel):
    user: str | None = None
    email: EmailStr | None = None
    psswd: str | None = None


# Models para autenticación / token
class LoginRequest(BaseModel):
    user: str = Field(..., min_length=1)
    psswd: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut | None = None