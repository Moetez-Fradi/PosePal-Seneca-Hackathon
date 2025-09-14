
from pathlib import Path
from fastapi import FastAPI
import cv2
import mediapipe as mp
import numpy as np

from app.api.routes import auth
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.voice import router as coach_tts_router
from app.api.routes.ai_feedback import router as ai_feedback_router

from app.api.utils.engine import (
    set_config_handler,
    generate_frames,
)

app = FastAPI()

app.include_router(auth.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = (BASE_DIR / "../static").resolve()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/set_config")
def set_config(exercise: str):
    return set_config_handler(exercise)


@app.get("/video")
def video_feed():
    return StreamingResponse(generate_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

app.include_router(coach_tts_router)
app.include_router(ai_feedback_router)