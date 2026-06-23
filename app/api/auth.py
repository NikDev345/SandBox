import json
import os
import secrets
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.utils.jwt import create_access_token, revoke_token, verify_token


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

OAUTH_STATES = {}
PROVIDERS = {
    "google": {
        "client_id": "GOOGLE_CLIENT_ID",
        "client_secret": "GOOGLE_CLIENT_SECRET",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
    },
    "github": {
        "client_id": "GITHUB_CLIENT_ID",
        "client_secret": "GITHUB_CLIENT_SECRET",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scope": "read:user user:email",
    },
}


def public_user(user):
    return UserResponse.model_validate(user, from_attributes=True)


def token_response(user):
    token = create_access_token(
        {
            "sub": user.id,
            "email": user.email,
            "provider": user.provider
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "user": public_user(user)
    }


def get_bearer_token(authorization: str | None):
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    token = get_bearer_token(authorization)
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = AuthService.get_user_by_id(
        db,
        str(payload.get("sub"))
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists"
        )

    return user


def oauth_config(provider: str):
    config = PROVIDERS.get(provider)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unsupported OAuth provider"
        )

    client_id = os.getenv(config["client_id"])
    client_secret = os.getenv(config["client_secret"])

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider.title()} OAuth is not configured"
        )

    return config, client_id, client_secret


def oauth_redirect_uri(request: Request, provider: str):
    base_url = os.getenv("OAUTH_REDIRECT_BASE_URL")
    if base_url:
        return f"{base_url.rstrip('/')}/auth/oauth/{provider}/callback"

    return str(request.url_for("oauth_callback", provider=provider))


def post_form(url: str, payload: dict, headers: dict | None = None):
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers or {}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return dict(urllib.parse.parse_qsl(body))


def get_json(url: str, headers: dict):
    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def frontend_callback_response(user):
    payload = token_response(user)
    redirect_url = (
        "/?"
        + urllib.parse.urlencode(
            {
                "auth_token": payload["access_token"],
                "auth_user": json.dumps(
                    {
                        "id": payload["user"].id,
                        "name": payload["user"].name,
                        "email": payload["user"].email,
                        "provider": payload["user"].provider,
                    }
                )
            }
        )
    )
    return RedirectResponse(redirect_url)


@router.post("/signup")
def signup(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    user = AuthService.create_user(
        db=db,
        name=data.name.strip(),
        email=data.email,
        password=data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    return {
        "message": "User created successfully",
        "user": public_user(user)
    }


@router.post("/login")
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    user = AuthService.authenticate_user(
        db=db,
        email=data.email,
        password=data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return token_response(user)


@router.post("/guest")
def guest_login(
    db: Session = Depends(get_db)
):
    user = AuthService.create_guest_user(db)
    return token_response(user)


@router.get("/me")
def me(
    user=Depends(get_current_user)
):
    return public_user(user)


@router.get("/protected")
def protected_route(
    user=Depends(get_current_user)
):
    return {
        "ok": True,
        "user": public_user(user)
    }


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None)
):
    token = get_bearer_token(authorization)
    if not token or not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    revoke_token(token)
    return {
        "message": "Logged out"
    }


@router.get("/oauth/{provider}/login")
def oauth_login(
    provider: str,
    request: Request
):
    config, client_id, _ = oauth_config(provider)
    state = secrets.token_urlsafe(32)
    OAUTH_STATES[state] = provider

    params = {
        "client_id": client_id,
        "redirect_uri": oauth_redirect_uri(request, provider),
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }

    return RedirectResponse(
        f"{config['authorize_url']}?{urllib.parse.urlencode(params)}"
    )


@router.get("/oauth/{provider}/callback", name="oauth_callback")
def oauth_callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db)
):
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider returned error: {error}"
        )

    if not code or not state or OAUTH_STATES.pop(state, None) != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth callback state"
        )

    config, client_id, client_secret = oauth_config(provider)
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": oauth_redirect_uri(request, provider),
        "grant_type": "authorization_code",
    }

    token_data = post_form(
        config["token_url"],
        token_payload,
        {"Accept": "application/json"}
    )
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth token exchange failed"
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    profile = get_json(config["user_url"], headers)

    if provider == "github":
        email = profile.get("email")
        if not email:
            emails = get_json(config["emails_url"], headers)
            primary = next(
                (
                    item
                    for item in emails
                    if item.get("primary") and item.get("verified")
                ),
                None
            )
            email = primary.get("email") if primary else None

        name = profile.get("name") or profile.get("login")
    else:
        email = profile.get("email")
        name = profile.get("name")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth provider did not return a verified email"
        )

    user = AuthService.get_or_create_oauth_user(
        db=db,
        provider=provider,
        email=email,
        name=name or email.split("@")[0]
    )

    return frontend_callback_response(user)
