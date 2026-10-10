import os
import textwrap
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

class SlideRenderer:
    def __init__(self):
        self.width = 1920
        self.height = 1080
        self._load_fonts()

    def _load_fonts(self):
        # Prefer system Arial / Helvetica
        bold_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf"
        ]
        regular_paths = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf"
        ]

        self.font_bold_file = None
        for p in bold_paths:
            if os.path.exists(p):
                self.font_bold_file = p
                break

        self.font_reg_file = None
        for p in regular_paths:
            if os.path.exists(p):
                self.font_reg_file = p
                break

    def get_font(self, size: int, bold: bool = False) -> ImageFont.ImageFont:
        font_file = self.font_bold_file if bold else self.font_reg_file
        if font_file:
            try:
                return ImageFont.truetype(font_file, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def render_slide(
        self,
        topic: str,
        grade: str,
        slide: Dict[str, Any],
        slide_idx: int,
        total_slides: int,
        theme: str = "modern-dark"
    ) -> Image.Image:
        """Renders a single 1920x1080 slide image."""
        img = Image.new("RGBA", (self.width, self.height), color=(15, 23, 42, 255))
        draw = ImageDraw.Draw(img)

        # Theme color palettes
        themes = {
            "modern-dark": {
                "bg_top": (11, 15, 25),
                "bg_bottom": (19, 27, 46),
                "accent": (56, 189, 248),      # Cyan 400
                "accent_rgb": "#38bdf8",
                "accent_glow": (56, 189, 248, 40),
                "card_bg": (30, 41, 59, 230),   # Slate 800
                "card_border": (51, 65, 85, 255),
                "text_primary": (248, 250, 252),
                "text_secondary": (148, 163, 184),
                "badge_bg": (14, 116, 144, 255),
                "callout_bg": (12, 74, 96, 220),
                "callout_border": (6, 182, 212, 255),
            },
            "emerald": {
                "bg_top": (6, 26, 21),
                "bg_bottom": (13, 43, 35),
                "accent": (52, 211, 153),      # Emerald 400
                "accent_rgb": "#34d399",
                "accent_glow": (52, 211, 153, 40),
                "card_bg": (17, 54, 44, 230),
                "card_border": (34, 84, 70, 255),
                "text_primary": (240, 253, 244),
                "text_secondary": (167, 243, 208),
                "badge_bg": (5, 150, 105, 255),
                "callout_bg": (6, 78, 59, 220),
                "callout_border": (16, 185, 129, 255),
            },
            "amber": {
                "bg_top": (26, 19, 11),
                "bg_bottom": (41, 30, 18),
                "accent": (251, 191, 36),      # Amber 400
                "accent_rgb": "#fbbf24",
                "accent_glow": (251, 191, 36, 40),
                "card_bg": (46, 35, 23, 230),
                "card_border": (77, 58, 38, 255),
                "text_primary": (255, 251, 235),
                "text_secondary": (217, 187, 150),
                "badge_bg": (217, 119, 6, 255),
                "callout_bg": (120, 53, 15, 220),
                "callout_border": (245, 158, 11, 255),
            }
        }
        palette = themes.get(theme, themes["modern-dark"])

        # Draw vertical subtle gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(palette["bg_top"][0] * (1 - ratio) + palette["bg_bottom"][0] * ratio)
            g = int(palette["bg_top"][1] * (1 - ratio) + palette["bg_bottom"][1] * ratio)
            b = int(palette["bg_top"][2] * (1 - ratio) + palette["bg_bottom"][2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, 255))

        # Ambient glow in the top-right corner
        accent_color = palette["accent"]

        # 1. Top Header Bar
        # Topic badge
        topic_text = f"VELIX  •  {grade.upper()}  •  {topic.upper()[:45]}"
        font_header = self.get_font(22, bold=True)
        draw.rounded_rectangle([80, 60, 80 + len(topic_text) * 12 + 40, 104], radius=10, fill=palette["card_bg"], outline=palette["card_border"], width=1)
        draw.text((100, 72), topic_text, fill=palette["accent"], font=font_header)

        # Slide counter pill
        counter_text = f"SLIDE {slide_idx + 1:02d} / {total_slides:02d}"
        font_counter = self.get_font(20, bold=True)
        draw.rounded_rectangle([self.width - 260, 60, self.width - 80, 104], radius=10, fill=palette["badge_bg"])
        draw.text((self.width - 235, 73), counter_text, fill=(255, 255, 255), font=font_counter)

        # 2. Slide Title & Subtitle
        title = slide.get("title", f"Slide {slide_idx + 1}")
        subtitle = slide.get("subtitle", "")

        font_title = self.get_font(52, bold=True)
        font_sub = self.get_font(28, bold=False)

        draw.text((80, 136), title, fill=palette["text_primary"], font=font_title)
        if subtitle:
            draw.text((80, 206), subtitle, fill=palette["text_secondary"], font=font_sub)

        # Accent divider line under header
        draw.line([(80, 255), (self.width - 80, 255)], fill=palette["card_border"], width=2)
        draw.line([(80, 255), (320, 255)], fill=accent_color, width=4)

        # 3. Main Content Cards (Bullet Points)
        bullet_points = slide.get("bullet_points", [])
        start_y = 285
        available_height = 570
        spacing = available_height / max(len(bullet_points), 1)

        font_bullet = self.get_font(26, bold=False)
        font_bullet_num = self.get_font(22, bold=True)

        for i, bp in enumerate(bullet_points):
            card_top = start_y + i * spacing
            card_bottom = card_top + min(spacing - 20, 130)
            card_left = 80
            card_right = self.width - 80

            # Background card
            draw.rounded_rectangle(
                [card_left, card_top, card_right, card_bottom],
                radius=14,
                fill=palette["card_bg"],
                outline=palette["card_border"],
                width=1
            )

            # Left accent pill / number badge
            badge_x = card_left + 24
            badge_y = card_top + 20
            draw.rounded_rectangle(
                [badge_x, badge_y, badge_x + 36, badge_y + 36],
                radius=8,
                fill=accent_color
            )
            draw.text((badge_x + 11, badge_y + 6), str(i + 1), fill=(15, 23, 42), font=font_bullet_num)

            # Bullet text with wrapping
            wrapped = textwrap.wrap(bp, width=88)
            text_y = card_top + 18
            for line in wrapped[:3]:
                draw.text((card_left + 80, text_y), line, fill=palette["text_primary"], font=font_bullet)
                text_y += 36

        # 4. Key Takeaway Box (Bottom)
        takeaway = slide.get("key_takeaway")
        if takeaway:
            box_top = self.height - 180
            box_bottom = self.height - 70
            draw.rounded_rectangle(
                [80, box_top, self.width - 80, box_bottom],
                radius=16,
                fill=palette["callout_bg"],
                outline=palette["callout_border"],
                width=2
            )
            
            # Key Icon / Label
            font_label = self.get_font(20, bold=True)
            font_takeaway = self.get_font(24, bold=True)
            draw.text((110, box_top + 16), "💡 KEY TAKEAWAY", fill=palette["accent"], font=font_label)
            
            takeaway_wrapped = textwrap.wrap(takeaway, width=105)
            for j, t_line in enumerate(takeaway_wrapped[:2]):
                draw.text((110, box_top + 46 + j * 30), t_line, fill=(255, 255, 255), font=font_takeaway)

        # 5. Clean Footer Brand
        font_brand = self.get_font(18, bold=False)
        draw.text((self.width - 240, self.height - 42), "Powered by Velix Studio", fill=palette["text_secondary"], font=font_brand)

        return img.convert("RGB")

    def save_slide_image(
        self,
        topic: str,
        grade: str,
        slide: Dict[str, Any],
        slide_idx: int,
        total_slides: int,
        output_path: Path,
        theme: str = "modern-dark"
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img = self.render_slide(topic, grade, slide, slide_idx, total_slides, theme)
        img.save(str(output_path), "PNG", quality=95)

    @staticmethod
    def render_slide_video(
        image_path: Path,
        audio_path: Path,
        duration: float,
        output_video_path: Path,
        ffmpeg_bin: str = "/opt/homebrew/bin/ffmpeg"
    ):
        """
        Generates an MP4 video clip from a slide image and audio file, perfectly synced to the audio duration.
        """
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        # Pad duration slightly by 0.5s to prevent audio cutoffs
        total_dur = max(duration, 2.0)

        cmd = [
            ffmpeg_bin,
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(total_dur),
            str(output_video_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg slide render failed: {result.stderr}")

    @staticmethod
    def concatenate_videos(
        video_paths: List[Path],
        output_path: Path,
        ffmpeg_bin: str = "/opt/homebrew/bin/ffmpeg"
    ):
        """
        Combines all slide video clips into one final video.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        concat_list_file = output_path.parent / "concat_list.txt"
        with open(concat_list_file, "w") as f:
            for vp in video_paths:
                f.write(f"file '{vp.resolve()}'\n")

        cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg concatenation failed: {result.stderr}")

slide_renderer = SlideRenderer()
