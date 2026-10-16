from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionOptionDto(BaseModel):
    id: int
    text: str
    order_index: int


class SpeakQuestionRequest(BaseModel):
    question_id: int
    question_text: str
    options: List[QuestionOptionDto] = Field(default_factory=list)
    voice: Optional[str] = None
    include_options: bool = True


class SpeakCommentaryRequest(BaseModel):
    session_id: str
    event_type: str = Field(..., description="e.g. ROUND_END, GAME_OVER, STREAK")
    context_text: str
    emotion_tag: Optional[str] = Field(None, description="e.g. [cười], [thở dài]")
    voice: Optional[str] = None


class SynthesisResponse(BaseModel):
    success: bool
    audio_base64: Optional[str] = None
    duration_sec: Optional[float] = None
    sample_rate: int = 48000
    message: Optional[str] = None
