import base64
from typing import Literal, Optional
from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.services.mc_service import mc_service
from app.schemas.mc_dto import (
    SpeakQuestionRequest,
    SpeakCommentaryRequest,
    SynthesisResponse,
)

router = APIRouter(prefix="/api/v1/mc", tags=["Virtual MC (TTS)"])


class RawSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize with VieNeu-TTS")
    voice: Optional[str] = Field(None, description="Preset voice name (e.g. 'Hải Đăng', 'Trúc Ly')")


@router.get("/voices")
def get_voices():
    """List all available VieNeu-TTS preset voices."""
    return {"voices": mc_service.get_available_voices()}


@router.post("/question")
async def speak_question(
    request: SpeakQuestionRequest,
    response_format: Literal["audio", "json"] = Query("audio", description="Format: 'audio' (mp3 stream) or 'json' (base64)"),
):
    """
    Synthesizes natural MC speech for a Quiz question and its answer choices.
    """
    audio_bytes, duration, sample_rate = await mc_service.speak_question(request)

    if response_format == "audio":
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=question_{request.question_id}.mp3",
                "X-Audio-Duration": str(round(duration, 3)),
                "X-Audio-Sample-Rate": str(sample_rate),
            },
        )

    b64_data = base64.b64encode(audio_bytes).decode("utf-8")
    return SynthesisResponse(
        success=True,
        audio_base64=b64_data,
        duration_sec=round(duration, 3),
        sample_rate=sample_rate,
        message="Synthesized question audio successfully",
    )


@router.post("/commentary")
async def speak_commentary(
    request: SpeakCommentaryRequest,
    response_format: Literal["audio", "json"] = Query("audio", description="Format: 'audio' or 'json'"),
):
    """
    Synthesizes dynamic MC commentary for round endings, reveals, or leaderboard updates.
    """
    audio_bytes, duration, sample_rate = await mc_service.speak_commentary(request)

    if response_format == "audio":
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=commentary_{request.session_id}.mp3",
                "X-Audio-Duration": str(round(duration, 3)),
                "X-Audio-Sample-Rate": str(sample_rate),
            },
        )

    b64_data = base64.b64encode(audio_bytes).decode("utf-8")
    return SynthesisResponse(
        success=True,
        audio_base64=b64_data,
        duration_sec=round(duration, 3),
        sample_rate=sample_rate,
        message="Synthesized commentary audio successfully",
    )


@router.post("/synthesize")
async def raw_synthesize(
    payload: RawSpeechRequest,
    response_format: Literal["audio", "json"] = Query("audio", description="Format: 'audio' or 'json'"),
):
    """
    Direct TTS endpoint for arbitrary Vietnamese text with emotion tags.
    """
    audio_bytes, duration, sample_rate = await mc_service.synthesize_text(
        text=payload.text,
        voice=payload.voice,
    )

    if response_format == "audio":
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "X-Audio-Duration": str(round(duration, 3)),
                "X-Audio-Sample-Rate": str(sample_rate),
            },
        )

    b64_data = base64.b64encode(audio_bytes).decode("utf-8")
    return SynthesisResponse(
        success=True,
        audio_base64=b64_data,
        duration_sec=round(duration, 3),
        sample_rate=sample_rate,
        message="Synthesized speech successfully",
    )
