import asyncio
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.config import STORAGE_DIR
from backend.services.llm_service import llm_service
from backend.services.tts_service import tts_service
from backend.services.renderer_service import slide_renderer

router = APIRouter(prefix="/api/generate", tags=["generation"])

# In-memory job state store
JOBS: Dict[str, Dict[str, Any]] = {}

class OutlineRequest(BaseModel):
    topic: str
    grade: str
    age_group: str
    context_text: Optional[str] = None
    special_instructions: Optional[str] = None

class SlideItem(BaseModel):
    slide_number: int
    title: str
    subtitle: Optional[str] = ""
    bullet_points: List[str]
    key_takeaway: Optional[str] = ""
    narration_script: str

class SlidesRequest(BaseModel):
    topic: str
    grade: str
    age_group: str
    subheadings: List[str]
    context_text: Optional[str] = None
    tone: Optional[str] = "engaging and clear"
    special_instructions: Optional[str] = None

class RenderRequest(BaseModel):
    topic: str
    grade: str
    slides: List[SlideItem]
    voice_id: str = "Xb7hH8MSUJpSbSDYk0k2"
    theme: str = "modern-dark"
    stability: float = 0.5
    similarity_boost: float = 0.75
    renderer: Literal["slides", "manim"] = "slides"  # "slides" (PIL static) or "manim" (3b1b animated)

@router.post("/outline")
async def generate_outline_endpoint(req: OutlineRequest):
    try:
        subheadings = await llm_service.generate_outline(
            topic=req.topic,
            grade=req.grade,
            age_group=req.age_group,
            context_text=req.context_text,
            special_instructions=req.special_instructions
        )
        return {"subheadings": subheadings, "warning": llm_service.last_warning}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slides")
async def generate_slides_endpoint(req: SlidesRequest):
    try:
        slides = await llm_service.generate_slides(
            topic=req.topic,
            grade=req.grade,
            age_group=req.age_group,
            subheadings=req.subheadings,
            context_text=req.context_text,
            tone=req.tone,
            special_instructions=req.special_instructions
        )
        return {"slides": slides, "warning": llm_service.last_warning}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PIL Static Slides Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

async def run_slides_pipeline(job_id: str, req: RenderRequest):
    job_dir = STORAGE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    job = JOBS[job_id]

    try:
        total_slides = len(req.slides)
        job["status"] = "processing"
        job["current_step"] = "Designing high-definition slide graphics"
        job["progress"] = 15

        rendered_slides = []
        slide_videos = []

        # 1. Render all slide images
        for i, slide_obj in enumerate(req.slides):
            slide_dict = slide_obj.model_dump()
            img_path = job_dir / f"slide_{i}.png"
            slide_renderer.save_slide_image(
                topic=req.topic,
                grade=req.grade,
                slide=slide_dict,
                slide_idx=i,
                total_slides=total_slides,
                output_path=img_path,
                theme=req.theme
            )
            rendered_slides.append({
                "slide_idx": i,
                "title": slide_dict["title"],
                "image_url": f"/storage/{job_id}/slide_{i}.png",
                "narration_script": slide_dict["narration_script"]
            })

        job["progress"] = 30
        job["slides_info"] = rendered_slides

        # 2. Synthesize audio per slide and create video clips
        for i, slide_obj in enumerate(req.slides):
            job["current_step"] = f"Synthesizing voiceover for Slide {i+1} of {total_slides} (ElevenLabs)"
            audio_path = job_dir / f"audio_{i}.mp3"

            duration = await tts_service.synthesize(
                text=slide_obj.narration_script,
                output_file=audio_path,
                voice_id=req.voice_id,
                stability=req.stability,
                similarity_boost=req.similarity_boost
            )

            job["current_step"] = f"Rendering video clip for Slide {i+1} of {total_slides} (FFmpeg)"
            clip_video_path = job_dir / f"clip_{i}.mp4"
            img_path = job_dir / f"slide_{i}.png"

            slide_renderer.render_slide_video(
                image_path=img_path,
                audio_path=audio_path,
                duration=duration,
                output_video_path=clip_video_path
            )

            slide_videos.append(clip_video_path)
            rendered_slides[i]["audio_url"] = f"/storage/{job_id}/audio_{i}.mp3"
            rendered_slides[i]["video_url"] = f"/storage/{job_id}/clip_{i}.mp4"
            rendered_slides[i]["duration"] = duration

            progress_pct = 30 + int(55 * (i + 1) / total_slides)
            job["progress"] = progress_pct

        # 3. Concatenate
        job["current_step"] = "Finalizing and stitching presentation video..."
        final_video_path = job_dir / "final_presentation.mp4"
        slide_renderer.concatenate_videos(slide_videos, final_video_path)

        job["status"] = "completed"
        job["progress"] = 100
        job["current_step"] = "Video ready!"
        job["final_video_url"] = f"/storage/{job_id}/final_presentation.mp4"
        job["completed_at"] = time.time()

    except Exception as e:
        print(f"[SlidesPipeline] Job {job_id} failed: {e}")
        import traceback; traceback.print_exc()
        job["status"] = "failed"
        job["error"] = str(e)
        job["current_step"] = f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# Manim 3b1b Animated Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

