import numpy as np

def normalize_landmarks(landmarks: np.ndarray):
    left_hip = landmarks[23][:3]
    right_hip = landmarks[24][:3]
    hip_center = (left_hip + right_hip) / 2.0
    translated = landmarks[:, :3] - hip_center
    left_shoulder = landmarks[11][:3]
    right_shoulder = landmarks[12][:3]
    shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder)
    return translated / shoulder_dist if shoulder_dist > 1e-6 else translated

def angle_between(v1, v2, eps=1e-8):
    n1 = np.linalg.norm(v1) + eps
    n2 = np.linalg.norm(v2) + eps
    cos = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return np.degrees(np.arccos(cos))

def calculate_joint_angle(a, b, c):
    a, b, c = np.array(a[:3]), np.array(b[:3]), np.array(c[:3])
    return angle_between(a - b, c - b)

def ema_update(prev, new, alpha=0.2):
    return alpha * new + (1 - alpha) * prev if prev is not None else new