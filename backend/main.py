import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import STORAGE_DIR
from backend.routers import generation, voices, ncert

app = FastAPI(
    title="Velix AI Video Studio API",
    description="Next-generation automated textbook-to-video narration platform powered by DeepSeek and ElevenLabs",
    version="2.0.0"
)

# CORS setup for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage directory for static access to generated slides, audios, and videos
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Include routers
app.include_router(ncert.router)
app.include_router(voices.router)
app.include_router(generation.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Velix Studio Backend",
        "version": "2.0.0",
        "models": {
            "llm": "DeepSeek Chat (V3/Flash)",
            "tts": "ElevenLabs Multilingual V2"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
