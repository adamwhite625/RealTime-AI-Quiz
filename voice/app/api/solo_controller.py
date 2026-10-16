import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.schemas.solo_dto import (
    SoloSessionStartRequest,
    SoloSessionStateResponse,
    SoloUtteranceResult,
)
from app.services.solo_practice_service import solo_practice_service
from app.services.voice_answer_service import voice_answer_service
from app.utils.vad import BargeInDetector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/solo", tags=["Solo Voice Practice Bot (Scenario 3)"])


@router.post("/start", response_model=SoloSessionStateResponse)
async def start_solo_session(request: SoloSessionStartRequest):
    """Initializes a new Solo 1-on-1 Practice Game Session."""
    session = solo_practice_service.create_session(request)
    curr_q = session.get_current_question()
    return SoloSessionStateResponse(
        session_id=session.session_id,
        quiz_title=session.quiz_title,
        current_index=session.current_index,
        total_questions=len(session.questions),
        score=session.score,
        state=session.state,
        current_question=curr_q,
        voice=session.voice,
    )


@router.get("/{session_id}", response_model=SoloSessionStateResponse)
async def get_solo_session(session_id: str):
    """Retrieves current state of a practice session."""
    session = solo_practice_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return SoloSessionStateResponse(
        session_id=session.session_id,
        quiz_title=session.quiz_title,
        current_index=session.current_index,
        total_questions=len(session.questions),
        score=session.score,
        state=session.state,
        current_question=session.get_current_question(),
        voice=session.voice,
    )


@router.post("/{session_id}/interact", response_model=SoloUtteranceResult)
async def interact_with_bot(session_id: str, payload: dict):
    """
    REST endpoint to interact with the Solo Voicebot.
    Accepts text or audio_base64:
    {"text": "Tôi chọn đáp án A"} or {"text": "Gợi ý cho tôi đi"} or {"audio_base64": "..."}
    """
    session = solo_practice_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    user_text = payload.get("text", "")
    if not user_text and "audio_base64" in payload:
        from app.integrations.sherpa_stt import stt_client
        transcribed, _ = await stt_client.transcribe_base64(payload["audio_base64"])
        user_text = transcribed

    if not user_text:
        raise HTTPException(status_code=400, detail="No text or audio provided.")

    return await session.handle_user_speech(user_text)


@router.websocket("/ws")
async def solo_voicebot_websocket(websocket: WebSocket):
    """
    Full-duplex real-time WebSocket connection for 1-on-1 Practice with VAD & Barge-in.
    
    Client events:
    - {"type": "START", "sessionId": "...", "voice": "Minh Quân"}
    - Binary audio chunks (player talking)
    - {"type": "STOP_SPEAKING"} -> triggers transcription & AI Tutor feedback
    - {"type": "READ_QUESTION"} -> triggers bot to read current question
    
    Server events:
    - {"event": "bot_speech_start", "text": "..."}
    - Binary audio chunks (VieNeu-TTS audio)
    - {"event": "bot_speech_end"}
    - {"event": "barge_in", "message": "Bot playback interrupted"}
    - {"event": "utterance_result", "data": {...}}
    """
    await websocket.accept()
    logger.info("Solo Practice WebSocket connected")

    session = None
    audio_buffer = bytearray()
    stream_task: Optional[asyncio.Task] = None
    is_bot_speaking = False

    def on_barge_in_triggered():
        nonlocal is_bot_speaking, stream_task
        if is_bot_speaking and stream_task and not stream_task.done():
            logger.info("Barge-in: Cancelling bot audio playback task!")
            stream_task.cancel()
            is_bot_speaking = False

    barge_in_detector = BargeInDetector(
        dbfs_threshold=-38.0,
        min_speech_frames=2,
        on_barge_in=on_barge_in_triggered,
    )

    async def stream_audio_to_client(wav_bytes: bytes, text: str, event_type: str = "bot_speech"):
        nonlocal is_bot_speaking
        try:
            is_bot_speaking = True
            barge_in_detector.reset()
            await websocket.send_json({
                "event": f"{event_type}_start",
                "text": text,
            })

            # Stream audio in 4KB chunks
            chunk_size = 4096
            for i in range(0, len(wav_bytes), chunk_size):
                if not is_bot_speaking:
                    break
                chunk = wav_bytes[i:i + chunk_size]
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.01)

            if is_bot_speaking:
                await websocket.send_json({"event": f"{event_type}_end"})
        except asyncio.CancelledError:
            logger.info("Audio streaming cancelled due to barge-in")
            await websocket.send_json({"event": "barge_in", "message": "Audio interrupted by user speech"})
        except Exception as exc:
            logger.error("Error streaming audio to client: %s", exc)
        finally:
            is_bot_speaking = False

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type == "START":
                        start_req = SoloSessionStartRequest(
                            session_id=data.get("sessionId"),
                            quiz_title=data.get("quizTitle", "Luyện Tập Solo"),
                            voice=data.get("voice", "Minh Quân"),
                        )
                        session = solo_practice_service.create_session(start_req)
                        curr_q = session.get_current_question()
                        
                        await websocket.send_json({
                            "event": "session_started",
                            "sessionId": session.session_id,
                            "quizTitle": session.quiz_title,
                            "totalQuestions": len(session.questions),
                        })

                        # Automatically read Question 1
                        if curr_q:
                            speech_text = session.format_question_speech(curr_q)
                            wav, _ = await session.generate_speech_audio(speech_text)
                            stream_task = asyncio.create_task(stream_audio_to_client(wav, speech_text, "question"))

                    elif msg_type == "READ_QUESTION":
                        if session:
                            curr_q = session.get_current_question()
                            if curr_q:
                                speech_text = session.format_question_speech(curr_q)
                                wav, _ = await session.generate_speech_audio(speech_text)
                                stream_task = asyncio.create_task(stream_audio_to_client(wav, speech_text, "question"))

                    elif msg_type == "STOP_SPEAKING":
                        # User finished speaking -> transcribe & evaluate
                        if len(audio_buffer) > 0 and session:
                            transcribe_res = await voice_answer_service.transcribe_audio(bytes(audio_buffer))
                            user_text = transcribe_res.get("text", "")
                            audio_buffer.clear()

                            if user_text:
                                result = await session.handle_user_speech(user_text)
                                await websocket.send_json({
                                    "event": "utterance_result",
                                    "data": result.model_dump(),
                                })

                                # Stream bot's reply audio
                                if result.bot_speech_text:
                                    wav, _ = await session.generate_speech_audio(result.bot_speech_text)
                                    stream_task = asyncio.create_task(stream_audio_to_client(wav, result.bot_speech_text, "bot_reply"))

                except Exception as exc:
                    logger.error("WebSocket message handling error: %s", exc)
                    await websocket.send_json({"event": "error", "message": str(exc)})

            elif "bytes" in message:
                raw_chunk = message["bytes"]
                audio_buffer.extend(raw_chunk)

                # Check for Barge-in during bot speech
                if is_bot_speaking and len(raw_chunk) >= 640:
                    try:
                        import numpy as np
                        frame = np.frombuffer(raw_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                        barge_in_detector.process_frame(frame)
                    except Exception:
                        pass

    except (WebSocketDisconnect, RuntimeError):
        logger.info("Solo Practice WebSocket disconnected cleanly")
        if stream_task and not stream_task.done():
            stream_task.cancel()
    except Exception as exc:
        logger.error("Solo Practice WebSocket unexpected error: %s", exc)
