import logging
from typing import List, Dict, Any, Tuple, Optional

from app.integrations.vieneu_tts import vieneu_tts
from app.schemas.mc_dto import SpeakQuestionRequest, SpeakCommentaryRequest, QuestionOptionDto

logger = logging.getLogger(__name__)

OPTION_LABELS = ["A", "B", "C", "D", "E", "F"]


class MCService:
    """
    Business Logic Service for Virtual AI MC (Host) in QuizMaster.
    Generates dynamic spoken scripts with emotional cues and converts them to high-quality audio.
    """

    @staticmethod
    def build_question_script(
        question_text: str,
        options: List[QuestionOptionDto],
        include_options: bool = True,
        question_number: Optional[int] = None,
    ) -> str:
        """Formats question text and choices into natural MC speech."""
        prefix = f"Câu hỏi số {question_number}: " if question_number else "Câu hỏi: "
        script_parts = [f"{prefix}{question_text.strip()}"]

        if include_options and options:
            script_parts.append("Các lựa chọn là:")
            # Sort by order_index
            sorted_options = sorted(options, key=lambda o: o.order_index)
            for idx, opt in enumerate(sorted_options):
                label = OPTION_LABELS[idx] if idx < len(OPTION_LABELS) else f"Số {idx + 1}"
                script_parts.append(f"Đáp án {label}: {opt.text.strip()}.")

        return " ".join(script_parts)

    @staticmethod
    def build_commentary_script(
        event_type: str,
        context_text: str,
        emotion_tag: Optional[str] = None,
    ) -> str:
        """Formats game events into energetic MC commentary with emotion tags."""
        emotion = f" {emotion_tag}" if emotion_tag else ""
        clean_context = context_text.strip()

        match event_type.upper():
            case "ROUND_END":
                return f"Đã hết giờ trả lời! {clean_context}{emotion or ' [cười]'}"
            case "REVEAL_ANSWER":
                return f"Đáp án chính xác là: {clean_context}. Xin chúc mừng các bạn đã có câu trả lời đúng!{emotion or ' [cười]'}"
            case "LEADERBOARD":
                return f"Bảng xếp hạng sau câu hỏi vừa rồi: {clean_context}. Cuộc đua đang rất kịch tính!{emotion or ' [cười]'}"
            case "GAME_OVER":
                return f"Trận đấu đã chính thức khép lại! {clean_context}{emotion or ' [cười]'} Cảm ơn tất cả các bạn đã thi đấu hết mình!"
            case _:
                return f"{clean_context}{emotion}"

    async def speak_question(self, request: SpeakQuestionRequest) -> Tuple[bytes, float, int]:
        """Synthesize spoken audio for a question and its options."""
        script = self.build_question_script(
            question_text=request.question_text,
            options=request.options,
            include_options=request.include_options,
            question_number=request.question_id,
        )
        logger.info("MC Question Script: %s", script)
        return await vieneu_tts.synthesize(text=script, voice=request.voice, as_mp3=True)

    async def speak_commentary(self, request: SpeakCommentaryRequest) -> Tuple[bytes, float, int]:
        """Synthesize commentary audio for game events."""
        script = self.build_commentary_script(
            event_type=request.event_type,
            context_text=request.context_text,
            emotion_tag=request.emotion_tag,
        )
        logger.info("MC Commentary Script: %s", script)
        return await vieneu_tts.synthesize(text=script, voice=request.voice, as_mp3=True)

    async def synthesize_text(self, text: str, voice: Optional[str] = None) -> Tuple[bytes, float, int]:
        """Synthesize arbitrary text with VieNeu-TTS."""
        return await vieneu_tts.synthesize(text=text, voice=voice, as_mp3=True)

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """List all voices supported by the engine."""
        return vieneu_tts.list_preset_voices()


mc_service = MCService()
