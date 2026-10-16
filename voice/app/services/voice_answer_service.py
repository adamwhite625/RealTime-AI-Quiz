import logging
from typing import Optional, Dict, Any, Union
import httpx

from app.core.settings import settings
from app.integrations.sherpa_stt import stt_client
from app.schemas.answer_dto import MatchAnswerRequest, MatchAnswerResponse, VoiceAnswerSubmitRequest
from app.services.answer_matcher import answer_matcher

logger = logging.getLogger(__name__)


class VoiceAnswerService:
    """
    Coordinates Voice-based Answer Processing:
    Audio Decoding -> Sherpa-ONNX STT -> Pattern/Fuzzy Matcher -> (Optional) Spring Boot Submission.
    """

    async def transcribe_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Transcribes incoming audio bytes to Vietnamese text."""
        text, duration = await stt_client.transcribe_bytes(audio_bytes)
        return {
            "text": text,
            "language": "vi",
            "duration_sec": round(duration, 2),
        }

    async def match_voice_answer(self, req: MatchAnswerRequest) -> MatchAnswerResponse:
        """
        Determines the player's chosen answer option from audio or transcribed text.
        """
        text = req.transcribed_text or ""

        # 1. Transcribe audio if provided
        if req.audio_base64 and not text:
            transcribed, dur = await stt_client.transcribe_base64(req.audio_base64)
            text = transcribed

        # 2. Match text against options
        match_result = answer_matcher.match(text, req.options)
        return match_result

    async def submit_to_spring_backend(
        self,
        session_id: str,
        player_id: int,
        question_id: int,
        selected_option_id: Union[int, str],
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls Spring Boot backend to submit the player's answer:
        POST /api/sessions/{sessionId}/submit-answer
        """
        url = f"{settings.SPRING_BACKEND_URL}/api/sessions/{session_id}/submit-answer"
        payload = {
            "playerId": player_id,
            "questionId": question_id,
            "selectedOptionId": int(selected_option_id),
        }
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    return res.json()
                else:
                    logger.warning("Spring Boot submit-answer failed (%d): %s", res.status_code, res.text)
                    return {
                        "error": True,
                        "status_code": res.status_code,
                        "detail": res.text,
                    }
        except Exception as exc:
            logger.error("Failed to connect to Spring Boot backend: %s", exc)
            return {"error": True, "detail": str(exc)}

    async def process_and_submit(
        self,
        req: VoiceAnswerSubmitRequest,
        auth_token: Optional[str] = None,
    ) -> MatchAnswerResponse:
        """
        End-to-end voice answer pipeline:
        Transcribe audio -> Match Option -> Automatically submit to Spring Boot if matched.
        """
        match_req = MatchAnswerRequest(
            question_id=req.question_id,
            options=req.options,
            audio_base64=req.audio_base64,
            transcribed_text=req.transcribed_text,
        )
        match_res = await self.match_voice_answer(match_req)

        # If matched and option has valid ID, forward to Spring Boot
        if match_res.is_matched and match_res.matched_option_id is not None:
            submission = await self.submit_to_spring_backend(
                session_id=req.session_id,
                player_id=req.player_id,
                question_id=req.question_id,
                selected_option_id=match_res.matched_option_id,
                auth_token=auth_token,
            )
            match_res.submission_result = submission

        return match_res


voice_answer_service = VoiceAnswerService()
