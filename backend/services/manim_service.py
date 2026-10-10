"""
Manim Renderer Service for Velix Studio 2.0

Generates animated 3Blue1Brown-style educational videos using the Manim Community
library. Each slide is rendered as an animated Scene with kinetic typography,
color-coded bullet reveals, and smooth transitions — then combined with
ElevenLabs TTS audio.
"""
import re
import logging
import subprocess
import shutil
import textwrap
from pathlib import Path
from typing import List, Dict, Any
from backend.config import FFMPEG_PATH

# ── Manim imports (deferred so the module can be imported even if manim has
#    import-time side-effects) ─────────────────────────────────────────────────

def manim_available() -> bool:
    """Check whether the manim package is importable on this server."""
    import importlib.util
    return importlib.util.find_spec("manim") is not None


def _fit_lines(text: str, width: int, max_lines: int) -> str:
    """Wrap text to roughly `width` characters, capped at `max_lines`
    with a trailing ellipsis so MText objects never overflow the frame."""
    lines = textwrap.wrap(" ".join(text.split()), width=width) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(",;:. ")
        if len(lines[-1]) > width - 2:
            lines[-1] = lines[-1][: width - 2].rstrip()
        lines[-1] += " …"
    return "\n".join(lines)


_SUPERSCRIPTS = str.maketrans("0123456789-+()=n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁼⁽⁾ⁿ")


def _prettify_formula(text: str) -> str:
    """Render ASCII math gracefully when a LaTeX toolchain is unavailable
    (e.g. 'a^2 + b^2 = c^2' -> 'a² + b² = c²')."""
    text = text.replace(" * ", " × ")
    return re.sub(
        r"\^([\w+\-()=]+)",
        lambda m: m.group(1).translate(_SUPERSCRIPTS),
        text,
    )

# ── Theme palettes ────────────────────────────────────────────────────────────

MANIM_THEMES = {
    "modern-dark": {
        "bg":           "#0b0f19",
        "title":        "#38bdf8",   # cyan-400
        "subtitle":     "#94a3b8",   # slate-400
        "bullet_num":   "#0ea5e9",   # cyan-500
        "bullet_text":  "#e2e8f0",   # slate-200
        "takeaway_bg":  "#0c4a60",
        "takeaway_border": "#06b6d4",
        "takeaway_text":"#ffffff",
        "brand":        "#64748b",
        "accent":       "#38bdf8",
        "divider":      "#334155",
    },
    "emerald": {
        "bg":           "#061a15",
        "title":        "#34d399",
        "subtitle":     "#a7f3d0",
        "bullet_num":   "#10b981",
        "bullet_text":  "#ecfdf5",
        "takeaway_bg":  "#064e3b",
        "takeaway_border": "#10b981",
        "takeaway_text":"#ffffff",
        "brand":        "#6ee7b7",
        "accent":       "#34d399",
        "divider":      "#22543a",
    },
    "amber": {
        "bg":           "#1a130b",
        "title":        "#fbbf24",
        "subtitle":     "#fde68a",
        "bullet_num":   "#f59e0b",
        "bullet_text":  "#fffbeb",
        "takeaway_bg":  "#78350f",
        "takeaway_border": "#f59e0b",
        "takeaway_text":"#ffffff",
        "brand":        "#fcd34d",
        "accent":       "#fbbf24",
        "divider":      "#4d381a",
    },
}


