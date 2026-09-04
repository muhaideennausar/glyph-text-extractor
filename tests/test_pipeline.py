"""
Automated unit and integration test suite for Glyph.
Tests image preprocessing, Tesseract OCR accuracy, clipboard, and notifications.
"""

import os
import sys
import unittest
import tempfile
from PIL import Image, ImageDraw

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import stat
from unittest.mock import patch
import subprocess

from glyph.preprocess import ImagePreprocessor, MAX_SAFE_PIXELS
from glyph.ocr import OCREngine, TesseractEngine
from glyph.clipboard import ClipboardManager
from glyph.capture import _create_secure_temp_file
from glyph.app import run_pipeline
from glyph.errors import (
    ImageValidationError,
    DimensionLimitExceededError,
)


class TestGlyphPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_synthetic_image(self, text: str, dark_mode: bool = False, font_size: int = 14) -> str:
        """Helper to create synthetic test images with known text."""
        bg_color = (24, 24, 28) if dark_mode else (255, 255, 255)
        text_color = (240, 240, 240) if dark_mode else (10, 10, 10)

        img = Image.new("RGB", (450, 90), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Using default font bitmap
        draw.text((25, 30), text, fill=text_color)

        filename = os.path.join(self.temp_dir.name, f"test_{'dark' if dark_mode else 'light'}.png")
        img.save(filename)
        return filename

    def test_light_mode_ocr(self):
        """Tests OCR on a standard light-theme screenshot."""
        expected = "Production Ready Linux OCR"
        img_path = self.create_synthetic_image(expected, dark_mode=False)

        raw = Image.open(img_path)
        processed = ImagePreprocessor.process(raw, scale_factor=3.0)

        engine = OCREngine(language="eng", default_psm=6)
        text = engine.extract_text(processed)
        self.assertIn("Production Ready Linux OCR", text)

    def test_dark_mode_inversion_and_ocr(self):
        """Tests auto-inversion and OCR accuracy on a dark-theme screenshot."""
        expected = "Dark Mode Extractor Test"
        img_path = self.create_synthetic_image(expected, dark_mode=True)

        raw = Image.open(img_path)
        processed = ImagePreprocessor.process(raw, scale_factor=3.0)

        engine = OCREngine(language="eng", default_psm=6)
        text = engine.extract_text(processed)
        self.assertIn("Dark Mode Extractor Test", text)

    def test_clipboard_copy(self):
        """Tests copying text to system clipboard."""
        sample_text = "Glyph Clipboard Test 12345"
        success = ClipboardManager.copy(sample_text)
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            self.assertIsInstance(success, bool)
        else:
            self.assertTrue(success)

    def test_pipeline_execution(self):
        """Tests the entire run_pipeline coordinator with notifications suppressed."""
        expected = "End To End Pipeline Test"
        img_path = self.create_synthetic_image(expected, dark_mode=False)

        result = run_pipeline(
            image_path=img_path,
            language="eng",
            psm=6,
            scale=3.0,
            notify=False,
            copy_clipboard=True,
            print_stdout=False
        )
        self.assertIn("End To End Pipeline Test", result)

    def test_corrupt_image_rejection(self):
        """Tests that corrupted non-image files are rejected with ImageValidationError."""
        corrupt_file = os.path.join(self.temp_dir.name, "corrupt.png")
        with open(corrupt_file, "wb") as f:
            f.write(b"NOT_A_VALID_PNG_HEADER_CORRUPT_DATA")

        with self.assertRaises(ImageValidationError):
            ImagePreprocessor.process(corrupt_file)

        # Ensure run_pipeline safely catches this and returns empty string
        result = run_pipeline(image_path=corrupt_file, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    def test_zero_byte_file_rejection(self):
        """Tests that 0-byte files are caught gracefully without unhandled exceptions."""
        empty_file = os.path.join(self.temp_dir.name, "empty.png")
        with open(empty_file, "wb") as f:
            pass

        with self.assertRaises(ImageValidationError):
            ImagePreprocessor.process(empty_file)

        result = run_pipeline(image_path=empty_file, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    def test_nonexistent_file_rejection(self):
        """Tests that nonexistent files are rejected gracefully."""
        missing = os.path.join(self.temp_dir.name, "does_not_exist.png")
        with self.assertRaises(ImageValidationError):
            ImagePreprocessor.process(missing)

        result = run_pipeline(image_path=missing, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    def test_decompression_bomb_budget_guard(self):
        """Tests that images exceeding 50,000,000 pixels are rejected before memory allocation."""
        # Create a lightweight 1-bit image that exceeds 50M pixels (10000 x 5001 = 50,010,000 px)
        huge_img = Image.new("1", (10000, 5001))
        with self.assertRaises(DimensionLimitExceededError):
            ImagePreprocessor.process(huge_img)

        # Also test with saved file
        huge_path = os.path.join(self.temp_dir.name, "huge.png")
        huge_img.save(huge_path)

        with self.assertRaises(DimensionLimitExceededError):
            ImagePreprocessor.process(huge_path)

        result = run_pipeline(image_path=huge_path, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    def test_secure_temp_file_permissions(self):
        """Tests that temporary capture files are strictly created with 0o600 permissions."""
        path = _create_secure_temp_file()
        try:
            self.assertTrue(os.path.exists(path))
            file_stat = os.stat(path)
            mode = stat.S_IMODE(file_stat.st_mode)
            # Ensure permissions are exactly 0o600 (read/write only by owner)
            self.assertEqual(mode, 0o600)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_tesseract_timeout_recovery(self):
        """Tests that TesseractEngine recovers cleanly from subprocess timeouts."""
        engine = TesseractEngine(language="eng")
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="tesseract", timeout=10)):
            sample_img = Image.new("RGB", (100, 30), color=(255, 255, 255))
            text = engine.extract_text(sample_img)
            self.assertEqual(text, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
