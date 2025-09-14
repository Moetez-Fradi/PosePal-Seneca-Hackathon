import numpy as np
from collections import deque

def get_pushup_config(angle_between, ema_update):
    thresholds = {
        "UPRIGHT_DELTA_Y_MIN": 0.75,
        "PLANK_TORSO_Y_MAX":  0.32,
        "HANDS_SHOULDER_RATIO_MIN": 0.55,
        "HANDS_SHOULDER_RATIO_MAX": 1.55,
        "HANDS_X_OFFSET_MAX":       0.65,
        "HIP_LINE_MAX_DEV": 0.22,
        "ELBOW_ABS_REQUIRED": 110.0,
        "ELBOW_REL_DROP_DEG":  45.0,
        "BOTTOM_OK_RATIO":       0.30,
        "angle_between": angle_between,
        "ema_update":    ema_update,
    }

    deques = {
        "upright":      deque(maxlen=4),
        "plank":        deque(maxlen=4),
        "hand_ratio":   deque(maxlen=4),
        "hand_xoffset": deque(maxlen=4),
        "hip_dev_abs":  deque(maxlen=4),
        "hip_dev_sign": deque(maxlen=4),
        "elbow_mean_hist": deque(maxlen=12),
        "bottom_ok":       deque(maxlen=8),
    }

    smoothed = {
        "upright_score": None,
        "plank_score":   None,
        "hands_ratio":   None,
        "hands_xoffset": None,
        "hip_dev":       None,
        "hip_dev_dir":   None,
        "elbow_mean":    None,
        "top_max":       None,
    }
    return thresholds, deques, smoothed


def _signed_y_distance_to_line(pt, a, b):
    pa = pt[:2] - a[:2]
    v  = b[:2]  - a[:2]
    vv = np.dot(v, v) + 1e-9
    t  = np.dot(pa, v) / vv
    proj = a[:2] + t * v
    signed_y = pt[1] - proj[1]
    dist = np.linalg.norm(pt[:2] - proj)
    return signed_y, dist


def analyze_pushup(norm, smoothed, deques, thresholds):
    ab  = thresholds["angle_between"]
    ema = thresholds["ema_update"]
    mistakes = []

    L_SH, R_SH = norm[11], norm[12]
    L_ELB, R_ELB = norm[13], norm[14]
    L_WR,  R_WR  = norm[15], norm[16]
    L_HIP, R_HIP = norm[23], norm[24]
    L_ANK, R_ANK = norm[27], norm[28]

    sh_center  = (L_SH + R_SH) / 2.0
    hip_center = (L_HIP + R_HIP) / 2.0
    ank_center = (L_ANK + R_ANK) / 2.0

    shoulder_span = np.linalg.norm((R_SH - L_SH)[:2]) + 1e-9
    wrist_span    = abs(R_WR[0] - L_WR[0])

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
        mistakes.append("Get on the floor.")
        return mistakes[:2], smoothed
    if not in_plank:
        mistakes.append("Hold a straight plank.")

    hands_ratio  = wrist_span / shoulder_span
    x_offset_avg = 0.5 * (abs(L_WR[0] - L_SH[0]) + abs(R_WR[0] - R_SH[0]))
    deques["hand_ratio"].append(hands_ratio)
    deques["hand_xoffset"].append(x_offset_avg)

    smoothed["hands_ratio"]   = round(np.mean(deques["hand_ratio"]), 2) if deques["hand_ratio"] else hands_ratio
    smoothed["hands_xoffset"] = ema(smoothed["hands_xoffset"], x_offset_avg)

    if smoothed["hands_ratio"] is not None:
        if smoothed["hands_ratio"] > thresholds["HANDS_SHOULDER_RATIO_MAX"]:
            mistakes.append("Bring hands closer.")
        elif smoothed["hands_ratio"] < thresholds["HANDS_SHOULDER_RATIO_MIN"]:
            mistakes.append("Move hands wider.")
    if smoothed["hands_xoffset"] is not None and smoothed["hands_xoffset"] > thresholds["HANDS_X_OFFSET_MAX"]:
        if len(mistakes) < 2:
            mistakes.append("Hands under shoulders.")
    if len(mistakes) >= 2:
        return mistakes[:2], smoothed

    signed_y, dev_abs = _signed_y_distance_to_line(hip_center, sh_center, ank_center)
    deques["hip_dev_abs"].append(dev_abs)
    deques["hip_dev_sign"].append(signed_y)

    hip_dev_abs  = np.mean(deques["hip_dev_abs"])  if deques["hip_dev_abs"]  else dev_abs
    hip_dev_sign = np.mean(deques["hip_dev_sign"]) if deques["hip_dev_sign"] else signed_y

    smoothed["hip_dev"]     = ema(smoothed["hip_dev"], hip_dev_abs)
    smoothed["hip_dev_dir"] = ema(smoothed["hip_dev_dir"], hip_dev_sign)

    if smoothed["hip_dev"] is not None and smoothed["hip_dev"] > thresholds["HIP_LINE_MAX_DEV"]:
        if smoothed["hip_dev_dir"] is not None and smoothed["hip_dev_dir"] > 0:
            mistakes.append("Lift hips.")
        else:
            mistakes.append("Lower hips.")
    if len(mistakes) >= 2:
        return mistakes[:2], smoothed

    v1L = (L_SH - L_ELB)[:2]; v2L = (L_WR - L_ELB)[:2]
    v1R = (R_SH - R_ELB)[:2]; v2R = (R_WR - R_ELB)[:2]
    angle_left_2d  = ab(v1L, v2L)
    angle_right_2d = ab(v1R, v2R)
    elbow_mean_now = 0.5 * (angle_left_2d + angle_right_2d)

    smoothed["elbow_mean"] = ema(smoothed["elbow_mean"], elbow_mean_now)
    deques["elbow_mean_hist"].append(elbow_mean_now)

    if len(deques["elbow_mean_hist"]):
        top_max = max(deques["elbow_mean_hist"])
        smoothed["top_max"] = top_max if smoothed.get("top_max") is None else max(smoothed["top_max"], top_max)
    else:
        top_max = smoothed.get("top_max", elbow_mean_now)

    abs_pass = (smoothed["elbow_mean"] is not None and
                smoothed["elbow_mean"] <= thresholds["ELBOW_ABS_REQUIRED"])
    rel_pass = False
    if smoothed.get("top_max") is not None:
        rel_pass = (smoothed["elbow_mean"] <= (smoothed["top_max"] - thresholds["ELBOW_REL_DROP_DEG"]))

    bottom_ok_now = 1 if (abs_pass or rel_pass) else 0
    deques["bottom_ok"].append(bottom_ok_now)
    bottom_ok_ratio = np.mean(deques["bottom_ok"]) if deques["bottom_ok"] else 0.0

    if bottom_ok_ratio < thresholds["BOTTOM_OK_RATIO"]:
        mistakes.insert(0, "Go lower.")

    return mistakes[:2], smoothed
