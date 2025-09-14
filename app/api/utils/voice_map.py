CUE_TEXT_TO_KEY = [
    ("get on the floor.",     "GET_ON_FLOOR"),
    ("hold a straight plank.", "HOLD_PLANK"),
    ("bring hands closer.",   "HANDS_CLOSER"),
    ("move hands wider.",     "HANDS_WIDER"),
    ("hands under shoulders.", "HANDS_UNDER_SHOULDERS"),
    ("lift hips.",            "LIFT_HIPS"),
    ("lower hips.",           "LOWER_HIPS"),
    ("go lower.",             "GO_LOWER"),

    ("step back; show knees/ankles.", "STEP_BACK"),
    ("go deeper.",          "SQUAT_GO_DEEPER"),
    ("chest up.",           "SQUAT_CHEST_UP"),
    ("push left knee out.", "SQUAT_KNEE_OUT_LEFT"),
    ("push right knee out.","SQUAT_KNEE_OUT_RIGHT"),
]


def cue_key_from_text(msg: str) -> str | None:
    """
    Match exactly what the analyzers return (case + punctuation insensitive).
    """
    low = msg.strip().lower()
    for needle, key in CUE_TEXT_TO_KEY:
        if low == needle:
            return key
    return None