async def run_manim_pipeline(job_id: str, req: RenderRequest):
    from backend.services.manim_service import manim_renderer

    job_dir = STORAGE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    job = JOBS[job_id]

    try:
        total_slides = len(req.slides)
        job["status"] = "processing"
        job["current_step"] = "Initializing Manim 3b1b animation engine..."
        job["progress"] = 10

        rendered_slides = []
        slide_videos = []

        for i, slide_obj in enumerate(req.slides):
            slide_dict = slide_obj.model_dump()

            # 1. Synthesize TTS audio first (Manim needs the duration)
            job["current_step"] = f"Synthesizing voiceover for Slide {i+1} of {total_slides} (ElevenLabs)"
            audio_path = job_dir / f"audio_{i}.mp3"

            duration = await tts_service.synthesize(
                text=slide_obj.narration_script,
                output_file=audio_path,
                voice_id=req.voice_id,
                stability=req.stability,
                similarity_boost=req.similarity_boost
            )

            # 2. Render Manim animation matched to audio duration
            job["current_step"] = f"Animating Slide {i+1} of {total_slides} (Manim 3b1b Engine)"
            clip_video_path = job_dir / f"clip_{i}.mp4"

            # Run Manim in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: manim_renderer.render_slide_video(
                    topic=req.topic,
                    grade=req.grade,
                    slide=slide_dict,
                    slide_idx=i,
                    total_slides=total_slides,
                    audio_path=audio_path,
                    audio_duration=duration,
                    output_video_path=clip_video_path,
                    theme=req.theme,
                )
            )

            # 3. Extract thumbnail from rendered video
            thumb_path = job_dir / f"slide_{i}.png"
            manim_renderer.render_thumbnail(clip_video_path, thumb_path)

            slide_videos.append(clip_video_path)
            rendered_slides.append({
                "slide_idx": i,
                "title": slide_dict["title"],
                "image_url": f"/storage/{job_id}/slide_{i}.png",
                "audio_url": f"/storage/{job_id}/audio_{i}.mp3",
                "video_url": f"/storage/{job_id}/clip_{i}.mp4",
                "duration": duration,
                "narration_script": slide_dict["narration_script"],
            })

            progress_pct = 10 + int(75 * (i + 1) / total_slides)
            job["progress"] = progress_pct
            job["slides_info"] = rendered_slides

        # 4. Concatenate all Manim clips into final video
        job["current_step"] = "Stitching animated presentation..."
        final_video_path = job_dir / "final_presentation.mp4"
        manim_renderer.concatenate_videos(slide_videos, final_video_path)

        job["status"] = "completed"
        job["progress"] = 100
        job["current_step"] = "Animated video ready!"
        job["final_video_url"] = f"/storage/{job_id}/final_presentation.mp4"
        job["completed_at"] = time.time()

    except Exception as e:
        print(f"[ManimPipeline] Job {job_id} failed: {e}")
        import traceback; traceback.print_exc()
        job["status"] = "failed"
        job["error"] = str(e)
        job["current_step"] = f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# Unified render endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/render")
async def start_render_job(req: RenderRequest, background_tasks: BackgroundTasks):
    from backend.services.manim_service import manim_available

    if req.renderer == "manim" and not manim_available():
        raise HTTPException(
            status_code=400,
            detail="Manim renderer requested, but the 'manim' package is not installed on the server. "
                   "Install it with: pip install manim"
        )

    job_id = f"job_{uuid.uuid4().hex[:10]}"

    renderer_label = "Manim 3b1b" if req.renderer == "manim" else "PIL HD Slides"

    JOBS[job_id] = {
        "job_id": job_id,
        "topic": req.topic,
        "grade": req.grade,
        "theme": req.theme,
        "voice_id": req.voice_id,
        "renderer": req.renderer,
        "status": "queued",
        "progress": 5,
        "current_step": f"Initializing {renderer_label} pipeline...",
        "created_at": time.time(),
        "slides_info": [],
        "final_video_url": None,
        "error": None
    }

    if req.renderer == "manim":
        background_tasks.add_task(run_manim_pipeline, job_id, req)
    else:
        background_tasks.add_task(run_slides_pipeline, job_id, req)

    return {"job_id": job_id, "status": "queued", "renderer": req.renderer}

@router.get("/job/{job_id}")
def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
