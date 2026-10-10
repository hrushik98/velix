import io
from pathlib import Path
from typing import Optional
import httpx
from pypdf import PdfReader

class PDFService:
    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> str:
        """Extract clean text from PDF bytes."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            full_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text.append(f"--- Page {i+1} ---\n{text.strip()}")
            return "\n\n".join(full_text)
        except Exception as e:
            raise RuntimeError(f"Error reading PDF: {e}")

    @classmethod
    async def extract_text_from_url(cls, url: str) -> str:
        """Download PDF from URL and extract text."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download PDF from {url} (status {resp.status_code})")
            return cls.extract_text_from_bytes(resp.content)

pdf_service = PDFService()
