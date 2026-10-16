import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.settings import settings
from app.api import health, mc_controller, answer_controller, solo_controller

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s on port %s...", settings.APP_NAME, settings.PORT)
    # Eagerly verify engines
    try:
        from app.integrations.sherpa_stt import stt_client
        logger.info("Sherpa STT Engine ready")
    except Exception as exc:
        logger.warning("Sherpa STT pre-check warning: %s", exc)
    try:
        from app.integrations.gemini_llm import gemini_llm
        if gemini_llm.is_configured:
            logger.info("Gemini LLM Engine configured (%s)", settings.GEMINI_MODEL)
    except Exception as exc:
        logger.warning("Gemini LLM pre-check warning: %s", exc)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time Voice AI Engine for QuizMaster (TTS, STT, and Solo Voicebot)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware for Frontend & Backend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(mc_controller.router)
app.include_router(answer_controller.router)
app.include_router(solo_controller.router)

# Direct WebSocket aliases
app.add_api_websocket_route("/ws/voice-answer", answer_controller.websocket_voice_answer)
app.add_api_websocket_route("/ws/solo-practice", solo_controller.solo_voicebot_websocket)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is active",
        "docs": "/docs",
        "health": "/health",
    }
