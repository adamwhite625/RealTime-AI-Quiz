from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.schemas.answer_dto import OptionInfo


class SoloQuestionItem(BaseModel):
    id: Optional[Union[str, int]] = Field(None, description="Question ID")
    text: str = Field(..., description="Question prompt text")
    options: List[OptionInfo] = Field(..., description="List of 4 options (A, B, C, D)")
    correct_option_id: Optional[Union[str, int]] = Field(None, description="Correct option ID")
    correct_label: Optional[str] = Field(None, description="Correct option label (e.g. A, B, C, D)")
    correct_text: Optional[str] = Field(None, description="Correct option text")
    explanation: Optional[str] = Field(None, description="Pre-configured explanation if available")


class SoloSessionStartRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional custom session identifier")
    quiz_id: Optional[str] = Field(None, description="Quiz ID in Spring Boot backend to fetch questions from")
    quiz_title: Optional[str] = Field("Bài Luyện Tập Solo", description="Title of the practice session")
    voice: Optional[str] = Field("Minh Quân", description="TTS preset voice (Minh Quân, Hải Đăng, Trúc Ly...)")
    questions: Optional[List[SoloQuestionItem]] = Field(None, description="Custom list of questions for practice")


class SoloSessionStateResponse(BaseModel):
    session_id: str
    quiz_title: str
    current_index: int
    total_questions: int
    score: int
    state: str  # "IDLE", "READING_QUESTION", "WAITING_FOR_ANSWER", "EXPLAINING", "COMPLETED"
    current_question: Optional[SoloQuestionItem] = None
    voice: str


class SoloUtteranceResult(BaseModel):
    user_transcription: str
    intent: str  # "answer", "hint", "explanation", "chit_chat", "unclear"
    matched_label: Optional[str] = None
    matched_text: Optional[str] = None
    is_correct: Optional[bool] = None
    bot_speech_text: str
    bot_audio_base64: Optional[str] = None
    session_completed: bool = False
    current_score: int = 0
