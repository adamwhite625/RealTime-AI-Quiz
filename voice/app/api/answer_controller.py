import json
import logging
from typing import Optional, List
from fastapi import APIRouter, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.schemas.answer_dto import (
    MatchAnswerRequest,
    MatchAnswerResponse,
    OptionInfo,
    TranscribeResponse,
    VoiceAnswerSubmitRequest,
)
from app.services.voice_answer_service import voice_answer_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Recognition & Answer Matching"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(file: UploadFile = File(...)):
    """
    Transcribe an uploaded audio file (WAV, MP3, WebM, OGG, etc.) to Vietnamese text.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file provided.")
        
        result = await voice_answer_service.transcribe_audio(content)
        return TranscribeResponse(**result)
    except Exception as exc:
        logger.error("Audio transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/answer/match", response_model=MatchAnswerResponse)
async def match_voice_answer(request: MatchAnswerRequest):
    """
    Match audio or transcribed speech against a set of question options.
    Returns matched option ID, label (A/B/C/D), match confidence, and match type.
    """
    try:
        return await voice_answer_service.match_voice_answer(request)
    except Exception as exc:
        logger.error("Answer matching failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/answer/submit", response_model=MatchAnswerResponse)
async def submit_voice_answer(
    request: VoiceAnswerSubmitRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Full pipeline: Decodes player's spoken answer -> Matches choice -> Submits to Spring Boot session.
    """
    try:
        token = authorization.replace("Bearer ", "") if authorization else None
        return await voice_answer_service.process_and_submit(request, auth_token=token)
    except Exception as exc:
        logger.error("Voice answer submit failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.websocket("/ws/answer")
async def websocket_voice_answer(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for players answering trivia questions via voice.
    
    Protocol:
    1. Send INIT_QUESTION with questionId and options list.
    2. Stream binary audio chunks (PCM16 or WebM chunks).
    3. Send STOP_ANSWER to trigger transcription, matching, and score submission.
    """
    await websocket.accept()
    logger.info("WebSocket connection opened for voice answer")

    session_id: Optional[str] = None
    player_id: Optional[int] = None
    question_id: Optional[int] = None
    options: List[OptionInfo] = []
    audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                try:
                    payload = json.loads(message["text"])
                    msg_type = payload.get("type")

                    if msg_type == "INIT_QUESTION":
                        session_id = payload.get("sessionId")
                        player_id = payload.get("playerId")
                        question_id = payload.get("questionId")
                        raw_opts = payload.get("options", [])
                        options = [OptionInfo(**o) for o in raw_opts]
                        audio_buffer.clear()
                        await websocket.send_json({
                            "type": "INITIALIZED",
                            "questionId": question_id,
                            "optionsCount": len(options),
                        })

                    elif msg_type == "STOP_ANSWER":
                        # Process accumulated audio
                        if len(audio_buffer) == 0:
                            await websocket.send_json({
                                "type": "ERROR",
                                "message": "No audio received before STOP_ANSWER",
                            })
                            continue

                        # Transcribe audio buffer directly
                        transcribe_res = await voice_answer_service.transcribe_audio(bytes(audio_buffer))
                        transcribed_text = transcribe_res.get("text", "")

                        match_res = await voice_answer_service.match_voice_answer(
                            MatchAnswerRequest(
                                question_id=question_id,
                                options=options,
                                transcribed_text=transcribed_text,
                            )
                        )

                        # Submit to Spring Boot if session & player are set
                        if session_id and player_id and match_res.is_matched and match_res.matched_option_id:
                            sub_res = await voice_answer_service.submit_to_spring_backend(
                                session_id=session_id,
                                player_id=player_id,
                                question_id=question_id,
                                selected_option_id=match_res.matched_option_id,
                            )
                            match_res.submission_result = sub_res

                        await websocket.send_json({
                            "type": "ANSWER_RESULT",
                            "result": match_res.model_dump(),
                        })
                        audio_buffer.clear()

                except Exception as exc:
                    logger.error("WebSocket message processing error: %s", exc)
                    await websocket.send_json({"type": "ERROR", "message": str(exc)})

            elif "bytes" in message:
                audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by player")
    except Exception as exc:
        logger.error("WebSocket unexpected error: %s", exc)
