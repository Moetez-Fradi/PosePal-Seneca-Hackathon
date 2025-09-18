import os
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from openai import OpenAI

from app.api.utils import state
from app.api.prompts import cute, harsh

router = APIRouter(prefix="/ai", tags=["ai"])

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)
MODEL = "meta-llama/llama-3-8b-instruct"

APP_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = APP_DIR.parent
VOICE_DIR = (REPO_ROOT / "scripts" / "piper-voices").resolve()
STATIC_TMP = (APP_DIR / "static" / "tmp").resolve()
STATIC_TMP.mkdir(parents=True, exist_ok=True)

PERSONA_TO_MODEL = {
    "default": VOICE_DIR / "en_US-libritts-high.onnx",
    "goggins": VOICE_DIR / "en_US-joe-medium.onnx",
    "barbie": VOICE_DIR / "en_US-amy-medium.onnx",
}

class FeedbackIn(BaseModel):
    exercise: Optional[str] = None
    reps: Optional[int] = None
    duration: Optional[float] = None
    mistakes: Optional[List[str]] = None
    persona: Optional[str] = None

def _default_payload_from_state() -> Optional[dict]:
    if state.LAST_SET_SUMMARY:
        base = dict(state.LAST_SET_SUMMARY)
        base.setdefault("persona", getattr(state, "PERSONA", "default"))
        return base
    return None

def _fmt_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "unknown"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"

def _build_prompt(payload: dict) -> str:
    exercise = payload.get("exercise", "exercise")
    reps = payload.get("reps", 0)
    duration = _fmt_duration(payload.get("duration"))
    mistakes = payload.get("mistakes", []) or []

    return (
        f"Exercise: {exercise}\n"
        f"Reps: {reps}\n"
        f"Duration: {duration}\n"
        f"Frequent issues: {', '.join(mistakes) if mistakes else 'none'}"
    )

def _call_openrouter(prompt: str, persona: str) -> str:
    style = {
        "default": "Neutral, supportive.",
        "goggins": harsh.PROMPT,
        "barbie": cute.PROMPT,
    }.get(persona, "Neutral, supportive.")

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise fitness coach. "
                        "Return 1–3 short sentences: "
                        "1) praise/motivation, "
                        "2) one actionable cue, "
                        "3) a target for next set. "
                        "Avoid emojis. Keep under 40 words. Don't start with 'here are three sentences' or anything. Provide directly with the sentences. "
                        f"Style: {style}"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("[LLM] fallback:", e)
        return "Keep your form tight and steady Queen! You got this."

def _piper_tts(text: str, persona: str) -> str:
    piper_bin = shutil.which("piper-tts")
    if not piper_bin:
        raise HTTPException(status_code=500, detail="piper-tts not found")
    model_path = PERSONA_TO_MODEL.get(persona, PERSONA_TO_MODEL["default"])
    if not model_path.exists():
        raise HTTPException(status_code=500, detail=f"Missing model {model_path}")
    uid = uuid.uuid4().hex[:10]
    out_path = STATIC_TMP / f"feedback_{persona}_{uid}.wav"
    subprocess.run([piper_bin, "--model", str(model_path), "--output_file", str(out_path)],
                   input=text.encode("utf-8"), check=True)
    return f"/static/tmp/{out_path.name}"

@router.get("/feedback/status")
def feedback_status():
    return {"ready": state.FEEDBACK_READY, "seq": state.FEEDBACK_SEQ}

@router.post("/feedback")
def feedback_endpoint(
    body: FeedbackIn | None = Body(default=None),
    force: bool = Query(False),
):
    if not force and (not state.FEEDBACK_READY or not state.LAST_SET_SUMMARY):
        return {"audio_url": None, "text": None, "seq": state.FEEDBACK_SEQ}

    state.FEEDBACK_READY = False
    seq = state.FEEDBACK_SEQ

    payload = body.dict() if body else _default_payload_from_state()
    if not payload:
        raise HTTPException(status_code=400, detail="No workout summary available")
    payload.setdefault("persona", getattr(state, "PERSONA", "default"))

    prompt = _build_prompt(payload)
    text = _call_openrouter(prompt, payload["persona"])

    audio_url = None
    try:
        audio_url = _piper_tts(text, payload["persona"])
    except Exception as e:
        print("[TTS] error:", e)

    state.LAST_FEEDBACK = {"text": text, "audio_url": audio_url,
                           "persona": payload["persona"], "seq": seq}
    return state.LAST_FEEDBACK

@router.get("/feedback/last")
def feedback_last():
    return getattr(state, "LAST_FEEDBACK", {"status": "no_feedback"})
