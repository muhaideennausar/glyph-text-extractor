"""
Unit tests for the pluggable OCR subsystem.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
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

    def test_detect_optimal_psm(self):
        """Tests geometry-based PSM selection heuristic."""
        # Single-line snippet: wide and short
        img_single = Image.new("L", (300, 50))
        self.assertEqual(TesseractEngine.detect_optimal_psm(img_single), 7)

        # Standard text block / UI clip
        img_block = Image.new("L", (250, 150))
        self.assertEqual(TesseractEngine.detect_optimal_psm(img_block), 6)

        # Full page / multi-column document
        img_page = Image.new("L", (800, 700))
        self.assertEqual(TesseractEngine.detect_optimal_psm(img_page), 3)

    def test_tesseract_clean_text_noise_filter(self):
        """Tests that single-character noise lines are filtered out."""
        raw = "Line One\n.\nLine Two\n~\nLine Three"
        cleaned = TesseractEngine._clean_text(raw)
        self.assertEqual(cleaned, "Line One\nLine Two\nLine Three")

    @patch("subprocess.run")
    def test_extract_tsv_parsing(self, mock_run):
        """Tests TSV structured data extraction and confidence parsing."""
        tsv_output = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t10\t10\t50\t20\t95.5\tHello\n"
            "5\t1\t1\t1\t1\t2\t70\t10\t50\t20\t88.0\tWorld\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=tsv_output.encode("utf-8"))

        engine = TesseractEngine(language="eng")
        dummy_img = Image.new("L", (100, 40))
        records = engine.extract_tsv(dummy_img, psm=7)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["text"], "Hello")
        self.assertEqual(records[0]["conf"], 95.5)
        self.assertEqual(records[1]["text"], "World")
        self.assertEqual(records[1]["conf"], 88.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

