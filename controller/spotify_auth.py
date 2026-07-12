from fastapi import APIRouter, HTTPException, Request
from fastapi.routing import RedirectResponse
import os
from urllib.parse import urlencode
import secrets
from service.spotify_authenticator import exchange_spotify_tokens

REDIRECT_URL = "/auth/spotify/callback"
AUTH_COOKIE_KEY = "spotify_oauth_state"

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

router = APIRouter(prefix="/auth/spotify", tags=["spotify-auth"])

@router.get("/login")
def login():
  state = secrets.token_urlsafe(32)

  response = RedirectResponse(
    url = "https://accounts.spotify.com/authorize",
    params = urlencode({
      "client_id": client_id,
      "response_type": "code",
      "redirect_uri": REDIRECT_URL,
      "scope": "user-read-currently-playing",
      "state": state
    }),
    status_code = 302
  )

  response.set_cookie(
    key = AUTH_COOKIE_KEY,
    value = state,
    httponly=True,
    max_age = 600,
    samesite = "lax"
  )

  return response

@router.get("/callback")
def callback(request: Request, code: str | None = None, state: str | None = None):
  cookie_state = request.cookies.get(AUTH_COOKIE_KEY)

  if not state or not cookie_state or state != cookie_state:
    raise HTTPException(status_code = 400, detail = "Invalid OAuth state")
  
  exchange_spotify_tokens(
    code = code,
    redirect_url = REDIRECT_URL,
    client_id = client_id,
    client_secret = client_secret
  )

  response = RedirectResponse(url="/")
  response.delete_cookie(AUTH_COOKIE_KEY)

  return response