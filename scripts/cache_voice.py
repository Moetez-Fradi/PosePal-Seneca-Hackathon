# scripts/cache_tts.py
from pathlib import Path
import subprocess
import json
import sys

VOICE_DIR = Path("/home/Golden5ragon/piper-voices")
VOICES = {
    "default": VOICE_DIR / "en_US-libritts-high.onnx",
    "goggins": VOICE_DIR / "en_US-joe-medium.onnx",
    "barbie":  VOICE_DIR / "en_US-amy-medium.onnx",
}

OUT_ROOT = Path("app/static/tts")
OUT_ROOT.mkdir(parents=True, exist_ok=True)

BASE_CUES = {
    "GET_ON_FLOOR": "Get on the floor.",
    "HOLD_PLANK": "Hold a straight plank.",
    "HANDS_CLOSER": "Bring hands closer.",
    "HANDS_WIDER": "Move hands wider.",
    "HANDS_UNDER_SHOULDERS": "Hands under shoulders.",
    "LIFT_HIPS": "Lift hips.",
    "LOWER_HIPS": "Lower hips.",
    "GO_LOWER": "Go lower.",
    "STEP_BACK": "Step back; show knees and ankles.",
    "SQUAT_GO_DEEPER": "Go deeper.",
    "SQUAT_CHEST_UP": "Chest up.",
    "SQUAT_KNEE_OUT_LEFT": "Push left knee out.",
    "SQUAT_KNEE_OUT_RIGHT": "Push right knee out.",
}

PERSONA_CUES = {
    "goggins": {
        "GET_ON_FLOOR": "Get on the floor. No excuses.",
        "HOLD_PLANK": "Lock it in. Straight line.",
        "HANDS_CLOSER": "Hands closer. Now.",
        "HANDS_WIDER": "Hands wider. Own it.",
        "HANDS_UNDER_SHOULDERS": "Hands under shoulders. Tight.",
        "LIFT_HIPS": "Lift your hips. Stop sagging.",
        "LOWER_HIPS": "Lower your hips. No piking.",
        "GO_LOWER": "Lower. Hit depth.",
        "STEP_BACK": "Step back. Show the legs.",
        "SQUAT_GO_DEEPER": "Deeper. Full rep.",
        "SQUAT_CHEST_UP": "Chest up. Control it.",
        "SQUAT_KNEE_OUT_LEFT": "Left knee out. Now.",
        "SQUAT_KNEE_OUT_RIGHT": "Right knee out. Now.",
    },
    "barbie": {
        "GET_ON_FLOOR": "Floor time, queen.",
        "HOLD_PLANK": "Hold that plank, queen.",
        "HANDS_CLOSER": "Hands closer, queen.",
        "HANDS_WIDER": "Hands wider, queen.",
        "HANDS_UNDER_SHOULDERS": "Hands under shoulders, queen.",
        "LIFT_HIPS": "Lift hips, queen.",
        "LOWER_HIPS": "Lower hips, queen.",
        "GO_LOWER": "Lower, queen.",
        "STEP_BACK": "Step back, queen. Show knees and ankles.",
        "SQUAT_GO_DEEPER": "Deeper, queen.",
        "SQUAT_CHEST_UP": "Chest up, queen.",
        "SQUAT_KNEE_OUT_LEFT": "Left knee out, queen.",
        "SQUAT_KNEE_OUT_RIGHT": "Right knee out, queen.",
    },
    "default": {},
}

NUM_MAX = 20

def rep_line_for(persona: str, n: int) -> str:
    if persona == "default":
        return str(n)
    if persona == "barbie":
        return "Six — come on, queen, keep going!" if n == 6 else str(n)
    if persona == "goggins":
        if n == 10:
            return "Ten — a machine here!"
        if n in (13, 14, 15):
            return {
                13: "Thirteen — come on!",
                14: "Fourteen — come on!",
                15: "Fifteen — come on!",
            }[n]
        if n in (17, 18, 19, 20):
            return {
                17: "Get it! Seventeen.",
                18: "Get it! Eighteen.",
                19: "Get it! Nineteen.",
                20: "Get it! Twenty.",
            }[n]
        return str(n)
    return str(n)

def persona_text(persona: str, key: str) -> str:
    overrides = PERSONA_CUES.get(persona, {})
    return overrides.get(key, BASE_CUES[key])

def synth_with_piper(model_path: Path, text: str, out_wav: Path):
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["piper-tts", "--model", str(model_path), "--output_file", str(out_wav)],
        input=text.encode("utf-8"),
        check=True
    )

def generate_cues_for_persona(persona: str, model_path: Path) -> dict:
    out_dir = OUT_ROOT / persona
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for key in BASE_CUES.keys():
        text = persona_text(persona, key)
        out_file = out_dir / (key.lower() + ".wav")
        synth_with_piper(model_path, text, out_file)
        manifest[key] = f"/static/tts/{persona}/{out_file.name}"
    return manifest

def generate_counts_for_persona(persona: str, model_path: Path) -> dict:
    out_dir = OUT_ROOT / persona
    out_dir.mkdir(parents=True, exist_ok=True)
    rep_map = {}
    for n in range(1, NUM_MAX + 1):
        text = rep_line_for(persona, n)
        out_file = out_dir / f"rep_{n}.wav"
        synth_with_piper(model_path, text, out_file)
        rep_map[f"REP_{n}"] = f"/static/tts/{persona}/{out_file.name}"
    return rep_map

def main():
    for persona, model in VOICES.items():
        if not model.exists():
            print(f"missing model for '{persona}': {model}", file=sys.stderr)
            sys.exit(1)
    for persona, model in VOICES.items():
        cue_manifest = generate_cues_for_persona(persona, model)
        rep_manifest = generate_counts_for_persona(persona, model)
        out_dir = OUT_ROOT / persona
        (out_dir / "tts_manifest.json").write_text(json.dumps(cue_manifest, indent=2))
        (out_dir / "rep_manifest.json").write_text(json.dumps(rep_manifest, indent=2))
    print("\nDone")

if __name__ == "__main__":
    main()
