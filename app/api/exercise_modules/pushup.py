# exercise_modules/pushup.py
import numpy as np
from collections import deque

def get_pushup_config(angle_between, ema_update):
    """
    Looser, simpler push-up config.
    Uses shoulder-width–normalized coords from normalize_landmarks().
    """
    thresholds = {
        # Posture classification (looser)
        "UPRIGHT_DELTA_Y_MIN": 0.70,   # > => you're upright/standing
        "PLANK_TORSO_Y_MAX":  0.25,    # < => you're roughly horizontal (plank)

        # Hand placement (wider acceptable range)
        "HANDS_SHOULDER_RATIO_MIN": 0.70,
        "HANDS_SHOULDER_RATIO_MAX": 1.30,
        "HANDS_X_OFFSET_MAX":       0.45,  # avg(|wrist_x - shoulder_x|)

        # Hip alignment relative to shoulder->ankle line (more tolerant)
        "HIP_LINE_MAX_DEV": 0.18,

        # Elbow ROM (more lenient)
        "ELBOW_LOCK_TOP":      160.0,  # good top if >= this
        "ELBOW_BOTTOM_TARGET": 100.0,  # bottom OK if <= this

        # Utilities
        "angle_between": angle_between,
        "ema_update": ema_update,
    }

    # Shorter windows to react faster (but still smooth)
    deques = {
        "upright": deque(maxlen=5),
        "plank":  deque(maxlen=5),

        "hand_ratio": deque(maxlen=5),
        "hand_xoffset": deque(maxlen=5),

        "hip_dev_abs": deque(maxlen=5),
        "hip_dev_sign": deque(maxlen=5),

        "elbow_L": deque(maxlen=5),
        "elbow_R": deque(maxlen=5),
    }

    smoothed = {
        "upright_score": None,
        "plank_score": None,
        "hands_ratio": None,
        "hands_xoffset": None,
        "hip_dev": None,
        "hip_dev_dir": None,
        "elbow_flex_left": None,
        "elbow_flex_right": None,
        "elbow_mean": None,
    }
    return thresholds, deques, smoothed


def _signed_y_distance_to_line(pt, a, b):
    """
    Signed vertical residual (y grows downward). Positive => pt is below the line (sag),
    negative => pt is above (pike). Also returns Euclidean distance to the line.
    """
    pa = pt[:2] - a[:2]
    v  = b[:2]  - a[:2]
    vv = np.dot(v, v) + 1e-9
    t  = np.dot(pa, v) / vv
    proj = a[:2] + t * v
    signed_y = pt[1] - proj[1]
    dist = np.linalg.norm(pt[:2] - proj)
    return signed_y, dist


