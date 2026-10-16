import logging
from typing import Optional, List, Dict, Any
import httpx

from app.core.settings import settings

logger = logging.getLogger(__name__)


class GeminiLLMClient:
    """
    Adapter integration for Google Gemini LLM API (gemini-3.5-flash-lite).
    Powers AI Tutor commentary, smart hints, and natural conversational dialogue.
    """
    _instance: Optional["GeminiLLMClient"] = None

    def __new__(cls) -> "GeminiLLMClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._api_key = settings.GEMINI_API_KEY
            cls._model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        return cls._instance

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 10)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_output_tokens: int = 200,
        temperature: float = 0.7,
    ) -> str:
        """
        Sends an asynchronous generateContent request to Gemini API.
        """
        if not self.is_configured:
            logger.warning("Gemini API key is not configured; skipping LLM call.")
            return ""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_output_tokens,
                "temperature": temperature,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            # Clean up any potential markdown formatting for TTS
                            text = text.replace("*", "").replace("#", "").replace("`", "")
                            return text
                else:
                    logger.error("Gemini API error (%d): %s", res.status_code, res.text)
        except Exception as exc:
            logger.error("Failed to connect to Gemini API: %s", exc)

        return ""

    async def generate_explanation(
        self,
        question: str,
        options: List[str],
        correct_answer: str,
        user_choice: Optional[str] = None,
    ) -> str:
        """Generates a concise 1-2 sentence explanation of why the answer is correct."""
        sys_prompt = (
            "Bạn là AI MC và gia sư luyện thi thân thiện của QuizMaster. "
            "Nhiệm vụ của bạn là giải thích ngắn gọn, súc tích (1-2 câu, dưới 35 từ) bằng tiếng Việt tự nhiên "
            "để bộ đọc giọng nói TTS đọc cho người chơi nghe. "
            "Tuyệt đối không dùng gạch đầu dòng, danh sách, hay ký tự markdown."
        )

        user_prompt = (
            f"Câu hỏi: {question}\n"
            f"Các lựa chọn: {', '.join(options)}\n"
            f"Đáp án đúng là: {correct_answer}\n"
            f"Người chơi đã chọn: {user_choice or 'chưa chọn'}\n\n"
            f"Hãy giải thích ngắn gọn tại sao đáp án đúng lại là {correct_answer}."
        )

        return await self.generate_text(user_prompt, system_instruction=sys_prompt, max_output_tokens=150)

    async def generate_hint(
        self,
        question: str,
        options: List[str],
        correct_answer: str,
    ) -> str:
        """Generates a clever hint without directly spoiling the correct answer."""
        sys_prompt = (
            "Bạn là AI MC của game show trắc nghiệm QuizMaster. "
            "Người chơi đang cần một manh mối hoặc gợi ý. "
            "Hãy đưa ra đúng 1 câu gợi ý ngắn gọn, dí dỏm (dưới 25 từ) để dẫn dắt tư duy của người chơi. "
            "QUAN TRỌNG NHẤT: Tuyệt đối KHÔNG được nói thẳng ra đáp án đúng hay chữ cái tương ứng."
        )

        user_prompt = (
            f"Câu hỏi: {question}\n"
            f"Các lựa chọn: {', '.join(options)}\n"
            f"Đáp án đúng (bí mật): {correct_answer}\n\n"
            f"Hãy cho người chơi một gợi ý khéo léo."
        )

        return await self.generate_text(user_prompt, system_instruction=sys_prompt, max_output_tokens=100)

    async def generate_tutor_chat(
        self,
        question: str,
        user_speech: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Handles casual queries, encouragement, or banter from the player."""
        sys_prompt = (
            "Bạn là AI MC thông minh của game QuizMaster. "
            "Người chơi đang luyện tập solo 1-1 với bạn qua giọng nói. "
            "Hãy phản hồi câu nói của người chơi một cách tự nhiên, hào hứng, ngắn gọn đúng 1-2 câu (dưới 30 từ) "
            "để khuyến khích họ tập trung vượt qua câu hỏi trắc nghiệm."
        )

        user_prompt = (
            f"Câu hỏi hiện tại đang làm: {question}\n"
            f"Người chơi vừa nói: \"{user_speech}\"\n\n"
            f"Hãy đáp lại người chơi bằng 1 câu ngắn gọn."
        )

        return await self.generate_text(user_prompt, system_instruction=sys_prompt, max_output_tokens=100)


gemini_llm = GeminiLLMClient()
