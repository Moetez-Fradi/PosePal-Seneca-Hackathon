import os
import time
import uuid
import httpx
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from app.api.utils import state
from app.api.prompts import cute, harsh

router = APIRouter(prefix="/ai", tags=["ai"])

VOICE_DIR = Path("../../../scripts/piper-voices")
PERSONA_TO_MODEL = {
    "default": VOICE_DIR / "en_US-libritts-high.onnx",
    "goggins": VOICE_DIR / "en_US-joe-medium.onnx",
    "barbie":  VOICE_DIR / "en_US-amy-medium.onnx",
}

# parents[2] == app/
BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_TMP = (BASE_DIR / "static" / "tmp").resolve()
STATIC_TMP.mkdir(parents=True, exist_ok=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class FeedbackIn(BaseModel):
    exercise: Optional[str] = None
    reps: Optional[int] = None
    duration: Optional[float] = None
    mistakes: Optional[List[str]] = None
    persona: Optional[str] = None


def _default_payload_from_state():
    """
    Build a default payload from the last completed set summary.
    Returns None if we have no summary yet.
    """
    if state.LAST_SET_SUMMARY:
        base = dict(state.LAST_SET_SUMMARY)  # shallow copy
        base.setdefault("persona", getattr(state, "PERSONA", "default"))
        return base
    return None


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown duration"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _build_prompt(payload: dict) -> str:
    exercise = payload.get("exercise", "exercise")
    reps = payload.get("reps", 0)
    duration = payload.get("duration", None)
    mistakes = payload.get("mistakes", []) or []
    duration_str = _fmt_duration(duration)

    lines = [
        f"Exercise: {exercise}",
        f"Reps: {reps}",
        f"Duration: {duration_str}",
    ]
    if mistakes:
        lines.append("Frequent issues: " + ", ".join(mistakes))
    else:
        lines.append("Frequent issues: none detected")

    return "\n".join(lines)


async def _call_openrouter(prompt: str, persona: str) -> str:
    """
    Calls OpenRouter for a concise, 1–3 sentence feedback.
    Falls back to a stock line if OPENROUTER_API_KEY is missing.
    """
    if not OPENROUTER_API_KEY:
        return "Nice set! Keep your core tight and aim for the same depth next set."

    model = "openrouter/anthropic/claude-3.5-haiku"
    system = (
        "You are a concise fitness coach. "
        "Return 1–3 short sentences: 1) praise/motivation, 2) one actionable cue, 3) a target for next set. "
        "Avoid emojis. Keep under 40 words."
    )
    style = {
        "default": "Neutral, supportive.",
        "goggins": harsh.PROMPT,
        "barbie":  cute.PROMPT,
    }.get(persona, "Neutral, supportive.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "AI-Coach",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system + " Style: " + style},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                              headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text.strip()


def _piper_tts(text: str, persona: str) -> str:
    model = PERSONA_TO_MODEL.get(persona or "default", PERSONA_TO_MODEL["default"])
    if not model.exists():
        raise HTTPException(status_code=500, detail=f"Piper model not found for persona '{persona}'")

    uid = uuid.uuid4().hex[:10]
    out_path = STATIC_TMP / f"feedback_{persona}_{uid}.wav"

    subprocess.run(
        ["piper-tts", "--model", str(model), "--output_file", str(out_path)],
        input=text.encode("utf-8"),
        check=True
    )

    return f"/static/tmp/{out_path.name}"

@router.get("/feedback/status")
def feedback_status():
    """
    check if new feedback is ready.
    """
    return {"ready": state.FEEDBACK_READY, "seq": state.FEEDBACK_SEQ}


@router.post("/feedback")
async def feedback_endpoint(
    body: FeedbackIn | None = Body(default=None),
    force: bool = Query(False, description="generate anyway"),
):
    """
    generates the feedback text and says it once.
    """
    if not force:
        if not state.FEEDBACK_READY or not state.LAST_SET_SUMMARY:
            return {"audio_url": None, "text": None, "seq": state.FEEDBACK_SEQ}

    state.FEEDBACK_READY = False
    seq = state.FEEDBACK_SEQ

    payload = body.dict() if body else None
    if not payload:
        payload = _default_payload_from_state()
        if not payload:
            raise HTTPException(status_code=400, detail="No payload and no LAST_SET_SUMMARY available.")
    payload.setdefault("persona", getattr(state, "PERSONA", "default"))

    prompt = _build_prompt(payload)
    text = await _call_openrouter(prompt, payload["persona"])
    
    audio_url = _piper_tts(text, payload["persona"])

    state.LAST_FEEDBACK = {"text": text, "audio_url": audio_url, "persona": payload["persona"], "seq": seq}

    return state.LAST_FEEDBACK


@router.get("/feedback/last")
def feedback_last():
    return getattr(state, "LAST_FEEDBACK", {"status": "no_feedback"})
