"""
Pluggable OCR subsystem for Glyph.
"""

from glyph.ocr.base import BaseOCREngine
from glyph.ocr.tesseract import TesseractEngine
from glyph.ocr.registry import OCREngineRegistry

# Register built-in engines
OCREngineRegistry.register(TesseractEngine)

# Backward-compatibility alias
OCREngine = TesseractEngine

__all__ = [
    "BaseOCREngine",
    "TesseractEngine",
    "OCREngineRegistry",
    "OCREngine",
]

