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
    print(token.items())
    user_info = token["userinfo"]

    email = user_info["email"]
    name = user_info["name"]
    google_id = user_info["sub"]
    avatar = user_info.get("picture")

    # Find user
    user = user = db.query(Users).filter(
            Users.email == email
        ).first()

    if not user:
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
        "access_token",
        jwt_token,
        httponly=True
    )

    return response
