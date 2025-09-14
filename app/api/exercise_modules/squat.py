# exercise_modules/squat.py
import numpy as np
from collections import deque

_REQUIRED_LEG_IDXS = [25, 26, 27, 28]

def get_squat_config(angle_between, ema_update):
    thresholds = {
        "TORSO_LEAN_LIMIT_DEG": 55.0,
        "KNEE_CAVE_X_OFFSET":  0.18,
        "DEPTH_TOLERANCE":     0.05,
        "VIS_THR":             0.35,
        "INFRAME_MARGIN":      0.04,
        "VALGUS_TRIGGER":      0.65,
        "DEPTH_RATIO_TRIGGER": 0.50,
        "angle_between": angle_between,
        "ema_update":    ema_update,
    }
    deques = {
        "torso":     deque(maxlen=5),
        "depth":     deque(maxlen=5),
        "valgus_L":  deque(maxlen=5),
        "valgus_R":  deque(maxlen=5),
    }
    smoothed = {
        "torso_lean_deg":  None,
        "depth_flag":      None,
        "valgus_left":     None,
        "valgus_right":    None,
        "knee_flex_left":  None,
        "knee_flex_right": None,
    }
    return thresholds, deques, smoothed


def _in_frame_xy(x, y, margin):
    return (-margin <= x <= 1.0 + margin) and (-margin <= y <= 1.0 + margin)


def _legs_visible(raw_landmarks, vis_thr, margin):

    ok = 0
    for i in _REQUIRED_LEG_IDXS:
        x, y, _, v = raw_landmarks[i]
        if (v >= vis_thr) and _in_frame_xy(float(x), float(y), margin):
            ok += 1
    return ok >= 2


def analyze_squat(norm, smoothed, deques, thresholds, raw_landmarks):

    mistakes = []

    if not _legs_visible(raw_landmarks, thresholds["VIS_THR"], thresholds["INFRAME_MARGIN"]):
        mistakes.append("Step back; show knees/ankles.")
        return mistakes, smoothed

    L_SH, R_SH = norm[11], norm[12]
    L_HIP, R_HIP = norm[23], norm[24]
    L_KNEE, R_KNEE = norm[25], norm[26]
    L_ANK, R_ANK = norm[27], norm[28]

    hip_center  = (L_HIP + R_HIP) / 2.0
    sh_center   = (L_SH + R_SH) / 2.0
    knee_center = (L_KNEE + R_KNEE) / 2.0

    v_torso = sh_center[:2] - hip_center[:2]
    torso_lean_deg = thresholds["angle_between"](v_torso, np.array([0.0, -1.0]))
    deques["torso"].append(torso_lean_deg)
    smoothed["torso_lean_deg"] = thresholds["ema_update"](smoothed["torso_lean_deg"], torso_lean_deg)

    depth_ok = 1 if (hip_center[1] > (knee_center[1] - thresholds["DEPTH_TOLERANCE"])) else 0
    deques["depth"].append(depth_ok)
    smoothed["depth_flag"] = round(np.mean(deques["depth"]), 2) if deques["depth"] else None

    dx_L = L_KNEE[0] - L_ANK[0]
    dx_R = R_KNEE[0] - R_ANK[0]
    valgus_left  = 1 if abs(dx_L) > thresholds["KNEE_CAVE_X_OFFSET"] and dx_L < 0 else 0
    valgus_right = 1 if abs(dx_R) > thresholds["KNEE_CAVE_X_OFFSET"] and dx_R > 0 else 0
    deques["valgus_L"].append(valgus_left)
    deques["valgus_R"].append(valgus_right)
    smoothed["valgus_left"]  = round(np.mean(deques["valgus_L"]), 2) if deques["valgus_L"] else None
    smoothed["valgus_right"] = round(np.mean(deques["valgus_R"]), 2) if deques["valgus_R"] else None

    if smoothed["depth_flag"] is not None and smoothed["depth_flag"] < thresholds["DEPTH_RATIO_TRIGGER"]:
        mistakes.append("Go deeper.")
    if smoothed["torso_lean_deg"] is not None and smoothed["torso_lean_deg"] > thresholds["TORSO_LEAN_LIMIT_DEG"]:
        mistakes.append("Chest up.")
    if smoothed["valgus_left"] is not None and smoothed["valgus_left"] > thresholds["VALGUS_TRIGGER"]:
        mistakes.append("Push left knee out.")
    if smoothed["valgus_right"] is not None and smoothed["valgus_right"] > thresholds["VALGUS_TRIGGER"]:
        mistakes.append("Push right knee out.")

    return mistakes[:2], smoothed
