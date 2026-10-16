import logging
from typing import Optional, Callable
import numpy as np

from app.core.settings import settings
from app.utils.audio import calculate_dbfs

logger = logging.getLogger(__name__)


class BargeInDetector:
    """
    Lightweight, low-latency Voice Activity & Barge-in Detector.
    Monitors incoming user audio frames to detect when a player interrupts the bot.
    """

    def __init__(
        self,
        dbfs_threshold: float = -38.0,
        min_speech_frames: int = 2,
        on_barge_in: Optional[Callable[[], None]] = None,
    ):
        self.dbfs_threshold = dbfs_threshold
        self.min_speech_frames = min_speech_frames
        self.on_barge_in = on_barge_in

        self._consecutive_speech_frames = 0
        self._is_barge_in_triggered = False

    def reset(self):
        """Reset detector state for a new turn."""
        self._consecutive_speech_frames = 0
        self._is_barge_in_triggered = False

    def process_frame(self, frame_samples: np.ndarray) -> bool:
        """
        Analyzes a single PCM frame (e.g. 10ms-30ms).
        Returns True if barge-in was just triggered.
        """
        if frame_samples.size == 0 or self._is_barge_in_triggered:
            return False

        dbfs = calculate_dbfs(frame_samples)

        if dbfs > self.dbfs_threshold:
            self._consecutive_speech_frames += 1
            if self._consecutive_speech_frames >= self.min_speech_frames:
                self._is_barge_in_triggered = True
                logger.info(
                    "Barge-in triggered! (dbfs=%.1f > threshold=%.1f, frames=%d)",
                    dbfs,
                    self.dbfs_threshold,
                    self._consecutive_speech_frames,
                )
                if self.on_barge_in:
                    try:
                        self.on_barge_in()
                    except Exception as exc:
                        logger.warning("Error in on_barge_in callback: %s", exc)
                return True
        else:
            # Decay speech frame count on silence
            self._consecutive_speech_frames = max(0, self._consecutive_speech_frames - 1)

        return False
