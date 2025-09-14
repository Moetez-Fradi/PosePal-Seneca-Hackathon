from typing import Tuple, Dict, Any

def get_rest_config(angle_between, ema_update) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Returns dummy thresholds/deques/smoothed so the caller can keep the same code path.
    Rest has no analysis and no reps.
    """
    thresholds = {}
    deques = {}
    smoothed = {}
    return thresholds, deques, smoothed

def analyze_rest(norm, smoothed, deques, thresholds, *args, **kwargs):
    """
    Rest never produces mistakes and never changes smoothing state.
    Keep signature-compatible with squat/pushup analyzers.
    """
    mistakes = []
    updated_smoothed = smoothed
    return mistakes, updated_smoothed
