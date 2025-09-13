# exercise_modules/squat.py
import numpy as np
from collections import deque

def get_squat_config(angle_between, ema_update):
    thresholds = {
        "TORSO_LEAN_LIMIT_DEG": 45.0,
        "KNEE_CAVE_X_OFFSET": 0.12,
        "DEPTH_TOLERANCE": 0.02,
        "angle_between": angle_between,
        "ema_update": ema_update
    }
    deques = {
        "torso": deque(maxlen=8),
        "depth": deque(maxlen=8),
        "valgus_L": deque(maxlen=8),
        "valgus_R": deque(maxlen=8),
    }
    smoothed = {
        "torso_lean_deg": None,
        "depth_flag": None,
        "valgus_left": None,
        "valgus_right": None,
        "knee_flex_left": None,
        "knee_flex_right": None
    }
    return thresholds, deques, smoothed


def analyze_squat(norm, smoothed, deques, thresholds):
    mistakes = []

    L_SH, R_SH = norm[11], norm[12]
    L_HIP, R_HIP = norm[23], norm[24]
    L_KNEE, R_KNEE = norm[25], norm[26]
    L_ANK, R_ANK = norm[27], norm[28]

    hip_center = (L_HIP + R_HIP) / 2.0
    sh_center = (L_SH + R_SH) / 2.0
    knee_center = (L_KNEE + R_KNEE) / 2.0

    # --- Torso lean
    v_torso = sh_center[:2] - hip_center[:2]
    torso_lean_deg = thresholds["angle_between"](v_torso, np.array([0.0, -1.0]))
    deques["torso"].append(torso_lean_deg)
    smoothed["torso_lean_deg"] = thresholds["ema_update"](smoothed["torso_lean_deg"], torso_lean_deg)

    # --- Depth
    depth_ok = 1 if (hip_center[1] > (knee_center[1] - thresholds["DEPTH_TOLERANCE"])) else 0
    deques["depth"].append(depth_ok)
    smoothed["depth_flag"] = round(np.mean(deques["depth"]), 2) if deques["depth"] else None

    # --- Knee valgus
    dx_L = L_KNEE[0] - L_ANK[0]
    dx_R = R_KNEE[0] - R_ANK[0]
    valgus_left = 1 if abs(dx_L) > thresholds["KNEE_CAVE_X_OFFSET"] and dx_L < 0 else 0
    valgus_right = 1 if abs(dx_R) > thresholds["KNEE_CAVE_X_OFFSET"] and dx_R > 0 else 0
    deques["valgus_L"].append(valgus_left)
    deques["valgus_R"].append(valgus_right)
    smoothed["valgus_left"] = round(np.mean(deques["valgus_L"]), 2) if deques["valgus_L"] else None
    smoothed["valgus_right"] = round(np.mean(deques["valgus_R"]), 2) if deques["valgus_R"] else None

    # --- Rules
    if smoothed["depth_flag"] is not None and smoothed["depth_flag"] < 0.6:
        mistakes.append("Depth: Go lower (hips below knees).")
    if smoothed["torso_lean_deg"] is not None and smoothed["torso_lean_deg"] > thresholds["TORSO_LEAN_LIMIT_DEG"]:
        mistakes.append("Torso: Keep chest up.")
    if smoothed["valgus_left"] is not None and smoothed["valgus_left"] > 0.4:
        mistakes.append("Left knee: track over toes (avoid caving in).")
    if smoothed["valgus_right"] is not None and smoothed["valgus_right"] > 0.4:
        mistakes.append("Right knee: track over toes (avoid caving in).")

    return mistakes, smoothed
