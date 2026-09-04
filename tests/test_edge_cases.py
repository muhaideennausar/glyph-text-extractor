"""
Automated edge-case and failure-mode test suite for Glyph.
Covers the full testing matrix from Section 5 of PRODUCTION_PLAN.md:
- 10,000x10,000px Gigapixel Bomb
- 0-byte screenshot file
- Corrupt image variations
- D-Bus Portal timeouts and cancellation mocks
- Multi-line PDF formatting helpers
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

# Ensure src directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from glyph.preprocess import ImagePreprocessor
from glyph.capture import ScreenCapture
from glyph.clipboard import ClipboardManager, NotificationManager
from glyph.app import run_pipeline
from glyph.ui.editor import format_single_line, format_trim_whitespace
from glyph.errors import (
    ImageValidationError,
    DimensionLimitExceededError,
    PortalTimeoutError,
)


class TestEdgeCasesAndFailureModes(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Gigapixel Decompression Bomb (10,000 x 10,000 px = 100,000,000 pixels)
    # -------------------------------------------------------------------------
    def test_gigapixel_bomb_rejection(self):
        """Tests that a 10,000x10,000px (100MP) synthetic image is safely rejected without memory spike."""
        # 1-bit mode allows creating 100MP in memory with only ~12MB RAM
        gigapixel_img = Image.new("1", (10000, 10000))
        with self.assertRaises(DimensionLimitExceededError):
            ImagePreprocessor.process(gigapixel_img)

        # File-based rejection
        bomb_file = os.path.join(self.temp_dir.name, "bomb_100mp.png")
        gigapixel_img.save(bomb_file)

        with self.assertRaises(DimensionLimitExceededError):
            ImagePreprocessor.process(bomb_file)

        result = run_pipeline(image_path=bomb_file, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    # -------------------------------------------------------------------------
    # 2. 0-byte File Handling (Compositor Abort / Empty File)
    # -------------------------------------------------------------------------
    def test_zero_byte_empty_capture(self):
        """Tests that an empty 0-byte file (e.g. compositor abort) cleanly exits without unhandled traceback."""
        empty_path = os.path.join(self.temp_dir.name, "aborted_capture.png")
        with open(empty_path, "wb") as f:
            pass  # 0 bytes

        with self.assertRaises(ImageValidationError) as ctx:
            ImagePreprocessor.process(empty_path)
        self.assertIn("empty", str(ctx.exception).lower())

        result = run_pipeline(image_path=empty_path, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    # -------------------------------------------------------------------------
    # 3. Corrupt Image Variations
    # -------------------------------------------------------------------------
    def test_html_disguised_as_image(self):
        """Tests that HTML content disguised with .png extension is rejected cleanly."""
        fake_png = os.path.join(self.temp_dir.name, "fake.png")
        with open(fake_png, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Not an image</h1></body></html>")

        with self.assertRaises(ImageValidationError):
            ImagePreprocessor.process(fake_png)

        result = run_pipeline(image_path=fake_png, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    def test_truncated_png_header(self):
        """Tests that a truncated PNG file is rejected cleanly."""
        truncated_path = os.path.join(self.temp_dir.name, "truncated.png")
        with open(truncated_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # Only 8-byte signature, no IHDR

        with self.assertRaises(ImageValidationError):
            ImagePreprocessor.process(truncated_path)

        result = run_pipeline(image_path=truncated_path, notify=False, print_stdout=False)
        self.assertEqual(result, "")

    # -------------------------------------------------------------------------
    # 4. Portal Timeout & Cancellation Mocks
    # -------------------------------------------------------------------------
    @patch("glyph.capture.Gio.bus_get_sync")
    @patch("glyph.capture.Gio.DBusProxy.new_sync")
    @patch("glyph.capture.GLib.MainLoop")
    def test_portal_timeout_mock(self, mock_loop_cls, mock_proxy_cls, mock_bus_cls):
        """Tests that a hanging portal listener raises PortalTimeoutError when the 120s timer expires."""
        mock_bus = MagicMock()
        mock_bus.get_unique_name.return_value = ":1.99"
        mock_bus.signal_subscribe.return_value = 42
        mock_bus_cls.return_value = mock_bus

        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy

        # Simulate loop run triggering the timeout handler
        def fake_run():
            pass

        mock_loop = MagicMock()
        mock_loop.run.side_effect = fake_run
        mock_loop_cls.return_value = mock_loop

        # Patch GLib.timeout_add_seconds to immediately fire the timeout callback
        def fake_timeout_add(seconds, callback):
            callback()  # Fire on_timeout
            return 123

        with patch("glyph.capture.GLib.timeout_add_seconds", side_effect=fake_timeout_add):
            with self.assertRaises(PortalTimeoutError):
                ScreenCapture._capture_via_portal()

    @patch("glyph.capture.Gio.bus_get_sync")
    @patch("glyph.capture.Gio.DBusProxy.new_sync")
    @patch("glyph.capture.GLib.MainLoop")
    def test_portal_user_cancellation_mock(self, mock_loop_cls, mock_proxy_cls, mock_bus_cls):
        """Tests that user cancelling the portal dialog (response_code != 0) returns None cleanly."""
        mock_bus = MagicMock()
        mock_bus.get_unique_name.return_value = ":1.99"
        mock_bus.signal_subscribe.return_value = 42
        mock_bus_cls.return_value = mock_bus

        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy

        # Capture the signal handler callback
        signal_callback = None

        def fake_subscribe(*args, **kwargs):
            nonlocal signal_callback
            signal_callback = args[6]  # on_signal function
            return 99

        mock_bus.signal_subscribe.side_effect = fake_subscribe

        mock_loop = MagicMock()

        def fake_loop_run():
            # Trigger portal response signal with response_code = 1 (User cancelled)
            if signal_callback:
                from gi.repository import GLib
                parameters = GLib.Variant("(ua{sv})", (1, {}))
                signal_callback(mock_bus, "org.freedesktop.portal.Desktop", "/path", "iface", "Response", parameters, None)

        mock_loop.run.side_effect = fake_loop_run
        mock_loop_cls.return_value = mock_loop

        result = ScreenCapture._capture_via_portal()
        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # 5. Multi-line Formatting (PDF Clippings & Whitespace)
    # -------------------------------------------------------------------------
    def test_multi_line_pdf_single_line_formatting(self):
        """Tests formatting broken lines from PDF clippings into a single continuous sentence."""
        pdf_clipping = """This is an excerpt from a PDF
