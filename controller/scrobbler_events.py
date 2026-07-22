from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from service.ws_conn_manager import add_connection, remove_connection

group_name = 'scrobbler_events'
router = APIRouter(prefix="/scrobbler/events", tags=["scrobbler-events"])

@router.websocket("/ws")
async def scrobbler_events_ws(websocket: WebSocket):
  await websocket.accept()
  add_connection(group_name, websocket)

  try:
    while True:
      await websocket.receive_text()
  except WebSocketDisconnect:
    pass
  finally:
    remove_connection(group_name, websocket)
    await websocket.close()