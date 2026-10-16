import asyncio
import base64
import logging
import uuid
from typing import Dict, List, Optional

from app.core.settings import settings
from app.integrations.gemini_llm import gemini_llm
from app.integrations.vieneu_tts import vieneu_tts
from app.schemas.answer_dto import OptionInfo
from app.schemas.solo_dto import (
    SoloQuestionItem,
    SoloSessionStartRequest,
    SoloSessionStateResponse,
    SoloUtteranceResult,
)
from app.services.answer_matcher import answer_matcher

logger = logging.getLogger(__name__)

DEFAULT_PRACTICE_QUESTIONS: List[SoloQuestionItem] = [
    SoloQuestionItem(
        id=1,
        text="Thủ đô của Việt Nam là thành phố nào?",
        options=[
            OptionInfo(id=101, label="A", text="Hà Nội"),
            OptionInfo(id=102, label="B", text="Đà Nẵng"),
            OptionInfo(id=103, label="C", text="Thành phố Hồ Chí Minh"),
            OptionInfo(id=104, label="D", text="Huế"),
        ],
        correct_option_id=101,
        correct_label="A",
        correct_text="Hà Nội",
        explanation="Hà Nội là thủ đô ngàn năm văn hiến và là trung tâm chính trị của Việt Nam.",
    ),
    SoloQuestionItem(
        id=2,
        text="Hành tinh nào nằm ở vị trí gần Mặt Trời nhất trong Hệ Mặt Trời?",
        options=[
            OptionInfo(id=201, label="A", text="Sao Kim"),
            OptionInfo(id=202, label="B", text="Sao Thủy"),
            OptionInfo(id=203, label="C", text="Sao Hỏa"),
            OptionInfo(id=204, label="D", text="Sao Mộc"),
        ],
        correct_option_id=202,
        correct_label="B",
        correct_text="Sao Thủy",
        explanation="Sao Thủy (Mercury) là hành tinh nhỏ nhất và gần Mặt Trời nhất.",
    ),
    SoloQuestionItem(
        id=3,
        text="Đỉnh núi nào cao nhất Việt Nam và được mệnh danh là nóc nhà Đông Dương?",
        options=[
            OptionInfo(id=301, label="A", text="Fansipan"),
            OptionInfo(id=302, label="B", text="Bạch Mộc Lương Tử"),
            OptionInfo(id=303, label="C", text="Tây Côn Lĩnh"),
            OptionInfo(id=304, label="D", text="Pu Si Lung"),
        ],
        correct_option_id=301,
        correct_label="A",
        correct_text="Fansipan",
        explanation="Fansipan cao 3.143 mét tại dãy Hoàng Liên Sơn, tỉnh Lào Cai.",
    ),
]


