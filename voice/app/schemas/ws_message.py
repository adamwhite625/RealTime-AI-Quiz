from typing import Literal, Optional, Any
from pydantic import BaseModel, ConfigDict


class MediaPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    payload: str  # Base64 encoded audio
    sample_rate: Optional[int] = 16000


class ReceiveWsMessage(BaseModel):
    """Incoming message from Frontend (Player / Host) to Voice Service."""
    model_config = ConfigDict(extra="ignore")
    event: Literal["media", "start", "stop", "ping"]
    media: Optional[MediaPayload] = None
    data: Optional[dict[str, Any]] = None


class SendWsMessage(BaseModel):
    """Outgoing message from Voice Service to Frontend."""
    model_config = ConfigDict(extra="ignore")
    event: Literal["chunk", "transcription", "break", "answer_detected", "pong", "error"]
    media: Optional[MediaPayload] = None
    data: Optional[dict[str, Any]] = None
