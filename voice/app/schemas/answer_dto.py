from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class OptionInfo(BaseModel):
    id: Optional[Union[str, int]] = Field(None, description="Option ID from backend")
    label: Optional[str] = Field(None, description="Option Label (e.g., A, B, C, D)")
    text: str = Field(..., description="Option content text")


class TranscribeResponse(BaseModel):
    text: str = Field(..., description="Transcribed speech text")
    language: str = Field("vi", description="Detected or specified language")
    duration_sec: float = Field(0.0, description="Duration of processed audio in seconds")


class MatchAnswerRequest(BaseModel):
    question_id: Optional[Union[str, int]] = Field(None, description="Question ID")
    transcribed_text: Optional[str] = Field(None, description="Raw transcribed text if already available")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio bytes (WAV, WebM, MP3)")
    options: List[OptionInfo] = Field(..., description="List of options for the current question")


class MatchAnswerResponse(BaseModel):
    transcribed_text: str = Field(..., description="Transcribed text from speech")
    matched_option_id: Optional[Union[str, int]] = Field(None, description="Matched Option ID")
    matched_label: Optional[str] = Field(None, description="Matched label (A, B, C, D)")
    matched_text: Optional[str] = Field(None, description="Matched option text")
    confidence: float = Field(0.0, description="Matching confidence score (0.0 to 1.0)")
    match_type: str = Field("none", description="Match mechanism: 'label', 'index', 'content', or 'none'")
    is_matched: bool = Field(False, description="Whether an option was successfully recognized")
    submission_result: Optional[Dict[str, Any]] = Field(None, description="Response from Spring Boot backend if submitted")


class VoiceAnswerSubmitRequest(BaseModel):
    session_id: str = Field(..., description="Quiz game session ID (e.g. PIN or UUID)")
    player_id: int = Field(..., description="Player ID submitting the answer")
    question_id: int = Field(..., description="Question ID being answered")
    options: List[OptionInfo] = Field(..., description="List of options for the question")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio of player speaking answer")
    transcribed_text: Optional[str] = Field(None, description="Transcribed text if already parsed on client")
