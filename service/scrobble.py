import signal
import time
from unittest import skip
import httpx
from service.mongodb import get_db_connection
from service.spotify_authenticator import get_valid_access_token, handle_401_response

SPOTIFY_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
POLL_INTERVAL = 30

_is_worker_running = True

def stop_scrobble_job():
  global _is_worker_running
  _is_worker_running = False
  return

def start_scrobble_job():
  signal.signal(signal.SIGTERM, stop_scrobble_job)
  signal.signal(signal.SIGINT, stop_scrobble_job)

  while _is_worker_running:
    start = time.monotonic()
    try:
      scrobble_job()
    except Exception as e:
      print(f"scrobble_job failed: {e}")

    elapsed = time.monotonic() - start
    time.sleep(max(0, POLL_INTERVAL - elapsed))
  return

def scrobble_job():
  token = get_valid_access_token()

  response = httpx.get(
    SPOTIFY_ENDPOINT,
    headers={"Authorization": f"Bearer {token}"},
  )

  status_code = response.status_code

  if status_code == 401:
    response = handle_401_response()
    status_code = response.status_code
  
  if status_code == 403:
    response.raise_for_status()
  
  if status_code == 429:
    # TODO: Implement back-off
    skip()
    return

  response.raise_for_status()
  
  mongo_conn = get_db_connection()

  if status_code == 204:
    # TODO: Trigger an Silence Event
    return
  
  try:
    mongo_conn.now_playing.insert_one(response.json())
  except Exception as e:
        raise Exception("The following error occurred: ", e)