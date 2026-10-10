# Velix Studio 2.0 (2026 Modernized Stack)
High-definition automated educational video and narration studio powered by **DeepSeek LLM** and **ElevenLabs TTS**.

---

## 🌟 What's New vs Legacy Architecture

| Feature | Legacy Prototype (2024) | Velix Studio 2.0 (2026) |
|---|---|---|
| **Frontend** | Streamlit Python script | **Next.js 14 App Router** (TypeScript, Tailwind CSS, Lucide icons) |
| **Backend** | Synchronous Streamlit main thread | **FastAPI** asynchronous REST API with background task orchestration |
| **LLM Engine** | OpenAI `gpt-3.5-turbo` / `gpt-4-turbo` with brittle string parsing | **DeepSeek API** (`deepseek-chat`) with structured JSON schema outputs |
| **Voice / TTS** | OpenAI `tts-1` (`alloy`, `echo`, etc.) | **ElevenLabs Voice AI** (`eleven_multilingual_v2`) with in-browser previews |
| **Video Rendering** | Headless LibreOffice + Poppler + MoviePy 1.0 | **Dual engines: Native PIL 1920x1080 High-DPI Slides + 3Blue1Brown-style Manim animation, assembled with FFmpeg** |
| **Audio-Video Sync** | Hardcoded 6-second slide clips (desync bug) | **100% exact duration alignment** matched to milliseconds of spoken voiceover |
| **Curriculum Input** | Rigid Google search scraping (CAPTHCA failure) | Pre-loaded NCERT catalogue (Classes 6-12), PDF Upload & Custom Topics |

### Rendering Engines

Velix Studio 2.0 ships with two selectable rendering engines (choose in the Slide Deck step of the UI, or via the `renderer` field of `POST /api/generate/render`):

* **PIL HD Slides** (`slides`, default) — static 1920x1080 slide cards.
Fastest option, best for quick turnaround.
* **Manim 3b1b Animation** (`manim`) — animated scenes with kinetic typography, cascading bullet reveals, and typeset formulas.
Rendering is slower, so use it when you want a polished, motion-rich lecture.
Requires the Python `manim` package (`pip install manim`); optional LaTeX (`basictex` / MacTeX) enables full MathTex formula typesetting.

---

## 🚀 Architecture

```mermaid
flowchart LR
    A[Next.js 14 Frontend<br/>Port 3001] -->|Rewrites /api & /storage| B[FastAPI Backend<br/>Port 8001]
    B -->|Outline & Slide Scripts| C[DeepSeek LLM]
    B -->|Natural Voice Synthesis| D[ElevenLabs Voice API]
    B -->|Slide Graphics 1080p| E[PIL High-DPI Canvas]
    B -->|Animated Scenes 1080p| H[Manim 3b1b Engine]
    B -->|Audio + Slide Video Assembly| F[FFmpeg Engine]
    B -->|Static Output Streams| G[Storage / Final MP4]
```

---

## 🛠️ Quick Start

### 1. Backend (FastAPI)
The backend is located in [`backend/`](file:///Users/hrushik/Desktop/12_projects/velix/backend) and runs on port `8001`:

```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. Frontend (Next.js)
The frontend is located in [`frontend/`](file:///Users/hrushik/Desktop/12_projects/velix/frontend) and runs on port `3001`:

```bash
cd frontend
npm run dev -- -p 3001
```

Open your browser at **http://localhost:3001**.
