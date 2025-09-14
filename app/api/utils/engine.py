import time
import cv2
import numpy as np
import mediapipe as mp

from app.api.utils import state
from app.api.utils.rep_counter import RepCounter
from app.api.utils.gestures import GestureSwitch
from app.api.exercise_modules.squat import get_squat_config, analyze_squat
from app.api.exercise_modules.pushup import get_pushup_config, analyze_pushup
from app.api.exercise_modules.rest import get_rest_config, analyze_rest
from app.api.utils.landmarks import (
    normalize_landmarks,
    angle_between,
    ema_update,
    is_setup_issue,
    skeleton_specs,
    GREEN, ORANGE, RED,
)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

CONFIG = {"exercise": "squat"}
thresholds, deques, smoothed = get_squat_config(angle_between, ema_update)

rep_counter = RepCounter(good_min_frames=5, bad_min_frames=2)
gesture_switch = GestureSwitch(hand_raise_frames=10, plank_frames=10, cooldown_frames=30)

LAST_REP_FROZEN = 0
REP_FREEZE_UNTIL = 0.0
REST_MIN_SECONDS = 0.0


def _mmss(seconds: float) -> str:
    s = max(0, int(seconds))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"


def _set_active_exercise(ex_name: str):
    global thresholds, deques, smoothed, rep_counter
    CONFIG["exercise"] = ex_name
    rep_counter.reset()
    gesture_switch.reset()
    state.LAST_REP_SEEN = 0
    state.LAST_REP_SPOKEN = 0
    state.PENDING_REP = None
    state.LAST_REP_ANNOUNCED_AT = 0.0
    if ex_name == "squat":
        thresholds, deques, smoothed = get_squat_config(angle_between, ema_update)
    elif ex_name == "pushup":
        thresholds, deques, smoothed = get_pushup_config(angle_between, ema_update)
    elif ex_name == "rest":
        thresholds, deques, smoothed = get_rest_config(angle_between, ema_update)
    else:
        thresholds, deques, smoothed = get_squat_config(angle_between, ema_update)
        CONFIG["exercise"] = "squat"


def set_config_handler(exercise: str):
    if exercise not in {"squat", "pushup", "rest"}:
        return {"status": "error", "msg": f"Unknown exercise '{exercise}'"}
    _set_active_exercise(exercise)
    if exercise == "rest":
        state.REST_START_TIME = time.monotonic()
    return {"status": "ok", "exercise": CONFIG["exercise"]}



