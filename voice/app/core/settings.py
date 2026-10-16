import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = Field("quizmaster-voice-engine", description="Name of the voice service")
    PORT: int = Field(8001, description="HTTP / WebSocket port for the voice service")
    HOST: str = Field("0.0.0.0", description="Bind host")
    WS_PATH: str = Field("/ws/voice", description="Base WebSocket path")

    # Logging
    LOG_LEVEL: str = Field("INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    LOG_DIR: str = Field("logs", description="Directory to store log files")

    # Backend Integration (Spring Boot)
    SPRING_BACKEND_URL: str = Field("http://localhost:8080", description="Spring Boot Backend URL")

    # Audio & VAD Settings
    CLIENT_AUDIO_SR: int = Field(16000, description="Audio sample rate (Hz)")
    TENVAD_HOP_SIZE: int = Field(640, description="Hop size for VAD processing")
    TENVAD_THRESHOLD: float = Field(0.7, description="Speech probability threshold for VAD")
    VAD_DBFS_THRESHOLD: float = Field(-40.0, description="dBFS threshold for detecting speech")
    SILENCE_TIMEOUT_SEC: float = Field(5.0, description="Seconds of silence before timeout")

    # TTS Settings (VieNeu-TTS-v3-Turbo)
    TTS_ENGINE: str = Field("vieneu", description="TTS Engine: vieneu or api")
    VIENEU_MODEL_ID: str = Field("pnnbao-ump/VieNeu-TTS-v3-Turbo", description="Hugging Face Model ID")
    VIENEU_DEFAULT_VOICE: str = Field("Minh Quân", description="Default preset voice")
    VIENEU_SAMPLE_RATE: int = Field(48000, description="VieNeu-TTS output sample rate")

    # STT Settings (Sherpa-ONNX / Whisper)
    STT_ENGINE: str = Field("sherpa_onnx", description="STT Engine: sherpa_onnx or whisper_onnx")
    STT_MODEL_PATH: str = Field("models/stt", description="Path to lightweight ONNX model weights")

    # LLM Settings (Google Gemini)
    GEMINI_API_KEY: Optional[str] = Field(None, description="Gemini API Key (set via GEMINI_API_KEY env)")
    GEMINI_MODEL: str = Field("gemini-3.5-flash-lite", description="Gemini Model Identifier")


settings = Settings()
