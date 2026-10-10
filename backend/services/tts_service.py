import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from backend.config import ELEVENLABS_API_KEY, ELEVENLABS_BASE_URL

CURATED_VOICES = [
    {
        "voice_id": "Xb7hH8MSUJpSbSDYk0k2",
        "name": "Alice - Educator",
        "accent": "British",
        "gender": "Female",
        "description": "Clear, engaging, articulate teacher voice ideal for lessons and tutorials.",
        "category": "Educational",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/Xb7hH8MSUJpSbSDYk0k2/alice.mp3"
    },
    {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George - Storyteller",
        "accent": "British",
        "gender": "Male",
        "description": "Warm, captivating, deep narrative voice perfect for history and literature.",
        "category": "Narrative",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/JBFqnCBsd6RMkjVDRZzb/george.mp3"
    },
    {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah - Confident",
        "accent": "American",
        "gender": "Female",
        "description": "Mature, calm, reassuring academic presentation voice.",
        "category": "Academic",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/EXAVITQu4vr4xnSDxMaL/sarah.mp3"
    },
    {
        "voice_id": "IKne3meq5aSn9XLyUdCD",
        "name": "Charlie - Energetic",
        "accent": "Australian",
        "gender": "Male",
        "description": "Dynamic, upbeat, friendly mentor tone for STEM and modern topics.",
        "category": "Conversational",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/IKne3meq5aSn9XLyUdCD/charlie.mp3"
    },
    {
        "voice_id": "SAz9YHcvj6GT2YYXdXww",
        "name": "River - Neutral",
        "accent": "American",
        "gender": "Non-binary",
        "description": "Relaxed, balanced, crystal clear informative tone.",
        "category": "Informative",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/SAz9YHcvj6GT2YYXdXww/river.mp3"
    },
    {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel - Natural",
        "accent": "American",
        "gender": "Female",
        "description": "Calm, gentle, universally understood textbook voice.",
        "category": "Standard",
        "preview_url": "https://storage.googleapis.com/eleven-public-prod/previews/voices/21m00Tcm4TlvDq8ikWAM/rachel.mp3"
    }
]

class TTSService:
    def __init__(self, api_key: str = ELEVENLABS_API_KEY):
        self.api_key = api_key
        self.base_url = ELEVENLABS_BASE_URL

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Fetch available voices from ElevenLabs, falling back to curated list if needed."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                if res.status_code == 200:
                    data = res.json()
                    voices = []
                    for v in data.get("voices", []):
                        labels = v.get("labels", {})
                        voices.append({
                            "voice_id": v.get("voice_id"),
                            "name": v.get("name"),
                            "accent": labels.get("accent", "Neutral"),
                            "gender": labels.get("gender", "Neutral"),
                            "description": labels.get("description", v.get("category", "General")),
                            "category": v.get("category", "Generated"),
                            "preview_url": v.get("preview_url")
                        })
                    return voices if voices else CURATED_VOICES
        except Exception as e:
            print(f"[TTSService] Failed to fetch voices from ElevenLabs: {e}")
        return CURATED_VOICES

    async def synthesize(
        self,
        text: str,
        output_file: Path,
        voice_id: str = "Xb7hH8MSUJpSbSDYk0k2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        model_id: str = "eleven_multilingual_v2"
    ) -> float:
        """
        Synthesizes speech using ElevenLabs and writes to output_file.
        Returns audio duration in seconds.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        url = f"{self.base_url}/text-to-speech/{voice_id}"

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "use_speaker_boost": True
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                }
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"ElevenLabs TTS failed [{response.status_code}]: {response.text}"
                )

            with open(output_file, "wb") as f:
                f.write(response.content)

        return self.get_audio_duration(output_file)

    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        """Determines the duration of an audio file in seconds via ffprobe or ffmpeg."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            duration = float(res.stdout.strip())
            return duration
        except Exception:
            # Fallback estimation: average 150 words per minute ~ 2.5 words/sec, min 3 seconds
            try:
                size = os.path.getsize(audio_path)
                # 128 kbps mp3 = 16000 bytes per second
                est = max(3.0, size / 16000.0)
                return round(est, 2)
            except Exception:
                return 5.0

tts_service = TTSService()
