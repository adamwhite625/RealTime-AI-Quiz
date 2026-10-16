import asyncio
import base64
import logging
import os
import pathlib
import time
from typing import Optional, Tuple
import numpy as np

from app.core.settings import settings
from app.utils.ffmpeg import decode_audio_to_pcm16k

logger = logging.getLogger(__name__)


class SherpaSTTClient:
    """
    Adapter integration for Sherpa-ONNX lightweight Speech-to-Text engine.
    Supports:
    1. Vietnamese Zipformer 30M (int8 ONNX) - Fast, CPU friendly, native Vietnamese diacritics.
    2. Whisper Tiny (int8 ONNX) - General multilingual fallback.
    """
    _instance: Optional["SherpaSTTClient"] = None

    def __new__(cls) -> "SherpaSTTClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recognizer = None
            cls._instance._engine_type = None
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def _find_model_path(self, *relative_candidates: str) -> Optional[pathlib.Path]:
        """Looks for model directory in /app or current directory."""
        bases = [pathlib.Path("/app"), pathlib.Path("."), pathlib.Path("..")]
        for rel in relative_candidates:
            for base in bases:
                cand = (base / rel).resolve()
                if cand.exists():
                    return cand
        return None

    def _ensure_model_loaded(self):
        """Loads sherpa-onnx recognizer lazily."""
        if self._recognizer is not None:
            return

        import sherpa_onnx

        # 1. Check for Zipformer Vietnamese (preferred for VN quiz answers)
        zipformer_dir = self._find_model_path("models/stt_zipformer_vi", "voice/models/stt_zipformer_vi")
        if zipformer_dir and (zipformer_dir / "encoder.int8.onnx").exists():
            logger.info("Initializing Sherpa-ONNX Vietnamese Zipformer-30M from %s...", zipformer_dir)
            t0 = time.perf_counter()
            self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=str(zipformer_dir / "encoder.int8.onnx"),
                decoder=str(zipformer_dir / "decoder.onnx"),
                joiner=str(zipformer_dir / "joiner.int8.onnx"),
                tokens=str(zipformer_dir / "tokens.txt"),
                num_threads=2,
            )
            self._engine_type = "zipformer_vi"
            logger.info("Sherpa-ONNX Zipformer initialized in %.2fs", time.perf_counter() - t0)
            return

        # 2. Check for Whisper Tiny (fallback)
        whisper_dir = self._find_model_path("models/stt_whisper_tiny", "voice/models/stt_whisper_tiny")
        if whisper_dir and (whisper_dir / "tiny-encoder.int8.onnx").exists():
            logger.info("Initializing Sherpa-ONNX Whisper-Tiny from %s...", whisper_dir)
            t0 = time.perf_counter()
            self._recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=str(whisper_dir / "tiny-encoder.int8.onnx"),
                decoder=str(whisper_dir / "tiny-decoder.int8.onnx"),
                tokens=str(whisper_dir / "tiny-tokens.txt"),
                language="vi",
                num_threads=2,
            )
            self._engine_type = "whisper_tiny"
            logger.info("Sherpa-ONNX Whisper initialized in %.2fs", time.perf_counter() - t0)
            return

        raise RuntimeError(
            "No compatible STT model found in models/stt_zipformer_vi or models/stt_whisper_tiny. "
            "Please ensure model weights exist."
        )

    def _sync_transcribe(self, samples: np.ndarray, sample_rate: int = 16000) -> str:
        """Synchronous decoding of float32 samples at 16000Hz."""
        self._ensure_model_loaded()
        if len(samples) == 0:
            return ""

        stream = self._recognizer.create_stream()
        stream.accept_waveform(sample_rate, samples)
        self._recognizer.decode_stream(stream)
        return stream.result.text.strip()

    async def transcribe_samples(self, samples: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe float32 audio samples asynchronously without blocking event loop."""
        async with self._lock:
            return await asyncio.to_thread(self._sync_transcribe, samples, sample_rate)

    async def transcribe_bytes(self, audio_bytes: bytes, target_sr: int = 16000) -> Tuple[str, float]:
        """
        Transcribe arbitrary audio bytes (WAV, WebM, MP3, OGG, PCM) to text.
        
        Returns:
            Tuple of (transcribed_text, audio_duration_seconds)
        """
        if not audio_bytes:
            return "", 0.0

        # Decode to 16kHz float32 numpy array
        samples = await asyncio.to_thread(decode_audio_to_pcm16k, audio_bytes, target_sr)
        duration_sec = len(samples) / float(target_sr) if len(samples) > 0 else 0.0

        if duration_sec < 0.2:
            return "", duration_sec

        text = await self.transcribe_samples(samples, target_sr)
        logger.info("STT Transcribed (%.2fs): '%s' [engine=%s]", duration_sec, text, self._engine_type)
        return text, duration_sec

    async def transcribe_base64(self, audio_base64: str, target_sr: int = 16000) -> Tuple[str, float]:
        """Decodes base64 string and transcribes it."""
        # Strip potential data URL prefix: data:audio/webm;base64,...
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",", 1)[1]
        raw_bytes = base64.b64decode(audio_base64)
        return await self.transcribe_bytes(raw_bytes, target_sr)


stt_client = SherpaSTTClient()
