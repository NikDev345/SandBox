from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import RedirectResponse
from app.auth.google_oauth import oauth
from app.models.user import Users
from sqlalchemy.orm import Session
from app.utils.jwt import create_access_token
from app.database.engine import get_db
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/auth/google")
async def login_google(request: Request):
    request.session.pop("oauth_mode", None)
    request.session.pop("current_user_id", None)

    for key in list(request.session.keys()):
        if key.startswith("_state_google_"):
            request.session.pop(key)
            
    redirect_uri = request.url_for(
        "google_callback"
    )
    response = await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )
    return response


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
    
    oauth_mode = request.session.get("oauth_mode")
    current_user_id = request.session.get("current_user_id")
    
    if oauth_mode == "connect":
        user = db.query(Users).filter(
            Users.id == current_user_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
            
        existing = db.query(Users).filter(
            Users.google_id == google_id
        ).first()
        
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=400,
                detail="This Google account is already connected to another account."
            )
            
        user.google_connected = True
        user.google_id = google_id
        user.google_email = email
        user.google_name = name
        user.google_avatar = avatar

        user.provider = "google"

        if not user.name_customized:
            user.name = name

        if not user.email_customized:
            user.email = email

        if not user.avatar_customized:
            user.avatar_url = avatar

        db.commit()
        db.refresh(user)
        request.session.pop("oauth_mode", None)
        request.session.pop("current_user_id", None)

        return RedirectResponse("/#settings-accounts")

    # Find user by google id
    user = db.query(Users).filter(
        Users.google_id == google_id
    ).first()
    
    if user:
        user.google_connected = True
        user.google_email = email
        user.google_name = name
        user.google_avatar = avatar

        user.provider = "google"

        if not user.name_customized:
            user.name = name

        if not user.email_customized:
            user.email = email

        if not user.avatar_customized:
            user.avatar_url = avatar

        db.commit()
        db.refresh(user)

    # if user not found, then find user by local email
    if not user:
        user = db.query(Users).filter(
            Users.email == email
        ).first()
        
        # if user found by local email, then connect it with google
        if user:
            user.google_connected = True
            user.google_id = google_id
            user.google_email = email
            user.google_name = name
            user.google_avatar = avatar

            user.provider = "google"

            if not user.name_customized:
                user.name = name

            if not user.email_customized:
                user.email = email

            if not user.avatar_customized:
                user.avatar_url = avatar
            
            db.commit()
            db.refresh(user)
            
    # if user not found by local email, then create a brand new user
    if not user:
        user = Users(
            name=name,
            email=email,
            avatar_url=avatar,
            
            local_name=name,
            local_email=email,
            local_avatar=avatar,

            provider="google",
            provider_user_id=google_id,
            google_connected=True,
            google_id=google_id,
            google_email=email,
            google_name=name,
            google_avatar=avatar,
            
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
    request.session.pop("oauth_mode", None)
    request.session.pop("current_user_id", None)

    for key in list(request.session.keys()):
        if key.startswith("_state_github_"):
            request.session.pop(key)
            
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

    # GitHub profile
    profile = await oauth.github.get(
        "user",
        token=token
    )
    profile = profile.json()

    # User emails
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

    if not email and emails:
        email = emails[0]["email"]

    github_id = str(profile["id"])
    name = profile.get("name") or profile["login"]
    avatar = profile.get("avatar_url")
    oauth_mode = request.session.get("oauth_mode")
    current_user_id = request.session.get("current_user_id")

    if oauth_mode == "connect":

        user = db.query(Users).filter(
            Users.id == current_user_id
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        existing = db.query(Users).filter(
            Users.github_id == github_id
        ).first()

        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=400,
                detail="This GitHub account is already connected to another account."
            )

        user.github_connected = True
        user.github_id = github_id
        user.github_email = email
        user.github_name = name
        user.github_avatar = avatar

        user.provider = "github"

        if not user.google_connected:

            if not user.name_customized:
                user.name = name

            if not user.email_customized:
                user.email = email

            if not user.avatar_customized:
                user.avatar_url = avatar

        db.commit()
        db.refresh(user)

        request.session.pop("oauth_mode", None)
        request.session.pop("current_user_id", None)

        return RedirectResponse("/#settings-accounts")

    # --------------------------------------------------------
    # 1. Check if GitHub account is already linked
    # --------------------------------------------------------

    user = db.query(Users).filter(
        Users.github_id == github_id
    ).first()

    # Existing GitHub account
    if user:
        user.github_connected = True
        user.github_email = email
        user.github_name = name
        user.github_avatar = avatar
        user.provider = "github"
        
        if not user.google_connected:

            if not user.name_customized:
                user.name = name

            if not user.email_customized:
                user.email = email

            if not user.avatar_customized:
                user.avatar_url = avatar

        db.commit()
        db.refresh(user)
    # --------------------------------------------------------
    # 2. If not, check if a user already exists with this email
    # --------------------------------------------------------

    if not user:
        user = db.query(Users).filter(
            Users.email == email
        ).first()

        if user:
            # Link GitHub account

            user.github_connected = True
            user.github_id = github_id
            user.github_email = email
            user.github_name = name
            user.github_avatar = avatar

            user.provider = "github"
            
            if not user.google_connected:

                if not user.name_customized:
                    user.name = name

                if not user.email_customized:
                    user.email = email

                if not user.avatar_customized:
                    user.avatar_url = avatar
            

            db.commit()
            db.refresh(user)

    # --------------------------------------------------------
    # 3. Create a new user
    # --------------------------------------------------------

    if not user:
        user = Users(
            name=name,
            email=email,
            avatar_url=avatar,
            
            local_name=name,
            local_email=email,
            local_avatar=avatar,

            provider="github",
            provider_user_id=github_id,

            github_connected=True,
            github_id=github_id,
            github_email=email,
            github_name=name,
            github_avatar=avatar,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # --------------------------------------------------------
    # Login
    # --------------------------------------------------------

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

@router.get("/settings/connect/google")
async def connect_google(
    request: Request,
    current_user=Depends(get_current_user)
):
    request.session["oauth_mode"] = "connect"
    request.session["current_user_id"] = current_user["sub"]

    redirect_uri = request.url_for("google_callback")

    response = await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )
    return response
@router.get("/settings/connect/github")
async def connect_github(
    request: Request,
    current_user=Depends(get_current_user)
):
    request.session["oauth_mode"] = "connect"
    request.session["current_user_id"] = current_user["sub"]

    redirect_uri = request.url_for("github_callback")

    return await oauth.github.authorize_redirect(
        request,
        redirect_uri
    )
    
@router.post("/settings/disconnect/google")
async def disconnect_google(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Remove Google account
    user.google_connected = False
    user.google_id = None
    user.google_email = None
    user.google_name = None
    user.google_avatar = None

    # Provider becomes GitHub if connected, otherwise Local
    if user.github_connected:
        user.provider = "github"

        if not user.name_customized:
            user.name = user.github_name

        if not user.email_customized:
            user.email = user.github_email

        if not user.avatar_customized:
            user.avatar_url = user.github_avatar

    else:
        user.provider = "local"

        if not user.name_customized:
            user.name = user.local_name

        if not user.email_customized:
            user.email = user.local_email

        if not user.avatar_customized:
            user.avatar_url = user.local_avatar

    db.commit()
    db.refresh(user)

    return {"message": "Google disconnected successfully"}

@router.post("/settings/disconnect/github")
async def disconnect_github(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(Users).filter(
        Users.id == current_user["sub"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Remove GitHub account
    user.github_connected = False
    user.github_id = None
    user.github_email = None
    user.github_name = None
    user.github_avatar = None

    # Google has priority
    if user.google_connected:
        user.provider = "google"

        if not user.name_customized:
            user.name = user.google_name

        if not user.email_customized:
            user.email = user.google_email

        if not user.avatar_customized:
            user.avatar_url = user.google_avatar

    else:
        user.provider = "local"

        if not user.name_customized:
            user.name = user.local_name

        if not user.email_customized:
            user.email = user.local_email

        if not user.avatar_customized:
            user.avatar_url = user.local_avatar

    db.commit()
    db.refresh(user)

    return {"message": "GitHub disconnected successfully"}