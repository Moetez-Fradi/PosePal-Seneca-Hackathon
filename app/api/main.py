import cv2
import mediapipe as mp
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from utils.landmarks import normalize_landmarks, angle_between, ema_update
from exercise_modules.squat import get_squat_config, analyze_squat
from exercise_modules.pushup import get_pushup_config, analyze_pushup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
landmarks_history = []

# Default exercise config (squat)
CONFIG = {"exercise": "squat"}
thresholds, deques, smoothed = get_squat_config(angle_between, ema_update)


@app.get("/set_config")
def set_config(exercise: str = Query(...)):
    """
    Switch between available exercises (squat, pushup).
    Example: /set_config?exercise=pushup
    """
    global thresholds, deques, smoothed
    CONFIG["exercise"] = exercise

    if exercise == "squat":
        thresholds, deques, smoothed = get_squat_config(angle_between, ema_update)
    elif exercise == "pushup":
        thresholds, deques, smoothed = get_pushup_config(angle_between, ema_update)
    else:
        return {"status": "error", "msg": f"Unknown exercise '{exercise}'"}

    return {"status": "ok", "exercise": exercise}


def generate_frames():
    """
    Video generator: grabs frames from webcam, processes with mediapipe,
    runs the selected exercise analyzer, and streams annotated frames.
    """
    global smoothed

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
                mp_drawing.draw_landmarks(image, results.pose_landmarks,
                                          mp_pose.POSE_CONNECTIONS)

                lm = results.pose_landmarks.landmark
                data = np.array([[p.x, p.y, p.z, p.visibility] for p in lm],
                                dtype=np.float32)
                landmarks_history.append(data.tolist())
                norm = normalize_landmarks(data)

                # 🔹 Route to correct analyzer
                if CONFIG["exercise"] == "squat":
                    mistakes, updated_smoothed = analyze_squat(norm, smoothed, deques, thresholds)
                elif CONFIG["exercise"] == "pushup":
                    mistakes, updated_smoothed = analyze_pushup(norm, smoothed, deques, thresholds)
                else:
                    mistakes = [f"Unknown exercise: {CONFIG['exercise']}"]
                    updated_smoothed = smoothed

                smoothed.update(updated_smoothed)

                # HUD overlay
                y0, dy = 30, 28
                if mistakes:
                    for i, text in enumerate(mistakes):
                        cv2.putText(image, text, (12, y0 + i * dy),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    cv2.putText(image, "Form looks good!", (12, y0),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)

            # Encode as JPEG for streaming
            ret, buffer = cv2.imencode('.jpg', image)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.get("/video")
def video_feed():
    """
    Browser will display live video here:
    <img src="http://localhost:8000/video" />
    """
    return StreamingResponse(generate_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")
