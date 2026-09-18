from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.core.languages import list_supported_languages, get_language_config
from app.services.intent_engine import intent_engine
from app.services.speech_service import speech_service
from app.services.problem_solver import problem_solver

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

class ProcessVoiceRequest(BaseModel):
    text: str = Field(..., description="Recognized speech text or typed command")
    language: str = Field("en", description="Language code e.g. 'en' or 'mr'")
    current_path: Optional[str] = Field(None, description="Current user route in web app")

class TrainUtteranceRequest(BaseModel):
    route_id: str = Field(..., description="Unique ID of route, e.g. 'profile', 'analytics'")
    utterance: str = Field(..., description="Voice phrase in English or Marathi")
    language: str = Field("en", description="Language of utterance ('en' or 'mr')")

class ProblemSolveRequest(BaseModel):
    query: str = Field(..., description="Problem description or question")
    language: str = Field("en", description="Language code ('en' or 'mr')")
    context: Optional[Dict[str, Any]] = None

@router.get("/languages")
async def get_languages():
    """Returns list of supported multilingual languages."""
    return {"languages": list_supported_languages()}

@router.get("/routes")
async def get_nav_routes():
    """Returns all currently registered and trainable routes with their phrases."""
    return {"routes": intent_engine.get_all_routes()}

@router.post("/process")
async def process_voice_command(payload: ProcessVoiceRequest):
    """
    Main processing endpoint:
    Classifies intent, determines page navigation, and returns multilingual voice response.
    """
    result = await intent_engine.process_voice_command(
        query=payload.text,
        lang_code=payload.language
    )
    
    # Get speech synthesis hints or cloud audio
    tts_result = await speech_service.synthesize_speech_api(
        text=result.get("response_text", ""),
        lang_code=payload.language
    )
    
    return {
        "status": "success",
        "result": result,
        "tts": tts_result
    }

@router.post("/train")
async def train_route_utterance(payload: TrainUtteranceRequest):
    """
    Dynamically trains the AI assistant with a new custom voice phrase.
    """
    res = intent_engine.train_utterance(
        route_id=payload.route_id,
        utterance=payload.utterance,
        lang_code=payload.language
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/tts")
async def synthesize_tts(text: str, language: str = "en"):
    """
    Synthesizes speech for the given text and language.
    """
    return await speech_service.synthesize_speech_api(text=text, lang_code=language)

@router.post("/stt")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Transcribes uploaded audio bytes via Cloud STT APIs (Groq / Sarvam / Krutrim).
    """
    content = await audio_file.read()
    return await speech_service.transcribe_audio_api(
        audio_bytes=content,
        filename=audio_file.filename or "audio.wav",
        lang_code=language
    )

@router.post("/problem-solve")
async def solve_problem(payload: ProblemSolveRequest):
    """
    Modular problem solver hook for future ML pipeline and Q&A integrations.
    """
    return await problem_solver.solve_or_explain(
        query=payload.query,
        lang_code=payload.language,
        context=payload.context
    )
