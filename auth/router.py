import os
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import get_db
from models import User, DataSource
from auth.schemas import RegisterRequest, LoginRequest, AuthResponse, AuthStatusResponse
from auth.security import hash_password, verify_password, create_access_token, get_current_user_email, get_current_user_email_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/v1/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(request.password)
    
    new_user = User(
        id=uuid.uuid4(),
        email=request.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(new_user.email, str(new_user.id))
    
    logger.info(f"New user registered: {request.email}")
    
    return AuthResponse(
        ok=True,
        message="Account created successfully",
        access_token=access_token
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(user.email, str(user.id))
    
    logger.info(f"User logged in: {request.email}")
    
    return AuthResponse(
        ok=True,
        message="Welcome back!",
        access_token=access_token
    )


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    request: Request,
    db: Session = Depends(get_db)
):
    email = get_current_user_email_optional(request)
    if not email:
        return AuthStatusResponse(
            authenticated=False,
            email=None,
            google=False,
            instagram=False
        )
    
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user:
        return AuthStatusResponse(
            authenticated=False,
            email=None,
            google=False,
            instagram=False
        )
    
    google_connected = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "google_analytics"
        )
    ).scalar_one_or_none() is not None
    
    instagram_connected = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none() is not None
    
    return AuthStatusResponse(
        authenticated=True,
        email=user.email,
        google=google_connected,
        instagram=instagram_connected
    )


@router.get("/google/start")
async def google_oauth_start():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(code: str, db: Session = Depends(get_db)):
    import httpx
    
    logger.info(f"[OAUTH] Google callback received. FRONTEND_URL={FRONTEND_URL}")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("[OAUTH] Missing Google OAuth credentials")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Failed to exchange Google code: {token_response.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            id_token = tokens.get("id_token")
            
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"Failed to get Google user info: {userinfo_response.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
            
            user_info = userinfo_response.json()
            email = user_info.get("email")
            google_sub = user_info.get("sub")
            
            if not email or not google_sub:
                return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
            
            user = db.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
            
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    google_sub=google_sub
                )
                db.add(user)
            else:
                user.google_sub = google_sub
            
            db.commit()
            db.refresh(user)
            
            app_token = create_access_token(user.email, str(user.id))
            
            logger.info(f"User authenticated via Google: {email}")
            
            return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=success&token={app_token}")
    
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")


@router.post("/google/disconnect")
async def disconnect_google(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    data_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "google_analytics"
        )
    ).scalar_one_or_none()
    
    if data_source:
        db.delete(data_source)
    
    if user.google_sub:
        user.google_sub = None
    
    db.commit()
    
    logger.info(f"User disconnected Google: {email}")
    
    return {"ok": True, "message": "Google account disconnected"}


@router.get("/instagram/start")
async def instagram_oauth_start(
    redirect_uri: str,
    email: str = Depends(get_current_user_email)
):
    """
    Get Instagram OAuth URL. Frontend must call this with Authorization header,
    then navigate to the returned URL.
    """
    from urllib.parse import urlencode
    init_url = f"/v1/connections/instagram/init?{urlencode({'email': email})}"
    return {"url": init_url}


@router.get("/instagram/callback")
async def instagram_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Alias for Instagram OAuth callback that redirects to the main connections endpoint.
    This provides API consistency with the Google OAuth pattern.
    """
    from urllib.parse import urlencode
    redirect_url = f"/v1/connections/instagram/callback?{urlencode({'code': code, 'state': state})}"
    return RedirectResponse(url=redirect_url)


@router.post("/instagram/disconnect")
async def disconnect_instagram(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    data_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none()
    
    if data_source:
        db.delete(data_source)
        db.commit()
    
    logger.info(f"User disconnected Instagram: {email}")
    
    return {"ok": True, "message": "Instagram account disconnected"}
