from fastapi import WebSocket

conn: dict[str, list[WebSocket]] = {}

def add_connection(group: str, _conn: WebSocket):
    conn.setdefault(group, []).append(_conn)
    
def remove_connection(group:str, _conn: WebSocket):
    if group in conn:
        conn[group].remove(_conn)

async def broadcast_message(group:str, message: dict[str, int]):
    dead_conn = []

    for _conn in conn[group]:
        try:
            await _conn.send_json(message)
        except Exception:
            dead_conn.append(_conn)

    for _conn in dead_conn:
        conn[group].remove(_conn)