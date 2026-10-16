import subprocess
from pathlib import Path


def wav_bytes_to_mp3(
    wav_bytes: bytes,
    sample_rate: int = 16000,
    bitrate: str = "64k",
    channels: int = 1,
    ffmpeg_path: str = "ffmpeg",
) -> bytes:
    """Converts WAV bytes to MP3 bytes using ffmpeg."""
    cmd = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-ac", str(channels),
        "-ar", str(sample_rate),
        "-b:a", bitrate,
        "-f", "mp3",
        "pipe:1",
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate(wav_bytes)

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg wav->mp3 failed: {stderr.decode(errors='ignore')}")

    return stdout


def pcm16_to_wav_bytes(
    pcm16_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1,
) -> bytes:
    """Wraps raw PCM16 bytes into standard WAV format."""
    import io
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16_bytes)
    return buffer.getvalue()


def decode_audio_to_pcm16k(
    audio_bytes: bytes,
    target_sr: int = 16000,
    ffmpeg_path: str = "ffmpeg",
) -> "numpy.ndarray":
    """
    Decodes arbitrary audio bytes (WAV, WebM, MP3, OGG, Opus, AAC, etc.)
    into a mono float32 NumPy array at the target sample rate (default 16000Hz).
    Falls back to raw PCM16 buffer parsing if ffmpeg indicates raw stream.
    """
    import numpy as np

    cmd = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-ac", "1",
        "-ar", str(target_sr),
        "-f", "f32le",
        "pipe:1",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(audio_bytes)
        if proc.returncode == 0 and len(stdout) > 0:
            return np.frombuffer(stdout, dtype=np.float32)
    except Exception:
        pass

    # Fallback: assume input was already raw PCM16 mono
    try:
        raw_pcm16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return raw_pcm16.astype(np.float32) / 32768.0
    except Exception as exc:
        raise ValueError(f"Could not decode audio bytes to PCM: {exc}") from exc
