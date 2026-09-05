"""
Unit tests for the image preprocessing pipeline.
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

from glyph.preprocess import ImagePreprocessor


class TestImagePreprocessor(unittest.TestCase):

    def test_alpha_handling(self):
        """Tests that RGBA transparency is flattened onto a solid white background."""
        # Create transparent RGBA image with transparent pixel
        rgba_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        flattened = ImagePreprocessor._handle_alpha(rgba_img)

        self.assertEqual(flattened.mode, "RGB")
        # Checking pixel color: should be pure white (255, 255, 255)
        pixel = flattened.getpixel((50, 50))
        self.assertEqual(pixel, (255, 255, 255))

    def test_background_luminance_detection(self):
        """Tests detecting dark mode vs light mode background luminance."""
        # Pure black image
        dark_img = Image.new("L", (100, 100), color=0)
        dark_lum = ImagePreprocessor._detect_background_luminance(dark_img)
        self.assertEqual(dark_lum, 0.0)

        # Pure white image
        light_img = Image.new("L", (100, 100), color=255)
        light_lum = ImagePreprocessor._detect_background_luminance(light_img)
        self.assertEqual(light_lum, 255.0)

    def test_adaptive_scaling_rules(self):
        """Tests adaptive upscale factor calculations based on crop height."""
        # Small crop (h <= 120): should receive full 3.0x scaling
        scale_small = ImagePreprocessor._calculate_adaptive_scale(300, 80, 3.0)
        self.assertEqual(scale_small, 3.0)

        # Medium crop (120 < h <= 250): should be capped at 2.0x
        scale_med = ImagePreprocessor._calculate_adaptive_scale(500, 180, 3.0)
        self.assertEqual(scale_med, 2.0)

        # Large crop (250 < h <= 450): should be capped at 1.4x
        scale_large = ImagePreprocessor._calculate_adaptive_scale(600, 350, 3.0)
        self.assertEqual(scale_large, 1.4)

        # Very large or full page (h > 450): should not be upscaled (1.0x)
        scale_page = ImagePreprocessor._calculate_adaptive_scale(1000, 800, 3.0)
        self.assertEqual(scale_page, 1.0)

    def test_enhance_edges(self):
        """Tests that edge enhancement runs and preserves image dimensions."""
        img = Image.new("L", (100, 100), color=128)
        enhanced = ImagePreprocessor.enhance_edges(img)
        self.assertEqual(enhanced.size, (100, 100))

    def test_binarize_otsu(self):
        """Tests that Otsu binarization produces a two-tone (0 or 255) grayscale image."""
        img = Image.new("L", (100, 100), color=100)
        # Create a contrasting patch
        for x in range(30, 70):
            for y in range(30, 70):
                img.putpixel((x, y), 200)
        binarized = ImagePreprocessor.binarize_otsu(img)
        self.assertEqual(binarized.size, (100, 100))
        colors = binarized.getcolors()
        self.assertIsNotNone(colors)
        # All pixels must be either 0 or 255
        pixel_values = {val for count, val in colors}
        self.assertTrue(pixel_values.issubset({0, 255}))

    def test_process_with_enhance_and_binarize(self):
        """Tests running the pipeline with both edge sharpening and binarization enabled."""
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        processed = ImagePreprocessor.process(
            img,
            scale_factor=1.0,
            padding_px=10,
            enhance_edges=True,
            binarize=True
        )
        self.assertEqual(processed.size, (120, 120))


if __name__ == "__main__":
    unittest.main(verbosity=2)

