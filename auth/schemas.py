from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    ok: bool
    message: str = ""
    access_token: str | None = None


class ProviderStatus(BaseModel):
    connected: bool
    email: str | None = None


class AuthStatusResponse(BaseModel):
    authenticated: bool
    email: str | None = None
    providers: dict[str, ProviderStatus] = {}