class SoloPracticeSession:
    """Manages the lifecycle and state of a single player's practice game."""

    def __init__(
        self,
        session_id: str,
        quiz_title: str,
        questions: List[SoloQuestionItem],
        voice: str = "Minh Quân",
    ):
        self.session_id = session_id
        self.quiz_title = quiz_title
        self.questions = questions or DEFAULT_PRACTICE_QUESTIONS
        self.voice = voice or settings.VIENEU_DEFAULT_VOICE
        self.current_index = 0
        self.score = 0
        self.state = "IDLE"  # "READING_QUESTION", "WAITING_FOR_ANSWER", "COMPLETED"
        self.is_playing = False
        self._lock = asyncio.Lock()

    def get_current_question(self) -> Optional[SoloQuestionItem]:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def format_question_speech(self, q: SoloQuestionItem) -> str:
        """Constructs natural speech text for the MC reading the question and 4 choices."""
        opts_speech = []
        for idx, opt in enumerate(q.options):
            label = opt.label or chr(65 + idx)
            opts_speech.append(f"Đáp án {label}: {opt.text}.")
        
        return (
            f"Câu hỏi số {self.current_index + 1}: {q.text} "
            f"Các lựa chọn là: {' '.join(opts_speech)}"
        )

    async def generate_speech_audio(self, text: str) -> tuple[bytes, str]:
        """Synthesizes text via VieNeu-TTS and returns raw audio bytes and base64 string."""
        wav_bytes, dur, sr = await vieneu_tts.synthesize(text, voice=self.voice, as_mp3=False)
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        return wav_bytes, b64

    async def handle_user_speech(self, user_text: str) -> SoloUtteranceResult:
        """Processes player speech, recognizes intent, and formulates response."""
        async with self._lock:
            q = self.get_current_question()
            if not q:
                return SoloUtteranceResult(
                    user_transcription=user_text,
                    intent="completed",
                    bot_speech_text="Bạn đã hoàn thành tất cả các câu hỏi rồi!",
                    session_completed=True,
                    current_score=self.score,
                )

            norm = user_text.lower().strip()

            # 1. Check for Hint intent
            hint_triggers = ["gợi ý", "manh mối", "hint", "khó quá", "chỉ giùm", "giúp tôi", "bó tay"]
            if any(trig in norm for trig in hint_triggers):
                options_str = [f"{o.label or ''} {o.text}" for o in q.options]
                hint_text = await gemini_llm.generate_hint(
                    question=q.text,
                    options=options_str,
                    correct_answer=q.correct_text or str(q.correct_label),
                )
                if not hint_text:
                    hint_text = f"Hãy tập trung suy nghĩ về các lựa chọn nhé: {', '.join([o.text for o in q.options])}."

                _, b64 = await self.generate_speech_audio(hint_text)
                return SoloUtteranceResult(
                    user_transcription=user_text,
                    intent="hint",
                    bot_speech_text=hint_text,
                    bot_audio_base64=b64,
                    session_completed=False,
                    current_score=self.score,
                )

            # 2. Check for Explanation intent
            expl_triggers = ["tại sao", "giải thích", "vì sao", "lý do", "sao lại thế"]
            if any(trig in norm for trig in expl_triggers):
                options_str = [f"{o.label or ''} {o.text}" for o in q.options]
                expl_text = await gemini_llm.generate_explanation(
                    question=q.text,
                    options=options_str,
                    correct_answer=q.correct_text or str(q.correct_label),
                )
                if not expl_text:
                    expl_text = q.explanation or "Đáp án này đã được xác nhận là chuẩn xác nhất."

                _, b64 = await self.generate_speech_audio(expl_text)
                return SoloUtteranceResult(
                    user_transcription=user_text,
                    intent="explanation",
                    bot_speech_text=expl_text,
                    bot_audio_base64=b64,
                    session_completed=False,
                    current_score=self.score,
                )

            # 3. Check for Casual Chit-chat
            chat_triggers = ["chào", "xin chào", "bạn là ai", "tên gì", "bạn tên là gì"]
            if any(trig in norm for trig in chat_triggers):
                chat_text = await gemini_llm.generate_tutor_chat(
                    question=q.text,
                    user_speech=user_text,
                )
                if not chat_text:
                    chat_text = f"Xin chào! Tôi là MC của QuizMaster. Bạn đã sẵn sàng chọn đáp án cho câu hỏi chưa?"

                _, b64 = await self.generate_speech_audio(chat_text)
                return SoloUtteranceResult(
                    user_transcription=user_text,
                    intent="chit_chat",
                    bot_speech_text=chat_text,
                    bot_audio_base64=b64,
                    session_completed=False,
                    current_score=self.score,
                )

            # 4. Check for Answer choice
            match_res = answer_matcher.match(user_text, q.options)
            if match_res.is_matched:
                chosen_id = match_res.matched_option_id
                chosen_label = (match_res.matched_label or "").upper()
                chosen_text = match_res.matched_text

                # Determine if correct
                is_correct = False
                if q.correct_option_id and chosen_id:
                    is_correct = str(chosen_id) == str(q.correct_option_id)
                elif q.correct_label:
                    is_correct = chosen_label == q.correct_label.upper()
                elif q.correct_text:
                    is_correct = chosen_text.lower() == q.correct_text.lower()

                if is_correct:
                    self.score += 100
                    praise = f"Chính xác! Đáp án {chosen_label} là đáp án hoàn toàn đúng. [cười]"
                    feedback_text = praise
                else:
                    feedback_text = f"Rất tiếc, chưa đúng rồi. Đáp án đúng là {q.correct_label}: {q.correct_text}."
                    # Optional brief explanation from Gemini or pre-configured
                    if q.explanation:
                        feedback_text += f" {q.explanation}"

                # Advance to next question
                self.current_index += 1
                next_q = self.get_current_question()

                if next_q:
                    feedback_text += f" Chúng ta cùng đến với câu hỏi tiếp theo nhé!"
                    completed = False
                else:
                    feedback_text += f" Chúc mừng bạn đã hoàn thành bài luyện tập với tổng điểm là {self.score} điểm!"
                    completed = True
                    self.state = "COMPLETED"

                _, b64 = await self.generate_speech_audio(feedback_text)
                return SoloUtteranceResult(
                    user_transcription=user_text,
                    intent="answer",
                    matched_label=chosen_label,
                    matched_text=chosen_text,
                    is_correct=is_correct,
                    bot_speech_text=feedback_text,
                    bot_audio_base64=b64,
                    session_completed=completed,
                    current_score=self.score,
                )

            # 5. Unrecognized utterance
            fallback_text = "Tôi chưa nghe rõ bạn chọn đáp án nào. Bạn hãy nói lại xem bạn chọn A, B, C hay D nhé!"
            _, b64 = await self.generate_speech_audio(fallback_text)
            return SoloUtteranceResult(
                user_transcription=user_text,
                intent="unclear",
                bot_speech_text=fallback_text,
                bot_audio_base64=b64,
                session_completed=False,
                current_score=self.score,
            )


class SoloPracticeService:
    """Manages active solo practice sessions across connections."""

    def __init__(self):
        self._sessions: Dict[str, SoloPracticeSession] = {}

    def create_session(self, req: SoloSessionStartRequest) -> SoloPracticeSession:
        sid = req.session_id or f"solo_{uuid.uuid4().hex[:8]}"
        session = SoloPracticeSession(
            session_id=sid,
            quiz_title=req.quiz_title or "Luyện Tập Solo",
            questions=req.questions or DEFAULT_PRACTICE_QUESTIONS,
            voice=req.voice or "Minh Quân",
        )
        self._sessions[sid] = session
        logger.info("Solo Practice Session created: %s (%d questions)", sid, len(session.questions))
        return session

    def get_session(self, session_id: str) -> Optional[SoloPracticeSession]:
        return self._sessions.get(session_id)


solo_practice_service = SoloPracticeService()
