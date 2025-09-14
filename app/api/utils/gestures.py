from dataclasses import dataclass

@dataclass
class GestureSwitch:
    hand_raise_frames: int = 10
    plank_frames: int = 10
    cooldown_frames: int = 30

    def __post_init__(self):
        self._pushup_frames = 0
        self._squat_frames  = 0
        self._end_frames    = 0
        self._cooldown      = 0

    def reset(self):
        self._pushup_frames = 0
        self._squat_frames  = 0
        self._end_frames    = 0
        self._cooldown      = 0

    def detect(self, norm, current: str | None):
        if self._cooldown > 0:
            self._cooldown -= 1
            return None

        L_SH, R_SH = norm[11], norm[12]
        L_WR, R_WR = norm[15], norm[16]
        L_HIP, R_HIP = norm[23], norm[24]

        sh_y  = 0.5 * (L_SH[1] + R_SH[1])
        hip_y = 0.5 * (L_HIP[1] + R_HIP[1])

        is_upright = (hip_y > sh_y + 0.25)
        is_plank   = (abs(hip_y - sh_y) < 0.12)

        margin = 0.02
        left_above  = (L_WR[1] < L_SH[1] - margin)
        right_above = (R_WR[1] < R_SH[1] - margin)

        both_above = left_above and right_above
        one_above  = (left_above ^ right_above)

        if is_plank:
            self._pushup_frames += 1
        else:
            self._pushup_frames = 0

        if is_upright and one_above:
            self._squat_frames += 1
        else:
            self._squat_frames = 0

        if self._pushup_frames >= self.plank_frames and current != "pushup":
            self._cooldown = self.cooldown_frames
            return "pushup"

        if self._squat_frames >= self.hand_raise_frames and current != "squat":
            self._cooldown = self.cooldown_frames
            return "squat"

        return None

    def end_set_detect(self, norm, frames_required=12, debug=False):
        L_SH, R_SH = norm[11], norm[12]
        L_WR, R_WR = norm[15], norm[16]

        margin = 0.02

        left_above  = (L_WR[1] < L_SH[1] - margin)
        right_above = (R_WR[1] < R_SH[1] - margin)

        if left_above and right_above:
            self._end_frames += 1
        else:
            self._end_frames = max(0, self._end_frames - 1)

        if self._end_frames >= frames_required:
            self._end_frames = 0
            return True

        return False