def analyze_pushup(norm, smoothed, deques, thresholds):
    """
    Easier push-up analyzer:
      - Gentle posture setup cue if upright/not in plank
      - Simple hand-width/placement cue
      - Simple hip sag/pike cue
      - Simple elbow ROM cue
    Emits at most TWO cues per frame (top-priority first).
    """
    ab  = thresholds["angle_between"]
    ema = thresholds["ema_update"]
    mistakes = []

    # Landmarks
    L_SH, R_SH = norm[11], norm[12]
    L_ELB, R_ELB = norm[13], norm[14]
    L_WR,  R_WR  = norm[15], norm[16]
    L_HIP, R_HIP = norm[23], norm[24]
    L_ANK, R_ANK = norm[27], norm[28]

    sh_center  = (L_SH + R_SH) / 2.0
    hip_center = (L_HIP + R_HIP) / 2.0
    ank_center = (L_ANK + R_ANK) / 2.0

    # Spans
    shoulder_span = np.linalg.norm((R_SH - L_SH)[:2]) + 1e-9
    wrist_span    = abs(R_WR[0] - L_WR[0])

    # ---- 1) Posture: upright vs plank (priority #1)
    delta_y = abs(sh_center[1] - hip_center[1])
    deques["upright"].append(delta_y)
    deques["plank"].append(delta_y)

    upright_score = np.mean(deques["upright"]) if deques["upright"] else delta_y
    plank_score   = np.mean(deques["plank"])   if deques["plank"]   else delta_y

    smoothed["upright_score"] = ema(smoothed["upright_score"], upright_score)
    smoothed["plank_score"]   = ema(smoothed["plank_score"],   plank_score)

    clearly_upright = (smoothed["upright_score"] is not None and
                       smoothed["upright_score"] > thresholds["UPRIGHT_DELTA_Y_MIN"])
    in_plank = (smoothed["plank_score"] is not None and
                smoothed["plank_score"] < thresholds["PLANK_TORSO_Y_MAX"])

    if clearly_upright:
        mistakes.append("Get into push-up position on the floor: hands under shoulders, body straight.")
        # If upright, stop early—no need to add many cues in the same frame.
        return mistakes[:2], smoothed
    if not in_plank:
        mistakes.append("Make a straight line from shoulders to ankles (plank).")

    # ---- 2) Hands: width & under-shoulder (priority #2)
    hands_ratio  = wrist_span / shoulder_span
    x_offset_avg = 0.5 * (abs(L_WR[0] - L_SH[0]) + abs(R_WR[0] - R_SH[0]))

    deques["hand_ratio"].append(hands_ratio)
    deques["hand_xoffset"].append(x_offset_avg)

    smoothed["hands_ratio"]  = round(np.mean(deques["hand_ratio"]), 2) if deques["hand_ratio"] else hands_ratio
    smoothed["hands_xoffset"] = ema(smoothed["hands_xoffset"], x_offset_avg)

    if smoothed["hands_ratio"] is not None:
        if smoothed["hands_ratio"] > thresholds["HANDS_SHOULDER_RATIO_MAX"]:
            mistakes.append("Hands a bit wide — bring them slightly closer.")
        elif smoothed["hands_ratio"] < thresholds["HANDS_SHOULDER_RATIO_MIN"]:
            mistakes.append("Hands a bit narrow — move them slightly wider.")
    if smoothed["hands_xoffset"] is not None and smoothed["hands_xoffset"] > thresholds["HANDS_X_OFFSET_MAX"]:
        mistakes.append("Place hands more under your shoulders.")

    if len(mistakes) >= 2:
        return mistakes[:2], smoothed

    # ---- 3) Hips: sag vs pike (priority #3)
    signed_y, dev_abs = _signed_y_distance_to_line(hip_center, sh_center, ank_center)
    deques["hip_dev_abs"].append(dev_abs)
    deques["hip_dev_sign"].append(signed_y)

    hip_dev_abs  = np.mean(deques["hip_dev_abs"])  if deques["hip_dev_abs"]  else dev_abs
    hip_dev_sign = np.mean(deques["hip_dev_sign"]) if deques["hip_dev_sign"] else signed_y

    smoothed["hip_dev"]     = ema(smoothed["hip_dev"], hip_dev_abs)
    smoothed["hip_dev_dir"] = ema(smoothed["hip_dev_dir"], hip_dev_sign)

    if smoothed["hip_dev"] is not None and smoothed["hip_dev"] > thresholds["HIP_LINE_MAX_DEV"]:
        if smoothed["hip_dev_dir"] is not None and smoothed["hip_dev_dir"] > 0:
            mistakes.append("Lift hips slightly — avoid letting them sag.")
        else:
            mistakes.append("Lower hips slightly — avoid piking up.")
    if len(mistakes) >= 2:
        return mistakes[:2], smoothed

    # ---- 4) Elbow ROM (priority #4; keep cues gentle)
    # Left
    v1 = L_SH[:3] - L_ELB[:3]
    v2 = L_WR[:3] - L_ELB[:3]
    angle_left = ab(v1, v2)
    deques["elbow_L"].append(angle_left)
    smoothed["elbow_flex_left"] = ema(smoothed["elbow_flex_left"], angle_left)

    # Right
    v1 = R_SH[:3] - R_ELB[:3]
    v2 = R_WR[:3] - R_ELB[:3]
    angle_right = ab(v1, v2)
    deques["elbow_R"].append(angle_right)
    smoothed["elbow_flex_right"] = ema(smoothed["elbow_flex_right"], angle_right)

    # Mean
    elbow_mean_now = 0.5 * (angle_left + angle_right)
    smoothed["elbow_mean"] = ema(smoothed["elbow_mean"], elbow_mean_now)

    if in_plank and smoothed["elbow_mean"] is not None:
        if smoothed["elbow_mean"] > thresholds["ELBOW_LOCK_TOP"]:
            mistakes.append("Start lowering — bend the elbows.")
        elif smoothed["elbow_mean"] > thresholds["ELBOW_BOTTOM_TARGET"]:
            mistakes.append("Go a bit lower — aim closer to 90°.")
        # No “too deep” cue in easy mode; it’s forgiving.

    # Cap to max 2 cues per frame
    return mistakes[:2], smoothed
