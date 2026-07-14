import time
import logging
import httpx
from service.mongodb import get_db_connection
from service.spotify_authenticator import get_valid_access_token, handle_401_response
from schema import ScrobbleCurrentlyPlaying

NOW_PLAYING_TRACKING_ID = "now_playing_tracking_id"
SPOTIFY_ENDPOINT = "https://api.spotify.com/v1/me/player/currently-playing"
POLL_INTERVAL = 30
SCROBBLE_COMPLETE_PERCENTAGE = 80

logger = logging.getLogger(__name__)
_is_worker_running = True

def stop_scrobble_job():
  global _is_worker_running
  _is_worker_running = False
  return

def start_scrobble_job():
  while _is_worker_running:
    start = time.monotonic()
    try:
      scrobble_job()
    except Exception:
      logger.info("scrobble_job failed")
      raise

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
    logger.warning("Http 403. Log in first.")
    return
  
  if status_code == 429:
    # TODO: Implement back-off
    logger.warning("Spotify rate limit (429) — stopping scrobble worker")
    stop_scrobble_job()
    return

  response.raise_for_status()
  
  mongo_conn = get_db_connection()

  if status_code == 204:
    # TODO: Trigger an Silence Event
    mongo_conn.now_playing.delete_one({"_id":NOW_PLAYING_TRACKING_ID})
    return
  
  try:
    now_playing_doc = response.json()
    now_playing = ScrobbleCurrentlyPlaying.model_validate(now_playing_doc)
  except Exception:
    logger.error("Failed to validate now playing")
    return

  handle_scrobble(now_playing, now_playing_doc)
  handle_now_playing(now_playing_doc)

def get_scrobble_state(now_playing: ScrobbleCurrentlyPlaying):
  percentage_complete = round(now_playing.progress_ms / now_playing.item.duration_ms * 100)
  return percentage_complete > SCROBBLE_COMPLETE_PERCENTAGE

def get_should_update_scrobble_state(now_playing: ScrobbleCurrentlyPlaying):
  mongo_conn = get_db_connection()

  latest_scrobble_entry = mongo_conn.scrobble.find_one(
    {"item.id": now_playing.item.id},
    sort=[("timestamp", -1)]
  )

  last_scrobbled = (
    ScrobbleCurrentlyPlaying.model_validate(latest_scrobble_entry)
    if latest_scrobble_entry is not None
    else None
  )

  return (
    last_scrobbled is not None
    and now_playing.progress_ms is not None
    and last_scrobbled.progress_ms < now_playing.progress_ms
  )

def handle_scrobble(now_playing: ScrobbleCurrentlyPlaying, now_playing_doc: dict):
  mongo_conn = get_db_connection()

  should_scrobble = get_scrobble_state(now_playing)
  should_update_scrobble = get_should_update_scrobble_state(now_playing)
  
  if should_scrobble:
    if should_update_scrobble:
      try:
        mongo_conn.scrobble.update_one(
          {"item.id": now_playing.item.id},
          {"$set": {"progress_ms": now_playing.progress_ms}},
        )
      except Exception:
        logger.error("Failed to update scrobble")
        raise
    else:
      try:
        mongo_conn.scrobble.insert_one(now_playing_doc)
      except Exception:
        logger.error("Failed to insert scrobble")
        raise

def handle_now_playing(now_playing_doc: dict):
  mongo_conn = get_db_connection()

  now_playing_doc["_id"] = NOW_PLAYING_TRACKING_ID
  
  try:
    mongo_conn.now_playing.replace_one({"_id":NOW_PLAYING_TRACKING_ID}, now_playing_doc, upsert = True) 
  except Exception:
    logger.error("Failed to update now playing")
    raise