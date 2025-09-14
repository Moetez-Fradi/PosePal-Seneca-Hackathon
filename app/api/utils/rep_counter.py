from collections import deque

class RepCounter:
    """
    Increments when we transition from GOOD (no mistakes) to BAD (mistakes appear).
    Has small hysteresis so a single noisy bad frame doesn't count.
    """
    def __init__(self, good_min_frames: int = 5, bad_min_frames: int = 2):
        self.good_min_frames = good_min_frames
        self.bad_min_frames = bad_min_frames
        self._good_streak = 0
        self._bad_streak = 0
        self._was_good_phase = False
        self.count = 0

    def reset(self):
        self._good_streak = 0
        self._bad_streak = 0
        self._was_good_phase = False
        self.count = 0

    def update(self, good_now: bool) -> int:
        """
        Update with current frame's good/bad.
        Returns current total reps. (+1 only on good->bad transition with hysteresis)
        """
        if good_now:
            self._good_streak += 1
            self._bad_streak = 0
            if self._good_streak >= self.good_min_frames:
                self._was_good_phase = True
        else:
            self._bad_streak += 1
            self._good_streak = 0
            if self._was_good_phase and self._bad_streak >= self.bad_min_frames:
                self.count += 1
                self._was_good_phase = False

        return self.count
