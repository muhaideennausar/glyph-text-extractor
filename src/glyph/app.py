"""
Glyph core application coordinator and command-line interface.
"""

import os
import sys
import argparse
import logging
from typing import Optional
from PIL import Image

from glyph import __version__, __app_name__
from glyph.capture import ScreenCapture
from glyph.preprocess import ImagePreprocessor
from glyph.ocr import OCREngine
from glyph.clipboard import ClipboardManager, NotificationManager
from glyph.config import ConfigManager
from glyph.logging_config import setup_logging
from glyph.errors import (
    GlyphError,
    ImageValidationError,
    DimensionLimitExceededError,
    PortalTimeoutError,
    PortalUnavailableError,
)

logger = logging.getLogger("glyph")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description="Glyph: High-performance Linux screen text extractor (PowerToys Text Extractor clone)."
    )
    parser.add_argument(
        "--grab", "-g",
        action="store_true",
        default=True,
        help="Trigger interactive screen selection (default behavior)."
    )
    parser.add_argument(
        "--edit", "-e",
        action="store_true",
        default=None,
        help="Mode B: Open review & edit modal before copying to clipboard."
    )
    parser.add_argument(
        "--instant", "-i",
        action="store_true",
        default=None,
        help="Mode A: Directly copy to clipboard without opening editor modal."
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Path to an existing image file to extract text from."
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default=None,
        help="OCR language code (overrides config default)."
    )
    parser.add_argument(
        "--psm", "-p",
        type=int,
        default=None,
        help="Tesseract Page Segmentation Mode (overrides config default)."
    )
    parser.add_argument(
        "--scale", "-s",
        type=float,
        default=None,
        help="Image upscale factor before OCR (overrides config default)."
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        default=None,
        help="Show desktop notifications (overrides config)."
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        default=None,
        help="Suppress desktop notifications (overrides config)."
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        default=None,
        help="Copy extracted text to clipboard (overrides config)."
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        default=None,
        help="Do not copy extracted text to clipboard (overrides config)."
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the extracted text directly to stdout."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug logging."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{__app_name__} {__version__}"
    )
    return parser.parse_args()


def run_pipeline(
    image_path: str,
    language: str = "eng",
    psm: int = 6,
    scale: float = 3.0,
    edit_mode: bool = False,
    notify: bool = True,
    copy_clipboard: bool = True,
    print_stdout: bool = True
) -> str:
    """Executes the preprocessor -> OCR -> clipboard -> notification pipeline."""
    try:
        # 1. Preprocess image with defensive validation
        processed_image = ImagePreprocessor.process(image_path, scale_factor=scale)
    except ImageValidationError as e:
        logger.error(f"Image validation failed: {e}")
        if notify:
            NotificationManager.notify_error(f"Invalid image: {e}")
        return ""
    except DimensionLimitExceededError as e:
        logger.error(f"Image rejected for security: {e}")
        if notify:
            NotificationManager.notify_error("Image exceeds safety limits.")
        return ""
    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        if notify:
            NotificationManager.notify_error("Image processing failed.")
        return ""

    # 2. Extract text via Tesseract
    engine = OCREngine(language=language, default_psm=psm)
    extracted_text = engine.extract_text(processed_image, psm=psm)

    # 3. Handle result
    if extracted_text:
        if edit_mode:
            # Lazy import GTK4/Adw only when editor is requested
            from glyph.ui.editor import launch_edit_modal
            edited = launch_edit_modal(extracted_text)
            if edited is None:
                # User cancelled review in editor
                return ""
            extracted_text = edited

        if copy_clipboard:
            ClipboardManager.copy(extracted_text)
        if notify:
            NotificationManager.notify_success(extracted_text)
        if print_stdout:
            print(extracted_text)
    else:
        if notify:
            NotificationManager.notify_no_text()
        logger.info("No text detected in selection.")

    return extracted_text


def main() -> None:
    args = parse_args()

    # Configure structured logging
    setup_logging(debug=args.debug, verbose=args.verbose)

    # 1. Load configuration from XDG location
    config_mgr = ConfigManager()
    cfg = config_mgr.load_config()

    # 2. Resolve settings with CLI > Config > Factory Default precedence
    # OCR Language
    lang = args.lang if args.lang is not None else cfg.get("ocr", {}).get("default_language", "eng")

    # OCR PSM
    psm = args.psm if args.psm is not None else cfg.get("ocr", {}).get("default_psm", 6)

    # OCR Scaling
    if args.scale is not None:
        scale = args.scale
    else:
        adaptive = cfg.get("ocr", {}).get("enable_adaptive_scaling", True)
        scale = 3.0 if adaptive else 1.0

    # Operation Mode (Instant vs Review & Edit)
    if args.edit:
        edit_mode = True
    elif args.instant:
        edit_mode = False
    else:
        edit_mode = (cfg.get("general", {}).get("default_mode", "instant") == "edit")

    # Notifications
    if args.no_notify:
        notify = False
    elif args.notify:
        notify = True
    else:
        notify = cfg.get("general", {}).get("show_notifications", True)

    # Clipboard copy
    if args.no_copy:
        copy_clipboard = False
    elif args.copy:
        copy_clipboard = True
    else:
        copy_clipboard = cfg.get("general", {}).get("auto_copy_to_clipboard", True)

    # Determine input source: file or live screen capture
    temp_capture = False
    target_image_path: Optional[str] = None
    if args.file:
        target_image_path = os.path.abspath(args.file)
    else:
        # Interactive screen capture
        try:
            target_image_path = ScreenCapture.capture_interactive()
        except PortalTimeoutError as e:
            logger.error(f"Screen selection timed out: {e}")
            if notify:
                NotificationManager.notify_error("Screen selection timed out.")
            sys.exit(e.exit_code)
        except PortalUnavailableError as e:
            logger.error(f"Capture failed: {e}")
            if notify:
                NotificationManager.notify_error("No screenshot tool available.")
            sys.exit(e.exit_code)
        except GlyphError as e:
            logger.error(f"Capture error: {e}")
            sys.exit(e.exit_code)

        if not target_image_path:
            # User cancelled selection (e.g. pressed ESC)
            sys.exit(0)
        temp_capture = True

    try:
        run_pipeline(
            image_path=target_image_path,
            language=lang,
            psm=psm,
            scale=scale,
            edit_mode=edit_mode,
            notify=notify,
            copy_clipboard=copy_clipboard,
            print_stdout=args.stdout or bool(args.file)
        )
    finally:
        # Guaranteed cleanup of temporary captures across any storage path
        if temp_capture and target_image_path:
            try:
                if os.path.exists(target_image_path):
                    os.remove(target_image_path)
            except OSError as e:
                logger.debug(f"Failed to remove temp capture file {target_image_path}: {e}")


if __name__ == "__main__":
    main()

