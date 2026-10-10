import json
from typing import List, Dict, Any, Optional
import httpx
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

class LLMService:
    def __init__(self):
        self.last_warning = None

    @property
    def api_key(self) -> str:
        from backend import config
        return config.DEEPSEEK_API_KEY

    @property
    def base_url(self) -> str:
        from backend import config
        return config.DEEPSEEK_BASE_URL.rstrip("/")

    async def _chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = True) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 4000
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            if resp.status_code != 200:
                raise RuntimeError(f"DeepSeek API error [{resp.status_code}]: {resp.text}")

            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_outline(
        self,
        topic: str,
        grade: str,
        age_group: str,
        context_text: Optional[str] = None,
        special_instructions: Optional[str] = None
    ) -> List[str]:
        system_prompt = f"""You are an elite educational instructional designer.
Your task is to take an educational lesson or curriculum topic and break it down into 4 to 6 logical, engaging, and sequentially structured subheadings for an animated educational video.
Target Audience: {grade} (Students aged {age_group}).

Respond with a JSON object strictly in this structure:
{{
  "subheadings": [
    "1. Introduction: <Subheading Title>",
    "2. <Subheading Title>",
    ...
  ]
}}"""

        user_content = f"Topic: {topic}\nGrade: {grade}\nAge Group: {age_group}"
        if context_text:
            clipped_context = context_text[:12000]
            user_content += f"\n\nSource Content Extract:\n{clipped_context}"
        if special_instructions:
            user_content += f"\n\nSpecial Instructions:\n{special_instructions}"

        try:
            raw_response = await self._chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ], json_mode=True)

            parsed = json.loads(raw_response)
            subheadings = parsed.get("subheadings", [])
            if subheadings:
                self.last_warning = None
                return [s.strip() for s in subheadings if s.strip()]
        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "Insufficient Balance" in err_str:
                self.last_warning = "DeepSeek API returned Insufficient Balance (402). Generated using Velix Pedagogical Engine."
            else:
                self.last_warning = f"DeepSeek unavailable ({err_str[:60]}...). Using Velix Pedagogical Engine."
            print(f"[LLMService] Outline fallback triggered due to: {e}")

        # Intelligent structured pedagogical fallback
        return [
            f"1. Foundations & Discovery of {topic}",
            f"2. Core Principles & Mechanisms of {topic}",
            f"3. Practical Applications & Real-World Phenomena",
            f"4. Experimental Observation & Key Calculations",
            f"5. Summary, Core Rules & Review Questions"
        ]

    async def generate_slides(
        self,
        topic: str,
        grade: str,
        age_group: str,
        subheadings: List[str],
        context_text: Optional[str] = None,
        tone: str = "engaging and clear",
        special_instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        system_prompt = f"""You are an award-winning STEM and Humanities educator creating interactive slide presentations with spoken audio voiceover.
You will receive a topic and a list of subheadings.
For each subheading, produce one slide with:
1. "slide_number": integer
2. "title": catchy, clear slide title (max 6 words)
3. "subtitle": explanatory concept or question (max 10 words)
4. "bullet_points": array of 3 to 4 punchy, informative points (12-20 words each)
5. "key_takeaway": 1 memorable rule, formula, or core takeaway sentence
6. "narration_script": natural, spoken voiceover script written for ElevenLabs voice generation. It should sound like an encouraging teacher speaking directly to the student. DO NOT write meta-instructions like "Welcome to slide 2". Teach the concept directly with vivid explanation and analogies! (~40 to 75 words).

Respond STRICTLY with JSON:
{{
  "slides": [
    {{
      "slide_number": 1,
      "title": "...",
      "subtitle": "...",
      "bullet_points": ["point 1", "point 2", "point 3"],
      "key_takeaway": "...",
      "narration_script": "..."
    }}
  ]
}}"""

        user_content = f"""Topic: {topic}
Target Audience: {grade} (Ages: {age_group})
Tone: {tone}
Subheadings:
{json.dumps(subheadings, indent=2)}
"""
        if context_text:
            user_content += f"\nReference Material Extract:\n{context_text[:12000]}"
        if special_instructions:
            user_content += f"\nSpecial Instructions:\n{special_instructions}"

        try:
            raw_response = await self._chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ], json_mode=True)

            parsed = json.loads(raw_response)
            slides = parsed.get("slides", [])
            if slides:
                self.last_warning = None
                return slides
        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "Insufficient Balance" in err_str:
                self.last_warning = "DeepSeek API returned Insufficient Balance (402). Generated using Velix Pedagogical Engine."
            else:
                self.last_warning = f"DeepSeek unavailable ({err_str[:60]}...). Using Velix Pedagogical Engine."
            print(f"[LLMService] Slides fallback triggered due to: {e}")

        # Intelligent structured slide deck fallback
        fallback_slides = []
        for i, sub in enumerate(subheadings):
            clean_sub = sub.split(". ", 1)[-1] if ". " in sub else sub
            fallback_slides.append({
                "slide_number": i + 1,
                "title": clean_sub[:45],
                "subtitle": f"Understanding {clean_sub.lower()} for {grade}",
                "bullet_points": [
                    f"Fundamental concept: exploring how {clean_sub.lower()} shapes our understanding of {topic}.",
                    f"Key observation: identifying scientific patterns, formulas, and verified properties.",
                    f"Practical insight: recognizing everyday examples that bring {clean_sub.lower()} to life."
                ],
                "key_takeaway": f"Core Rule: {clean_sub} demonstrates the fundamental equilibrium of {topic}.",
                "narration_script": (
                    f"Welcome to our study of {clean_sub.lower()}. "
                    f"In this section, we examine the essential rules and principles governing {topic}. "
                    f"Notice how each principle connects directly to real-world phenomena around us. "
                    f"Keep this core definition in mind as we build toward the next concept."
                )
            })
        return fallback_slides

llm_service = LLMService()
