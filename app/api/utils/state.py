from typing import List, Dict

CURRENT_CUES: List[str] = []

PERSONA: str | None = None

def set_persona(name: str):
    global PERSONA
    PERSONA = name

LAST_TTS_AT: float = 0.0
LAST_TTS_PER_KEY: Dict[str, float] = {}
TTS_COOLDOWN_GLOBAL: float = 5.0
TTS_COOLDOWN_PER_KEY: float = 5.0

LAST_REP_SEEN: int = 0
LAST_REP_SPOKEN: int = 0
TTS_COOLDOWN_REP: float = 1.2

SET_ACTIVE: bool = False
SET_START_TIME: float = 0.0
SET_END_TIME: float = 0.0
SET_MISTAKES: list[str] = []
LAST_SET_SUMMARY: dict | None = None

REST_START_TIME: float = 0.0

FEEDBACK_READY: bool = False
FEEDBACK_SEQ: int = 0 

CURRENT_USER: str | None = None
LAST_SET_SUMMARY: dict | None = None
LAST_REST_SUMMARY: dict | None = None

WORKOUTS_BUFFER = []
