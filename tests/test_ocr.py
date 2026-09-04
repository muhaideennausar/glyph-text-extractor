"""
Unit tests for the pluggable OCR subsystem.
"""

import os
import sys
import unittest
from PIL import Image

# Ensure src directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from glyph.ocr.base import BaseOCREngine
from glyph.ocr.tesseract import TesseractEngine
from glyph.ocr.registry import OCREngineRegistry
from glyph.errors import EngineNotFoundError


class MockCustomEngine(BaseOCREngine):
    name = "mock_custom"
    display_name = "Mock Engine"
    description = "A mock engine for testing"

    def extract_text(self, image: Image.Image, **kwargs) -> str:
        return "mock text"

    def is_available(self) -> bool:
        return True


class TestOCRSubsystem(unittest.TestCase):

    def test_tesseract_engine_availability(self):
        """Tests that Tesseract engine detects system tesseract binary."""
        engine = TesseractEngine(language="eng")
        self.assertTrue(engine.is_available())
        langs = engine.get_supported_languages()
        self.assertIsInstance(langs, list)
        self.assertIn("eng", langs)

    def test_tesseract_clean_text(self):
        """Tests that _clean_text removes form-feeds and trims blank lines."""
        raw = "\x0c\n\n  Hello World!  \nLine Two   \n\n\x0c"
        cleaned = TesseractEngine._clean_text(raw)
        self.assertEqual(cleaned, "  Hello World!\nLine Two")

    def test_ocr_registry_workflow(self):
        """Tests registering, listing, and retrieving engines from OCREngineRegistry."""
        OCREngineRegistry.register(MockCustomEngine)
        engines = OCREngineRegistry.list_engines()
        self.assertIn("tesseract", engines)
        self.assertIn("mock_custom", engines)

        engine_instance = OCREngineRegistry.get_engine("mock_custom")
        self.assertIsInstance(engine_instance, MockCustomEngine)

        dummy_img = Image.new("RGB", (50, 50), (255, 255, 255))
        self.assertEqual(engine_instance.extract_text(dummy_img), "mock text")

    def test_registry_unknown_engine_raises(self):
        """Tests that retrieving an unknown engine raises EngineNotFoundError."""
        with self.assertRaises(EngineNotFoundError):
            OCREngineRegistry.get_engine("non_existent_engine")


if __name__ == "__main__":
    unittest.main(verbosity=2)