class ManimRendererService:
    """
    Renders each slide as a self-contained Manim Scene video with smooth
    Write / FadeIn / bullet-cascade animations, then stitches them together
    with per-slide TTS audio using FFmpeg.
    """

    def render_slide_video(
        self,
        topic: str,
        grade: str,
        slide: Dict[str, Any],
        slide_idx: int,
        total_slides: int,
        audio_path: Path,
        audio_duration: float,
        output_video_path: Path,
        theme: str = "modern-dark",
    ) -> Path:
        """
        1. Generate a Manim animation for one slide (headless, 1080p).
        2. Mux the animation video with the TTS audio, stretching/trimming
           the visual to match the audio length exactly.
        Returns the path to the final muxed clip.
        """
        import manim
        from manim import (
            config as mconfig,
            Scene, Text, VGroup,
            Write, FadeIn, Create,
            RoundedRectangle, Line,
            DOWN, RIGHT, LEFT, UP, ORIGIN,
            MathTex,
        )

        # Keep backend logs readable: manim is extremely chatty at INFO
        logging.getLogger("manim").setLevel(logging.WARNING)

        palette = MANIM_THEMES.get(theme, MANIM_THEMES["modern-dark"])
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        # ── Manim config ────────────────────────────────────────────────
        mconfig.pixel_width = 1920
        mconfig.pixel_height = 1080
        mconfig.frame_rate = 30
        mconfig.background_color = palette["bg"]
        mconfig.disable_caching = True
        manim_media_dir = output_video_path.parent / f"manim_media_{slide_idx}"
        mconfig.media_dir = str(manim_media_dir)

        # ── Build the Scene dynamically ────────────────────────────────
        _slide = slide
        _palette = palette
        _topic = topic
        _grade = grade
        _slide_idx = slide_idx
        _total = total_slides
        _audio_dur = audio_duration

        class SlideScene(Scene):
            def construct(self):
                p = _palette
                s = _slide
                safe_font = "sans-serif"

                # Frame geometry (manim default: 14.22 x 8.0 units at 1080p)
                frame_w = self.camera.frame_width
                frame_h = self.camera.frame_height
                margin_x = 0.9
                max_text_w = frame_w - 2 * margin_x

                # Decide animation pacing based on audio duration
                anim_budget = max(_audio_dur - 1.0, 3.0)  # leave 1s tail
                n_anims = 2 + len(s.get("bullet_points", [])) + (1 if s.get("key_takeaway") else 0)
                per_anim = max(anim_budget / n_anims, 0.4)

                # --- Header badge ---
                badge_text = f"VELIX  ·  {_grade.upper()}  ·  {_topic.upper()[:40]}"
                badge = Text(badge_text, font_size=20, color=p["accent"], font=safe_font)
                badge.to_corner(UP + LEFT, buff=0.6)
                self.add(badge)

                counter = Text(
                    f"SLIDE {_slide_idx+1:02d} / {_total:02d}",
                    font_size=20, color=p["accent"], font=safe_font
                )
                counter.to_corner(UP + RIGHT, buff=0.6)
                self.add(counter)

                # --- Title ---
                title = Text(
                    s.get("title", ""),
                    font_size=52,
                    color=p["title"],
                    font=safe_font,
                    weight="BOLD",
                )
                if title.width > max_text_w:
                    title.scale_to_fit_width(max_text_w)
                title.move_to(UP * 2.2)

                # --- Subtitle ---
                subtitle_text = s.get("subtitle", "")
                subtitle = Text(
                    subtitle_text,
                    font_size=28,
                    color=p["subtitle"],
                    font=safe_font,
                )
                if subtitle.width > max_text_w:
                    subtitle.scale_to_fit_width(max_text_w)
                subtitle.next_to(title, DOWN, buff=0.35)

                # --- Divider ---
                divider = Line(
                    start=LEFT * (max_text_w / 2),
                    end=RIGHT * (max_text_w / 2),
                    color=p["divider"],
                    stroke_width=2,
                )
                divider.next_to(subtitle, DOWN, buff=0.4)

                # Animate title + subtitle
                self.play(Write(title), run_time=min(per_anim, 1.2))
                self.play(FadeIn(subtitle), Create(divider), run_time=min(per_anim, 0.8))

                # --- Key takeaway box geometry (defines the bullet band below) ---
                takeaway = s.get("key_takeaway", "")
                box_w = max_text_w
                box_top_y = -frame_h / 2 + 0.75  # footer-safe default
                if takeaway:
                    box = RoundedRectangle(
                        corner_radius=0.2,
                        width=box_w,
                        height=1.2,
                        color=p["takeaway_border"],
                        fill_color=p["takeaway_bg"],
                        fill_opacity=0.85,
                        stroke_width=2,
                    )
                    box.to_edge(DOWN, buff=0.7)
                    box_top_y = box.get_top()[1]

                # --- Bullet points ---
                bullets = s.get("bullet_points", [])
                bullet_group = VGroup()
                for bi, bp in enumerate(bullets[:4]):
                    num = Text(
                        str(bi + 1),
                        font_size=24,
                        color=p["bullet_num"],
                        font=safe_font,
                        weight="BOLD",
                    )
                    body = Text(
                        _fit_lines(_prettify_formula(bp), 55, 2),
                        font_size=24,
                        color=p["bullet_text"],
                        font=safe_font,
                        line_spacing=1.1,
                    )
                    row = VGroup(num, body).arrange(RIGHT, buff=0.35, aligned_edge=UP)
                    bullet_group.add(row)

                if len(bullet_group) > 0:
                    bullet_group.arrange(DOWN, buff=0.45, aligned_edge=LEFT)

                    # Fit the cascade into the band between divider and takeaway
                    band_top = divider.get_bottom()[1] - 0.35
                    band_bottom = box_top_y + 0.3
                    band_h = max(band_top - band_bottom, 1.0)
                    if bullet_group.height > band_h:
                        bullet_group.scale_to_fit_height(band_h)
                    bullet_group.move_to([0, (band_top + band_bottom) / 2, 0])

                    for row in bullet_group:
                        self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=min(per_anim, 0.7))

                # --- Key Takeaway box ---
                if takeaway:
                    label = Text(
                        "💡 KEY TAKEAWAY",
                        font_size=18,
                        color=p["accent"],
                        font=safe_font,
                        weight="BOLD",
                    )

                    # MathTex only for short ASCII formulas; prose falls back to Text
                    tk_text = None
                    looks_mathy = (
                        takeaway.isascii()
                        and any(c in takeaway for c in ["=", "^", "+"])
                        and len(takeaway.split()) <= 8
                    )
                    if looks_mathy:
                        try:
                            tk_text = MathTex(takeaway, font_size=30, color=p["takeaway_text"])
                        except Exception:
                            tk_text = None
                    if tk_text is None:
                        tk_text = Text(
                            _fit_lines(_prettify_formula(takeaway), 60, 2),
                            font_size=22,
                            color=p["takeaway_text"],
                            font=safe_font,
                        )
                    if tk_text.width > box_w - 1.2:
                        tk_text.scale_to_fit_width(box_w - 1.2)

                    content_group = VGroup(label, tk_text).arrange(DOWN, buff=0.15)
                    if content_group.height > box.height - 0.35:
                        content_group.scale_to_fit_height(box.height - 0.35)
                    content_group.move_to(box.get_center())

                    self.play(
                        FadeIn(box),
                        FadeIn(content_group),
                        run_time=min(per_anim, 0.8),
                    )

                # --- Brand footer ---
                brand = Text(
                    "Powered by Velix Studio · Manim Engine",
                    font_size=16,
                    color=p["brand"],
                    font=safe_font,
                )
                brand.to_corner(DOWN + RIGHT, buff=0.35)
                self.add(brand)

                # Fill remaining time with a hold
                remaining = max(_audio_dur - self.renderer.time, 0.5)
                self.wait(remaining)

        # ── Render the scene ────────────────────────────────────────────
        scene = SlideScene()
        scene.render()
        raw_video = Path(scene.renderer.file_writer.movie_file_path)

        # ── Mux: replace audio, match duration to TTS ───────────────────
        muxed_path = output_video_path
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", str(raw_video),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            str(muxed_path),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg mux failed: {result.stderr[-300:]}")

        # Clean up manim's intermediate media directory
        try:
            shutil.rmtree(manim_media_dir, ignore_errors=True)
        except Exception:
            pass

        return muxed_path

    @staticmethod
    def render_thumbnail(
        raw_manim_video: Path,
        output_png: Path,
    ):
        """Extract a single frame from a Manim video as a thumbnail PNG."""
        output_png.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", "2",
            "-i", str(raw_manim_video),
            "-frames:v", "1",
            "-q:v", "2",
            str(output_png),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def concatenate_videos(video_paths: List[Path], output_path: Path):
        """Combine all slide clip videos into one final presentation."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        concat_list = output_path.parent / "concat_list.txt"
        with open(concat_list, "w") as f:
            for vp in video_paths:
                f.write(f"file '{vp.resolve()}'\n")

        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg concat failed: {result.stderr[-300:]}")


manim_renderer = ManimRendererService()