def generate_frames():
    global smoothed, LAST_REP_FROZEN, REP_FREEZE_UNTIL
    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            image = frame.copy()
            mistakes = []
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                data = np.array([[p.x, p.y, p.z, p.visibility] for p in lm], dtype=np.float32)
                norm = normalize_landmarks(data)
                suggestion = gesture_switch.detect(norm, CONFIG["exercise"])
                end_set = False if CONFIG["exercise"] == "rest" else \
                          gesture_switch.end_set_detect(norm, frames_required=12, debug=True)
                if CONFIG["exercise"] == "rest":
                    state.CURRENT_CUES = []
                    if state.REST_START_TIME == 0.0:
                        state.REST_START_TIME = time.monotonic()
                    rest_elapsed = time.monotonic() - state.REST_START_TIME
                    rest_str = _mmss(rest_elapsed)
                    cv2.putText(image, f"REST {rest_str}", (12, 26),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (220, 220, 220), 2)
                    cv2.putText(image, "Raise ONE hand to start SQUAT | Hold PLANK to start PUSH-UP",
                                (12, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)
                    if REST_MIN_SECONDS > 0 and (time.monotonic() - state.REST_START_TIME) < REST_MIN_SECONDS:
                        pass
                    else:
                        if suggestion in ("squat", "pushup"):
                            rest_duration = time.monotonic() - state.REST_START_TIME
                            state.LAST_REST_SUMMARY = {
                            "exercise" : "rest",
                                "started_at": state.REST_START_TIME,
                                "duration": rest_duration,
                                "ended_at": time.monotonic(),
                            }
                            state.WORKOUTS_BUFFER.append(state.LAST_REST_SUMMARY)
                            _set_active_exercise(suggestion)
                            state.SET_ACTIVE = True
                            state.SET_START_TIME = time.monotonic()
                            state.SET_MISTAKES = []
                            state.REST_START_TIME = 0.0
                            print("DEBUG: Exiting REST → start", suggestion)
                    now = time.monotonic()
                    display_reps = LAST_REP_FROZEN if now < REP_FREEZE_UNTIL else 0
                else:
                    if CONFIG["exercise"] == "squat":
                        mistakes, updated_smoothed = analyze_squat(
                            norm, smoothed, deques, thresholds, data
                        )
                    elif CONFIG["exercise"] == "pushup":
                        mistakes, updated_smoothed = analyze_pushup(
                            norm, smoothed, deques, thresholds
                        )
                    else:
                        mistakes, updated_smoothed = analyze_rest(norm, smoothed, deques, thresholds)
                    smoothed.update(updated_smoothed)
                    state.CURRENT_CUES = mistakes
                    good_form_now = (len(mistakes) == 0)
                    reps = rep_counter.update(good_form_now)
                    if reps > state.LAST_REP_SEEN:
                        state.LAST_REP_SEEN = reps
                        if not state.SET_ACTIVE:
                            state.SET_ACTIVE = True
                            state.SET_START_TIME = time.monotonic()
                            state.SET_MISTAKES = []
                            print("DEBUG: Set auto-started because reps increased")
                    if state.SET_ACTIVE and mistakes:
                        state.SET_MISTAKES.extend(mistakes)
                    if state.SET_ACTIVE and end_set:
                        state.LAST_REP_SEEN = max(state.LAST_REP_SEEN, reps)
                        state.SET_END_TIME = time.monotonic()
                        duration = state.SET_END_TIME - state.SET_START_TIME
                        summary = {
                            "exercise": CONFIG["exercise"],
                            "reps": state.LAST_REP_SEEN,
                            "duration": duration,
                            "mistakes": state.SET_MISTAKES.copy(),
                            "persona": getattr(state, "PERSONA", "default"),
                            "ended_at": time.time(),
                        }
                        state.WORKOUTS_BUFFER.append({
                            "exercise": summary["exercise"],
                            "duration": summary["duration"],
                            "reps": summary["reps"]
                        })
                        state.FEEDBACK_SEQ += 1
                        state.FEEDBACK_READY = True
                        state.LAST_SET_SUMMARY = summary
                        state.FEEDBACK_SEQ += 1
                        state.FEEDBACK_READY = True
                        print("SET_LOG:", summary)
                        LAST_REP_FROZEN = state.LAST_REP_SEEN
                        REP_FREEZE_UNTIL = time.monotonic() + 2.5
                        _set_active_exercise("rest")
                        state.SET_ACTIVE = False
                        state.REST_START_TIME = time.monotonic()
                        state.SET_MISTAKES.clear()
                        _set_active_exercise("rest")
                        state.SET_ACTIVE = False
                        state.REST_START_TIME = time.monotonic()
                    color = GREEN if good_form_now else (RED if is_setup_issue(mistakes) else ORANGE)
                    lm_spec, conn_spec = skeleton_specs(color)
                    mp_drawing.draw_landmarks(
                        image,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=lm_spec,
                        connection_drawing_spec=conn_spec,
                    )
                    now = time.monotonic()
                    if now < REP_FREEZE_UNTIL:
                        display_reps = LAST_REP_FROZEN
                    else:
                        display_reps = max(reps, state.LAST_REP_SEEN) if state.SET_ACTIVE else 0
                    header = f"{CONFIG['exercise'].upper()} | Reps: {display_reps}"
                    cv2.putText(image, header, (12, 26),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                    if state.SET_ACTIVE:
                        cv2.putText(image, "SET ACTIVE", (12, 48),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2)
                    y0, dy = 70, 28
                    if good_form_now:
                        cv2.putText(image, "Good form!", (12, y0),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, GREEN, 2)
                    else:
                        for i, text in enumerate(mistakes[:3]):
                            cv2.putText(image, text, (12, y0 + i * dy),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, RED, 2)
            else:
                state.CURRENT_CUES = []
            ok, buffer = cv2.imencode(".jpg", image)
            if not ok:
                continue
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")