document where sentences are broken
across multiple lines due to page margins
and narrow columns."""
        formatted = format_single_line(pdf_clipping)
        expected = "This is an excerpt from a PDF document where sentences are broken across multiple lines due to page margins and narrow columns."
        self.assertEqual(formatted, expected)

    def test_trim_whitespace_and_redundant_lines(self):
        """Tests trimming whitespace and collapsing multiple redundant empty lines."""
        clipping = "   Header Line   \n\n\n\n   Content line 1   \n\n   Content line 2   \n\n\n"
        trimmed = format_trim_whitespace(clipping)
        expected = "Header Line\nContent line 1\nContent line 2"
        self.assertEqual(trimmed, expected)

    def test_formatting_empty_inputs(self):
        """Tests formatting functions with empty strings or whitespace-only inputs."""
        self.assertEqual(format_single_line(""), "")
        self.assertEqual(format_single_line("    \n\n   "), "")
        self.assertEqual(format_trim_whitespace(""), "")
        self.assertEqual(format_trim_whitespace("   \n   \n   "), "")

    # -------------------------------------------------------------------------
    # 6. Compositor Tool Failures
    # -------------------------------------------------------------------------
    @patch("subprocess.run")
    def test_slurp_cancellation(self, mock_run):
        """Tests that slurp returning empty string (user Esc) returns None without error."""
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.returncode = 1
        mock_run.return_value = mock_proc

        result = ScreenCapture._capture_via_grim_slurp()
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_gnome_screenshot_cancellation(self, mock_run):
        """Tests that gnome-screenshot cancellation (non-zero or empty file) returns None."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_run.return_value = mock_proc

        result = ScreenCapture._capture_via_gnome_screenshot()
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_spectacle_cancellation(self, mock_run):
        """Tests that spectacle cancellation (non-zero or empty file) returns None."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_run.return_value = mock_proc

        result = ScreenCapture._capture_via_spectacle()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

