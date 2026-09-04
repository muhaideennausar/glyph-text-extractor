"""
Image preprocessing pipeline optimized for OCR on UI text and screen clips.
"""

import os
from typing import Tuple, Union
import statistics
import logging
from PIL import Image, ImageOps, UnidentifiedImageError

from glyph.errors import ImageValidationError, DimensionLimitExceededError

# Enforce security pixel budget (50 megapixels maximum) to prevent decompression bombs
MAX_SAFE_PIXELS = 50_000_000
Image.MAX_IMAGE_PIXELS = MAX_SAFE_PIXELS

logger = logging.getLogger("glyph.preprocess")


class ImagePreprocessor:
    """
    Cleans, normalizes, and prepares screen clippings for maximum Tesseract OCR accuracy.
    Handles dark-mode inversion, dynamic contrast adjustment, and resolution scaling.
    """

    @classmethod
    def validate_and_open(cls, image_path_or_obj: Union[str, Image.Image]) -> Image.Image:
        """
        Validates image source, checking existence, header validity, 
        and pixel limits before full decompression.
        """
        if isinstance(image_path_or_obj, str):
            if not os.path.exists(image_path_or_obj):
                raise ImageValidationError(f"Image file does not exist: {image_path_or_obj}")
            if os.path.getsize(image_path_or_obj) == 0:
                raise ImageValidationError(f"Image file is empty (0 bytes): {image_path_or_obj}")
            try:
                with Image.open(image_path_or_obj) as test_img:
                    test_img.verify()
                raw_img = Image.open(image_path_or_obj)
            except Image.DecompressionBombError as e:
                raise DimensionLimitExceededError(f"Decompression bomb limit exceeded: {e}")
            except (UnidentifiedImageError, SyntaxError, OSError) as e:
                raise ImageValidationError(f"Invalid or corrupted image file: {e}")
        elif isinstance(image_path_or_obj, Image.Image):
            raw_img = image_path_or_obj
        else:
            raise ImageValidationError(f"Unsupported image input type: {type(image_path_or_obj)}")

        w, h = raw_img.size
        if w <= 0 or h <= 0:
            if isinstance(image_path_or_obj, str):
                raw_img.close()
            raise ImageValidationError(f"Invalid image dimensions: {w}x{h}")
        if (w * h) > MAX_SAFE_PIXELS:
            if isinstance(image_path_or_obj, str):
                raw_img.close()
            raise DimensionLimitExceededError(
                f"Image resolution {w}x{h} ({w * h:,} pixels) exceeds safe limit of {MAX_SAFE_PIXELS:,} pixels."
            )

        return raw_img

    @staticmethod
    def _handle_alpha(image: Image.Image) -> Image.Image:
        """Flattens RGBA transparency against a solid white background."""
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            alpha = image.convert("RGBA")
            bg = Image.new("RGBA", alpha.size, (255, 255, 255, 255))
            bg.paste(alpha, mask=alpha.split()[3])
            return bg.convert("RGB")
        return image.convert("RGB")

    @staticmethod
    def _detect_background_luminance(image: Image.Image) -> float:
        """
        Samples the corners and outer perimeter pixels to determine if the crop
        has a dark or light background.
        """
        w, h = image.size
        if w <= 0 or h <= 0:
            return 255.0

        sample_points = [
            (0, 0), (max(0, w - 1), 0), (0, max(0, h - 1)), (max(0, w - 1), max(0, h - 1)),
            (w // 2, 0), (w // 2, max(0, h - 1)), (0, h // 2), (max(0, w - 1), h // 2)
        ]
        luminances = []
        for x, y in sample_points:
            x_clamped = max(0, min(w - 1, x))
            y_clamped = max(0, min(h - 1, y))
            try:
                pixel = image.getpixel((x_clamped, y_clamped))
                luminances.append(pixel if isinstance(pixel, (int, float)) else pixel[0])
            except Exception:
                continue

        if not luminances:
            return 255.0
        return statistics.median(luminances)

    @staticmethod
    def _calculate_adaptive_scale(orig_w: int, orig_h: int, target_scale: float) -> float:
        """
        Dynamically adjusts upscale factor based on image dimensions.
        Small crops (10-14px UI fonts) need 3x upscaling.
        Large crops or full pages already have large text and should not be blown up.
        """
        if target_scale <= 1.0:
            return 1.0

        if orig_h <= 120:
            return target_scale  # 3.0x for small UI snippets and 1-3 lines
        elif orig_h <= 250:
            return min(target_scale, 2.0)
        elif orig_h <= 450:
            return min(target_scale, 1.4)
        else:
            return 1.0  # Full pages or tall clippings

    @classmethod
    def process(
        cls,
        image_path_or_obj: Union[str, Image.Image],
        scale_factor: float = 3.0,
        padding_px: int = 30
    ) -> Image.Image:
        """
        Executes the full preprocessing pipeline:
        1. Validate & open safely
        2. Flatten alpha
        3. Convert to grayscale
        4. Dynamic contrast normalization
        5. Dark mode background detection & auto-inversion
        6. Adaptive upscaling (preserves scale for large text, upscales tiny UI fonts)
        7. White border padding to prevent edge character truncation
        """
        raw_img = cls.validate_and_open(image_path_or_obj)

        # 1. Flatten transparency
        img = cls._handle_alpha(raw_img)

        # 2. Convert to grayscale (Luminance)
        img = img.convert("L")

        # 3. Dynamic contrast normalization
        img = ImageOps.autocontrast(img, cutoff=1)

        # 4. Inversion if dark mode detected
        bg_lum = cls._detect_background_luminance(img)
        if bg_lum < 128:
            img = ImageOps.invert(img)
            img = ImageOps.autocontrast(img, cutoff=2)

        # 5. Smart adaptive upscaling
        orig_w, orig_h = img.size
        effective_scale = cls._calculate_adaptive_scale(orig_w, orig_h, scale_factor)
        if effective_scale > 1.0:
            new_w = max(1, int(orig_w * effective_scale))
            new_h = max(1, int(orig_h * effective_scale))
            img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

        # 6. Padding with pure white around the text
        if padding_px > 0:
            img = ImageOps.expand(img, border=padding_px, fill=255)

        return img

