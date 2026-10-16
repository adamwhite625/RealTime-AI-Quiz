from fastapi import APIRouter
from app.core.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Service health and diagnostic status."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "backend_target": settings.SPRING_BACKEND_URL,
        "tts_engine": settings.TTS_ENGINE,
        "stt_engine": settings.STT_ENGINE,
    }
