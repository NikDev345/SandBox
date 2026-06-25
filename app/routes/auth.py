from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse
from app.auth.google_oauth import oauth
from app.models.user import Users
from sqlalchemy.orm import Session
from app.utils.jwt import create_access_token
from app.database.engine import get_db

router = APIRouter()

@router.get("/auth/google")
async def login_google(request: Request):
    redirect_uri = request.url_for(
        "google_callback"
    )
    print("REDIRECT URI:", redirect_uri)
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    token = await oauth.google.authorize_access_token(
        request
    )

    user_info = token["userinfo"]

    email = user_info["email"]
    name = user_info["name"]
    google_id = user_info["sub"]
    avatar = user_info.get("picture")

    # Find user
    user = user = db.query(Users).filter(
            Users.email == email
        ).first()

    if user:
        user.provider = 'google'
        user.provider_user_id = google_id
        
        if avatar:
            user.avatar_url = avatar
            
        db.commit()
        db.refresh(user)

    else:
        user = Users(
            name=name,
            email=email,
            provider="google",
            provider_user_id=google_id,
            avatar_url=avatar
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(
        {
            'sub': user.id,
            "role": user.role
        }
    )

    response = RedirectResponse(
        "/"
    )

    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        secure=False,   # True only with HTTPS
        path="/"
    )

    return response

# GITHUB 

@router.get("/auth/github")
async def login_github(request: Request):
    redirect_uri = request.url_for("github_callback")

    return await oauth.github.authorize_redirect(
        request,
        redirect_uri
    )
    
@router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    token = await oauth.github.authorize_access_token(request)

    # Get GitHub profile
    profile = await oauth.github.get(
        "user",
        token=token
    )

    profile = profile.json()

    # Get user's emails
    emails = await oauth.github.get(
        "user/emails",
        token=token
    )

    emails = emails.json()

    email = None

    for item in emails:
        if item.get("primary"):
            email = item["email"]
            break

    if not email:
        email = emails[0]["email"]

    github_id = str(profile["id"])

    name = profile.get("name") or profile["login"]

    avatar = profile.get("avatar_url")

    user = db.query(Users).filter(
        Users.email == email
    ).first()

    if user:
        user.provider = 'github'
        user.provider_user_id = github_id
        
        if avatar:
            user.avatar_url = avatar
            
        db.commit()
        db.refresh(user)
    
    else:
        user = Users(
            name=name,
            email=email,
            provider="github",
            provider_user_id=github_id,
            avatar_url=avatar
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(
        {
            "sub": user.id,
            "role": user.role
        }
    )

    response = RedirectResponse("/")

    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    return response