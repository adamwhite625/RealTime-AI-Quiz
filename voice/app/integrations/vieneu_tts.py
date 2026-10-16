import asyncio
import io
import logging
import os
import pathlib
import shutil
import time
from hashlib import md5
from typing import Optional, Dict, Any, List, Tuple

import soundfile as sf
import numpy as np

from app.core.settings import settings
from app.utils.ffmpeg import wav_bytes_to_mp3

logger = logging.getLogger(__name__)


def _patch_vieneu_safe_fetch():
    """
    Patches vieneu's OnnxV3LiteEngine._fetch to copy real files into a local directory
    instead of using Hugging Face Hub symlinks. This resolves ONNX Runtime's security error:
    '[ONNXRuntimeError] : 1 : FAIL : External data path escapes model directory'.
    """
    try:
        from huggingface_hub import hf_hub_download
        import vieneu._v3_turbo_engine.onnx_runtime_lite as onnx_lite

        def _safe_fetch(repo: str, files: List[str], subfolder: Optional[str] = None) -> pathlib.Path:
            safe_dir = pathlib.Path("models/hf_safe") / repo.replace("/", "_") / (subfolder or "root")
            safe_dir.mkdir(parents=True, exist_ok=True)
            for fn in files:
                target = safe_dir / pathlib.Path(fn).name
                if not target.exists():
                    try:
                        src = hf_hub_download(repo, fn, repo_type="model", subfolder=subfolder or None)
                        shutil.copyfile(src, target)
                        logger.debug("Safe copy: %s -> %s", fn, target)
                    except Exception as e:
                        if fn.endswith((".json",)):
                            continue
                        raise e
            return safe_dir

        onnx_lite.OnnxV3LiteEngine._fetch = staticmethod(_safe_fetch)
        logger.info("VieNeu-TTS safe_fetch patch applied successfully")
    except Exception as exc:
        logger.warning("Could not apply VieNeu-TTS safe_fetch patch: %s", exc)


def _patch_vieneu_assets():
    """Ensure assets directory is correctly mapped in vieneu package."""
    try:
        import vieneu
        pkg_dir = pathlib.Path(vieneu.__file__).parent
        src = pkg_dir / "assets"
        dst = pkg_dir / "v3turbo" / "assets"
        if src.exists() and not dst.exists():
            shutil.copytree(src, dst)
            logger.info("VieNeu assets directory linked for v3turbo")
    except Exception as exc:
        logger.warning("Could not auto-link vieneu assets: %s", exc)


