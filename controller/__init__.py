from fastapi import FastAPI
from controller.spotify_auth import router as spotify_auth_router

def register_routes(app: FastAPI):
  app.include_router(spotify_auth_router)