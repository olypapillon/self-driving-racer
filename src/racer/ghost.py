"""The see-through replay of the fastest run so far."""

import bisect
import json
from dataclasses import dataclass

from .settings import FIXED_STEP, GHOST_PATH, RULES_VERSION


@dataclass
class Ghost:
    """A recorded run: ``frames[k]`` is the car's (distance, x) after k steps."""

    name: str
    time: float
    frames: list

    def at(self, steps):
        """Where the ghost is after ``steps``, or None once it has finished."""
        if steps >= len(self.frames):
            return None
        return self.frames[steps]

    def time_at(self, distance):
        """Race time at which the ghost reached ``distance``."""
        distances = [frame[0] for frame in self.frames]
        index = bisect.bisect_left(distances, distance)
        return min(index, len(self.frames) - 1) * FIXED_STEP


def load_ghost():
    try:
        data = json.loads(GHOST_PATH.read_text())
        if data.get("rules") != RULES_VERSION:
            return None
        return Ghost(data["name"], data["time"], [tuple(f) for f in data["frames"]])
    except (OSError, ValueError, KeyError):
        return None


def save_ghost(ghost):
    """Keep the leader's run between sessions (a no-op where files can't be written)."""
    try:
        GHOST_PATH.parent.mkdir(exist_ok=True)
        GHOST_PATH.write_text(
            json.dumps(
                {
                    "rules": RULES_VERSION,
                    "name": ghost.name,
                    "time": ghost.time,
                    "frames": ghost.frames,
                }
            )
        )
    except OSError:
        pass