class VieNeuTTSClient:
    """
    Adapter integration for VieNeu-TTS-v3-Turbo (pnnbao-ump/VieNeu-TTS-v3-Turbo).
    Provides high-fidelity 48kHz Vietnamese speech synthesis with preset voices.
    """
    _instance: Optional["VieNeuTTSClient"] = None

    def __new__(cls) -> "VieNeuTTSClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = None
            cls._is_initialized = False
            cls._cache: Dict[str, Tuple[bytes, float]] = {}
            cls._lock = asyncio.Lock()
        return cls._instance

    def _ensure_engine_loaded(self):
        """Loads VieNeu-TTS-v3-Turbo engine lazily with patched safe fetch."""
        if self._engine is not None:
            return

        _patch_vieneu_assets()
        _patch_vieneu_safe_fetch()

        logger.info("Loading VieNeu-TTS-v3-Turbo engine (mode=v3turbo, 48kHz, ONNX CPU)...")
        start_time = time.perf_counter()
        
        try:
            from vieneu.v3turbo import V3TurboVieNeuTTS
            self._engine = V3TurboVieNeuTTS()
            load_time = time.perf_counter() - start_time
            logger.info("VieNeu-TTS engine loaded successfully in %.2fs", load_time)
            self._is_initialized = True
        except Exception as exc:
            logger.error("Failed to load VieNeu-TTS engine: %s", exc)
            self._engine = None
            raise RuntimeError(f"VieNeu-TTS initialization failed: {exc}") from exc

    def list_preset_voices(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available preset voices."""
        _patch_vieneu_assets()
        try:
            import json
            import vieneu as vn
            json_path = pathlib.Path(vn.__file__).parent / "assets" / "voices_v3_turbo.json"
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                presets = data.get("presets", {})
            else:
                presets = {}

            voices = []
            for name, meta in presets.items():
                voices.append({
                    "name": name,
                    "gender": meta.get("gender", "unknown") if isinstance(meta, dict) else "unknown",
                    "description": meta.get("description", "") if isinstance(meta, dict) else "",
                })
            return voices
        except Exception as exc:
            logger.warning("Could not list preset voices: %s", exc)
            return [{"name": "Hải Đăng", "gender": "male", "description": "Default Voice"}]

    def _cache_key(self, text: str, voice: str) -> str:
        return md5(f"{text}::{voice}".encode("utf-8")).hexdigest()

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        as_mp3: bool = True,
    ) -> Tuple[bytes, float, int]:
        """
        Synthesize speech from Vietnamese text.
        
        Args:
            text: Text to speak (supports emotion tags like [cười], [thở dài])
            voice: Name of preset voice (e.g. 'Hải Đăng', 'Trúc Ly', 'Mai Anh')
            as_mp3: If True, convert output audio to MP3; else WAV.

        Returns:
            Tuple of (audio_bytes, duration_seconds, sample_rate)
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Input text cannot be empty.")

        selected_voice = voice or settings.VIENEU_DEFAULT_VOICE or "Hải Đăng"
        cache_id = self._cache_key(clean_text, selected_voice)

        # Check in-memory cache
        if cache_id in self._cache:
            audio_bytes, duration = self._cache[cache_id]
            logger.info("TTS Cache HIT for '%s...' (%.2fs)", clean_text[:30], duration)
            return audio_bytes, duration, settings.VIENEU_SAMPLE_RATE

        async with self._lock:
            # Double-check cache inside lock
            if cache_id in self._cache:
                audio_bytes, duration = self._cache[cache_id]
                return audio_bytes, duration, settings.VIENEU_SAMPLE_RATE

            start_t = time.perf_counter()
            self._ensure_engine_loaded()

            # Execute model inference in thread pool to not block asyncio event loop
            def _infer_sync():
                audio_array = self._engine.infer(text=clean_text, voice=selected_voice)
                
                # Write to WAV buffer
                wav_buffer = io.BytesIO()
                sf.write(wav_buffer, audio_array, settings.VIENEU_SAMPLE_RATE, format="WAV", subtype="PCM_16")
                wav_data = wav_buffer.getvalue()
                duration = len(audio_array) / float(settings.VIENEU_SAMPLE_RATE)
                return wav_data, duration

            wav_bytes, duration_sec = await asyncio.to_thread(_infer_sync)
            infer_duration = time.perf_counter() - start_t
            logger.info(
                "VieNeu-TTS synthesized '%s...' (voice=%s, dur=%.2fs) in %.2fs",
                clean_text[:40],
                selected_voice,
                duration_sec,
                infer_duration,
            )

            # Convert to MP3 if requested
            if as_mp3:
                try:
                    final_audio = wav_bytes_to_mp3(wav_bytes, sample_rate=settings.VIENEU_SAMPLE_RATE, bitrate="128k")
                except Exception as exc:
                    logger.warning("MP3 conversion failed, using WAV instead: %s", exc)
                    final_audio = wav_bytes
            else:
                final_audio = wav_bytes

            # Cache short static sentences (< 100 characters)
            if len(clean_text) <= 100:
                self._cache[cache_id] = (final_audio, duration_sec)

            return final_audio, duration_sec, settings.VIENEU_SAMPLE_RATE


vieneu_tts = VieNeuTTSClient()
