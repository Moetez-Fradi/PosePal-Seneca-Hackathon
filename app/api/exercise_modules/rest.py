from typing import Tuple, Dict, Any

def get_rest_config(angle_between, ema_update) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:

    thresholds = {}
    deques = {}
    smoothed = {}
    return thresholds, deques, smoothed

def analyze_rest(norm, smoothed, deques, thresholds, *args, **kwargs):

    mistakes = []
    updated_smoothed = smoothed
    return mistakes, updated_smoothed
