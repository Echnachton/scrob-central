import uvicorn
from fastapi import FastAPI
from controller import register_routes
import threading
import signal
from service.scrobble import start_scrobble_job, stop_scrobble_job

def main():
    print("Hello from scrob-central!")
    signal.signal(signal.SIGTERM, lambda *_: stop_scrobble_job())
    signal.signal(signal.SIGINT, lambda *_: stop_scrobble_job())
    threading.Thread(target=start_scrobble_job, daemon=True).start()
    
    app = FastAPI()
    register_routes(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
