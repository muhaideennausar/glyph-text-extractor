"""
Tesseract 5 LSTM OCR Engine implementation.
"""

import io
import logging
import shutil
import subprocess
from typing import List, Optional
from PIL import Image

from glyph.ocr.base import BaseOCREngine
from glyph.errors import EngineNotFoundError, RecognitionFailedError

logger = logging.getLogger("glyph.ocr.tesseract")


class TesseractEngine(BaseOCREngine):
    """
    Tesseract 5 LSTM OCR Engine.
    Extremely fast, CPU-only, in-memory streaming, ideal for typed/screen text.
    """

    name: str = "tesseract"
    display_name: str = "Tesseract 5 (Local/Fast)"
    description: str = "Default engine: instant, low-memory, runs on any hardware."

    def __init__(self, language: str = "eng", default_psm: int = 6):
        self.language = language
        self.default_psm = default_psm
        self._check_installed()

    def _check_installed(self) -> None:
        if not self.is_available():
            raise EngineNotFoundError(
                "Tesseract is not installed or not in PATH.",
                details="Install via: 'sudo apt install tesseract-ocr tesseract-ocr-eng'"
            )

    def is_available(self) -> bool:
        return bool(shutil.which("tesseract"))

    def get_supported_languages(self) -> List[str]:
        if not self.is_available():
            return []
        try:
            res = subprocess.run(
                ["tesseract", "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5
            )
            langs = []
            for line in res.stdout.splitlines()[1:]:
                clean = line.strip()
                if clean and clean != "osd":
                    langs.append(clean)
            return langs
        except subprocess.TimeoutExpired:
            logger.warning("Listing Tesseract languages timed out after 5 seconds.")
            return ["eng"]
        except Exception as e:
            logger.debug(f"Failed to list Tesseract languages: {e}")
            return ["eng"]

    def extract_text(self, image: Image.Image, psm: Optional[int] = None, **kwargs) -> str:
        target_psm = psm if psm is not None else self.default_psm

        # Encode image into memory buffer
        byte_buffer = io.BytesIO()
        image.save(byte_buffer, format="PNG")
        image_bytes = byte_buffer.getvalue()

        # Try primary PSM
        text = self._run_tesseract(image_bytes, target_psm)

        # Smart fallback if PSM 6 produced nothing
        if not text and target_psm == 6:
            text = self._run_tesseract(image_bytes, psm=3)
            if not text:
                text = self._run_tesseract(image_bytes, psm=7)

        return self._clean_text(text)

    def _run_tesseract(self, image_bytes: bytes, psm: int) -> str:
        cmd = [
            "tesseract",
            "stdin",
            "stdout",
            "-l", self.language,
            "--psm", str(psm),
            "--oem", "1",
        ]
        try:
            result = subprocess.run(
                cmd,
                input=image_bytes,
                capture_output=True,
                check=False,
                timeout=10
            )
            if result.returncode != 0:
                stderr_output = result.stderr.decode("utf-8", errors="replace").strip()
                if stderr_output:
                    logger.debug(f"Tesseract returned code {result.returncode}: {stderr_output}")
                return ""
            return result.stdout.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            logger.error(f"Tesseract OCR timed out after 10 seconds (psm={psm}, lang={self.language}).")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error running Tesseract: {e}")
            return ""

    @staticmethod
    def _clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        cleaned = raw_text.replace("\x0c", "")
        lines = [line.rstrip() for line in cleaned.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

