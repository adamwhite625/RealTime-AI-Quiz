import numpy as np
from numpy.typing import NDArray
from scipy import signal


def resample_audio(audio: NDArray, orig_sr: int, target_sr: int) -> NDArray:
    """
    Resamples the given audio signal from the original sample rate to the target sample rate.

    Parameters:
    - audio (NDArray): Input audio signal as a NumPy array.
    - orig_sr (int): Original sample rate of the audio.
    - target_sr (int): Target sample rate.

    Returns:
    - NDArray: The resampled audio signal.
    """
    if orig_sr == target_sr:
        return audio

    orig_dtype = audio.dtype
    gcd = np.gcd(orig_sr, target_sr)
    up = target_sr // gcd
    down = orig_sr // gcd

    resampled = signal.resample_poly(audio, up, down)

    if np.issubdtype(orig_dtype, np.integer):
        info = np.iinfo(orig_dtype)
        resampled = np.clip(resampled, info.min, info.max)
        resampled = resampled.astype(orig_dtype)
    else:
        resampled = resampled.astype(orig_dtype)

    return resampled


def calculate_dbfs(audio: NDArray, eps: float = 1e-10) -> float:
    """
    Calculate dBFS (decibels relative to full scale) for an audio signal.

    Supports int16, int32, float32, float64.
    """
    audio = np.asarray(audio)

    if audio.size == 0:
        return -np.inf

    if np.issubdtype(audio.dtype, np.integer):
        max_val = np.iinfo(audio.dtype).max
        audio_float = audio.astype(np.float32) / max_val
    elif np.issubdtype(audio.dtype, np.floating):
        audio_float = audio.astype(np.float32)
    else:
        raise TypeError(f"Unsupported audio dtype: {audio.dtype}")

    rms = np.sqrt(np.mean(audio_float ** 2))
    rms = max(rms, eps)

    dbfs = 20.0 * np.log10(rms)
    return float(dbfs)
