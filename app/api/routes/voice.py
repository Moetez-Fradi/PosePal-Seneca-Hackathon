from fastapi import APIRouter, Query
import time
import app.api.utils.state as state

router = APIRouter(prefix="", tags=["tts"])

CUE_TEXT_TO_KEY = [
    ("get on the floor", "GET_ON_FLOOR"),
    ("straight plank",   "HOLD_PLANK"),
    ("hands closer",     "HANDS_CLOSER"),
    ("hands wider",      "HANDS_WIDER"),
    ("hands under",      "HANDS_UNDER_SHOULDERS"),
    ("lift hips",        "LIFT_HIPS"),
    ("lower hips",       "LOWER_HIPS"),
    ("go lower",         "GO_LOWER"),
    ("show knees/ankles", "STEP_BACK"),
    ("deeper",            "SQUAT_GO_DEEPER"),
    ("chest up",          "SQUAT_CHEST_UP"),
    ("left knee out",     "SQUAT_KNEE_OUT_LEFT"),
    ("right knee out",    "SQUAT_KNEE_OUT_RIGHT"),
]

def cue_key_from_text(msg: str) -> str | None:
    low = msg.strip().lower()
    for needle, key in CUE_TEXT_TO_KEY:
        if needle in low:
            return key
    return None

def _cue_url(persona: str, cue_key: str) -> str:
    return f"/static/tts/{persona}/{cue_key.lower()}.wav"

def _rep_url(persona: str, n: int) -> str:
    return f"/static/tts/{persona}/rep_{n}.wav"

@router.get("/coach_cue")
def coach_cue():
    now = time.monotonic()
    if state.LAST_REP_SEEN > state.LAST_REP_SPOKEN:
        if now - state.LAST_TTS_AT >= state.TTS_COOLDOWN_REP:
            n = state.LAST_REP_SEEN
            url = _rep_url(state.PERSONA, n)
            state.LAST_REP_SPOKEN = n
            state.LAST_TTS_AT = now
            return {"url": url, "persona": state.PERSONA, "key": f"REP_{n}", "text": str(n)}
    if now - state.LAST_TTS_AT < state.TTS_COOLDOWN_GLOBAL:
        return {"url": None}
    for msg in state.CURRENT_CUES:
        cue_key = cue_key_from_text(msg)
        if not cue_key:
            continue
        last_for_key = state.LAST_TTS_PER_KEY.get(cue_key, 0.0)
        if now - last_for_key < state.TTS_COOLDOWN_PER_KEY:
            continue
        url = _cue_url(state.PERSONA, cue_key)
        state.LAST_TTS_PER_KEY[cue_key] = now
        state.LAST_TTS_AT = now
        return {"url": url, "persona": state.PERSONA, "key": cue_key, "text": msg}
    return {"url": None}

@router.get("/set_persona")
def set_persona_route(name: str = Query(..., pattern="^(default|goggins|barbie)$")):
    state.set_persona(name)
    return {"status": "ok", "persona": name}
