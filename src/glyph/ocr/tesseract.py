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

    def __init__(self, language: str = "eng", default_psm: int = 3):
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

    @staticmethod
    def detect_optimal_psm(image: Image.Image) -> int:
        """Heuristically selects the most accurate Tesseract PSM based on image geometry.

        - Single-line snippet (aspect ratio >= 3.0, height <= 80): PSM 7 (single line)
        - Short block / UI snippet (height <= 300): PSM 6 (uniform text block)
        - Large / page capture (height >= 500, width >= 600): PSM 3 (automatic multi-column)
        - Default for screen clips: PSM 6 (uniform block avoids spurious column breaks)
        """
        w, h = image.size
        if h <= 0:
            return 6
        aspect_ratio = w / float(h)

        if h <= 80 and aspect_ratio >= 3.0:
            return 7  # Single text line
        elif h <= 300:
            return 6  # Assume a single uniform block of text
        elif w >= 600 and h >= 500:
            return 3  # Fully automatic page segmentation
        else:
            return 6  # Uniform block is the most reliable default for screen clips

    def extract_text(
        self,
        image: Image.Image,
        psm: Optional[int] = None,
        auto_psm: bool = True,
        **kwargs
    ) -> str:
        if psm is not None:
            target_psm = psm
        elif auto_psm:
            target_psm = self.detect_optimal_psm(image)
        else:
            target_psm = self.default_psm

        # Encode image into memory buffer
        byte_buffer = io.BytesIO()
        image.save(byte_buffer, format="PNG")
        image_bytes = byte_buffer.getvalue()

        # Primary pass
        text = self._run_tesseract(image_bytes, target_psm)

        # If primary pass produced nothing, run smart fallback cascade
        if not text.strip():
            candidate_psms = [6, 7, 11, 3] if target_psm not in (6, 7) else [6, 11, 3, 7]
            for fallback_psm in candidate_psms:
                if fallback_psm != target_psm:
                    text = self._run_tesseract(image_bytes, psm=fallback_psm)
                    if text.strip():
                        break

        # If still empty, try Otsu binarization fallback pass
        if not text.strip():
            try:
                from glyph.preprocess import ImagePreprocessor
                bin_img = ImagePreprocessor.binarize_otsu(image)
                bin_buffer = io.BytesIO()
                bin_img.save(bin_buffer, format="PNG")
                bin_bytes = bin_buffer.getvalue()
                text = self._run_tesseract(bin_bytes, psm=target_psm)
                if not text.strip():
                    for fallback_psm in [6, 7, 11]:
                        text = self._run_tesseract(bin_bytes, psm=fallback_psm)
                        if text.strip():
                            break
            except Exception as e:
                logger.debug(f"Binarization fallback pass failed: {e}")

        return self._clean_text(text)

    def extract_tsv(self, image: Image.Image, psm: Optional[int] = None) -> List[dict]:
        """Extracts structured word data with confidence scores from Tesseract TSV."""
        target_psm = psm if psm is not None else self.detect_optimal_psm(image)
        byte_buffer = io.BytesIO()
        image.save(byte_buffer, format="PNG")
        cmd = [
            "tesseract",
            "stdin",
            "stdout",
            "tsv",
            "-l", self.language,
            "--psm", str(target_psm),
            "--oem", "1",
            "-c", "preserve_interword_spaces=1",
            "-c", "user_defined_dpi=300",
        ]
        try:
            res = subprocess.run(cmd, input=byte_buffer.getvalue(), capture_output=True, check=False, timeout=10)
            if res.returncode != 0:
                return []
            lines = res.stdout.decode("utf-8", errors="replace").splitlines()
            if not lines:
                return []
            headers = lines[0].split("\t")
            records = []
            for row in lines[1:]:
                parts = row.split("\t")
                if len(parts) == len(headers):
                    record = dict(zip(headers, parts))
                    try:
                        record["conf"] = float(record.get("conf", -1))
                    except ValueError:
                        record["conf"] = -1.0
                    records.append(record)
            return records
        except Exception as e:
            logger.debug(f"TSV extraction failed: {e}")
            return []

    def _run_tesseract(self, image_bytes: bytes, psm: int) -> str:
        cmd = [
            "tesseract",
            "stdin",
            "stdout",
            "-l", self.language,
            "--psm", str(psm),
            "--oem", "1",
            "-c", "preserve_interword_spaces=1",
            "-c", "user_defined_dpi=300",
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

        # Filter out stray single-character punctuation noise lines
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if len(stripped) == 1 and stripped in ".~`^'\"-–_":
                continue
            filtered_lines.append(line)

        while filtered_lines and not filtered_lines[0].strip():
            filtered_lines.pop(0)
        while filtered_lines and not filtered_lines[-1].strip():
            filtered_lines.pop()
        return "\n".join(filtered_lines)

