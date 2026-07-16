import uvicorn
import signal
import logging
import asyncio
from fastapi import FastAPI
from controller import register_routes
from service.scrobble import start_scrobble_job_async, stop_scrobble_job
from contextlib import asynccontextmanager

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    signal.signal(signal.SIGTERM, lambda *_: stop_scrobble_job())
    signal.signal(signal.SIGINT, lambda *_: stop_scrobble_job())
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.scrobble_task = asyncio.create_task(start_scrobble_job_async())
        yield
    
    app = FastAPI(lifespan=lifespan)
    register_routes(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
