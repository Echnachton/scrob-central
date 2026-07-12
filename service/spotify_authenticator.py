import base64
import datetime
import httpx
from service.mongodb import get_db_connection
import os

SPOTIFY_TEST_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
REFRESH_BUFFER = datetime.timedelta(minutes=5)
TOKEN_DOC_ID = "spotify_token"
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

def _get_expires_at(seconds: int):
  return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)

def _request_spotify_token(data: dict):
  access_token_request = httpx.post(
    url = "https://accounts.spotify.com/api/token",
    data = data,
    headers = {
      "Authorization" : f"Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}",
      "content-type" : "application/x-www-form-urlencoded"
    }
  )

  access_token_request.raise_for_status()

  return access_token_request.json()

def exchange_spotify_token(code: str, redirect_url: str):
  data = {
    "grant_type":"authorization_code",
    "code": code,
    "redirect_uri": redirect_url
  }
  token = _request_spotify_token(data=data)
  mongo_conn = get_db_connection()

  token["_id"] = TOKEN_DOC_ID
  token["expires_at"] = _get_expires_at(seconds=token['expires_in'])
  mongo_conn.spotify_token.replace_one({"_id":TOKEN_DOC_ID}, token, upsert = True)

  return

def refresh_spotify_token(refresh_token):
  data = {
    "grant_type": "refresh_token", 
    "refresh_token": refresh_token
  }
  
  token = _request_spotify_token(data=data)

  update = {
    "access_token": token["access_token"],
    "expires_in": token["expires_in"],
    "expires_at": _get_expires_at(seconds=token['expires_in'])
  }
  if "refresh_token" in token:
      update["refresh_token"] = token["refresh_token"]

  mongo_conn = get_db_connection()

  mongo_conn.spotify_token.update_one({"_id": TOKEN_DOC_ID}, {"$set": update})

  return update['access_token']

def get_valid_access_token() -> str:
  mongo_conn = get_db_connection()
  doc = mongo_conn.spotify_token.find_one({"_id": TOKEN_DOC_ID})

  if not doc or "refresh_token" not in doc:
    raise RuntimeError("No Spotify token available")

  expires_at = doc["expires_at"]
  if expires_at.tzinfo is None:
    expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
  
  if expires_at <= datetime.datetime.now(datetime.timezone.utc) + REFRESH_BUFFER:
    return refresh_spotify_token(doc["refresh_token"])
  
  return doc["access_token"]

def handle_401_response():
  doc = get_db_connection().spotify_token.find_one({"_id": TOKEN_DOC_ID})
  token = refresh_spotify_token(doc["refresh_token"])
  response = httpx.get(SPOTIFY_TEST_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
  status_code = response.status_code
  if status_code == 401:
      raise RuntimeError("Spotify auth expired — re-login at /auth/spotify/login")
  return response