"""
Automated unit tests for Glyph domain exception hierarchy and structured logging.
"""

import logging
import os
import sys
import unittest

# Ensure src directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from glyph.errors import (
    GlyphError,
    ConfigurationError,
    CaptureError,
    PortalTimeoutError,
    PortalCancelledError,
    PortalUnavailableError,
    PreprocessError,
    ImageValidationError,
    DimensionLimitExceededError,
    OCRError,
    EngineNotFoundError,
    RecognitionFailedError,
    ClipboardError,
)
from glyph.ocr import OCREngineRegistry
from glyph.logging_config import setup_logging


class TestDomainErrorsAndLogging(unittest.TestCase):

    def test_exception_hierarchy(self):
        """Tests that all domain exceptions properly inherit from GlyphError."""
        subclasses = [
            ConfigurationError,
            CaptureError,
            PortalTimeoutError,
            PortalCancelledError,
            PortalUnavailableError,
            PreprocessError,
            ImageValidationError,
            DimensionLimitExceededError,
            OCRError,
            EngineNotFoundError,
            RecognitionFailedError,
            ClipboardError,
        ]
        for cls in subclasses:
            self.assertTrue(issubclass(cls, GlyphError), f"{cls.__name__} is not a subclass of GlyphError")

    def test_exit_codes_defined(self):
        """Tests that domain errors have consistent, well-defined exit codes."""
        self.assertEqual(PortalCancelledError.exit_code, 0)
        self.assertEqual(ConfigurationError.exit_code, 2)
        self.assertEqual(CaptureError.exit_code, 3)
        self.assertEqual(PortalTimeoutError.exit_code, 4)
        self.assertEqual(PortalUnavailableError.exit_code, 5)
        self.assertEqual(ImageValidationError.exit_code, 7)
        self.assertEqual(DimensionLimitExceededError.exit_code, 8)
        self.assertEqual(EngineNotFoundError.exit_code, 10)

    def test_structured_error_string(self):
        """Tests that error messages format details correctly."""
        err1 = GlyphError("Simple error")
        self.assertEqual(str(err1), "Simple error")

        err2 = EngineNotFoundError("Engine missing", details="Install via apt")
        self.assertEqual(str(err2), "Engine missing (Install via apt)")
        self.assertEqual(err2.exit_code, 10)

    def test_registry_raises_engine_not_found(self):
        """Tests that requesting an unregistered OCR engine raises EngineNotFoundError."""
        with self.assertRaises(EngineNotFoundError) as ctx:
            OCREngineRegistry.get_engine("non_existent_engine_xyz")
        self.assertIn("non_existent_engine_xyz", str(ctx.exception))

    def test_logging_setup_levels(self):
        """Tests that setup_logging configures root logger levels properly."""
        logger_default = setup_logging(debug=False, verbose=False)
        self.assertEqual(logging.getLogger().level, logging.INFO)

        logger_verbose = setup_logging(debug=False, verbose=True)
        self.assertEqual(logging.getLogger().level, logging.INFO)

        logger_debug = setup_logging(debug=True, verbose=False)
        self.assertEqual(logging.getLogger().level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main(verbosity=2)

