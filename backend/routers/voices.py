from fastapi import APIRouter
from backend.services.tts_service import tts_service

router = APIRouter(prefix="/api/voices", tags=["voices"])

@router.get("")
async def get_voices():
    """Retrieve available ElevenLabs voices with metadata and audio previews."""
    voices = await tts_service.get_voices()
    return {"voices": voices}
