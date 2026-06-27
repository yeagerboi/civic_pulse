from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from authlib.integrations.starlette_client import OAuth
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.schemas.user import LocalUserCreate, LocalUserLogin

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/google/login")
async def login_google(request: Request, action: str = "login"):
    request.session["auth_action"] = action
    # Build redirect URI dynamically
    redirect_uri = str(request.url_for('auth_google'))
    # Ensure it uses https in production
    if "localhost" not in redirect_uri and "127.0.0.1" not in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # Force HTTPS redirect_uri for validation just like in login
        redirect_uri = str(request.url_for('auth_google'))
        if "localhost" not in redirect_uri and "127.0.0.1" not in redirect_uri:
            redirect_uri = redirect_uri.replace("http://", "https://")
            
        token = await oauth.google.authorize_access_token(request, redirect_uri=redirect_uri)
    except Exception as e:
        print(f"OAuth Error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not get user info")
        
    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("sub")
    picture = user_info.get("picture")
    
    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    action = request.session.get("auth_action", "login")
    
    if action == "login" and not user:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=AccountNotFound")
    
    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=picture,
            role="citizen"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    # Generate JWT
    access_token = create_access_token(data={"sub": user.email})
    
    # Redirect to frontend dashboard based on role
    if user.role == "admin":
        redirect_url = f"{settings.FRONTEND_URL}/admin/queue"
    else:
        redirect_url = f"{settings.FRONTEND_URL}/my-reports"
        
    response = RedirectResponse(url=redirect_url)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return response

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "avatar_url": current_user.avatar_url
    }

@router.get("/logout")
async def logout():
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/")
    response.delete_cookie("access_token", samesite="none", secure=True, path="/")
    return response

@router.post("/local/signup")
async def local_signup(user_in: LocalUserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "citizen"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email})
    response = Response(status_code=200, content='{"message": "Signup successful"}', media_type="application/json")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return response

@router.post("/local/login")
async def local_login(user_in: LocalUserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": user.email})
    
    # We return the user info and also set the cookie
    response = Response(status_code=200, content=f'{{"role": "{user.role}"}}', media_type="application/json")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return response
