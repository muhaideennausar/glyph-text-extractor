"""
Glyph core application coordinator and command-line interface.
"""

import os
import sys
import argparse
import logging
from typing import Optional

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


class GlyphVersionAction(argparse.Action):
    """Custom version action providing cross-distro diagnostic info if shadowed."""
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help="Show program's version number and exit."):
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        import glyph
        print(f"{__app_name__} {__version__}")
        loaded_path = os.path.abspath(glyph.__file__)
        sys_bin = "/usr/bin/glyph"
        local_bin = os.path.expanduser("~/.local/bin/glyph")
        if os.path.isfile(sys_bin) and os.path.isfile(local_bin):
            if "/.local/" in loaded_path:
                sys.stderr.write(
                    f"\n[Note] Running user installation from {os.path.dirname(loaded_path)}.\n"
                    f"       A system package is also installed at {sys_bin}.\n"
                    f"       Run './uninstall.sh' or remove '{local_bin}' to use the system package.\n"
                )
        sys.exit(0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description="Glyph - Text Extractor: High-performance Linux screen text extractor (PowerToys Text Extractor clone)."
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
        "--setup-shortcuts",
        action="store_true",
        help="Interactively configure global desktop shortcuts with collision detection."
    )
    parser.add_argument(
        "--remove-shortcuts",
        action="store_true",
        help="Remove registered Glyph global desktop shortcuts."
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Automatic yes to prompts (non-interactive mode)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--version", "-v",
        action=GlyphVersionAction
    )
    return parser.parse_args()


def run_pipeline(
    image_path: str,
    language: str = "eng",
    psm: Optional[int] = None,
    scale: float = 3.0,
    edit_mode: bool = False,
    notify: bool = True,
    copy_clipboard: bool = True,
    print_stdout: bool = True,
    enhance_edges: bool = True,
    auto_psm: bool = True
) -> str:
    """Executes the preprocessor -> OCR -> clipboard -> notification pipeline."""
    try:
        # 1. Preprocess image with defensive validation and edge enhancement
        processed_image = ImagePreprocessor.process(
            image_path,
            scale_factor=scale,
            enhance_edges=enhance_edges
        )
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

    # 2. Extract text via Tesseract with smart layout detection & fallback cascade
    engine = OCREngine(language=language, default_psm=(psm if psm is not None else 6))
    extracted_text = engine.extract_text(
        processed_image,
        psm=psm,
        auto_psm=(auto_psm and psm is None)
    )

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


def check_runtime_dependencies() -> None:
    """Verifies that core runtime dependencies are available before pipeline execution."""
    missing = []
    try:
        import PIL
    except ImportError:
        missing.append("Pillow (PIL)")

    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
    except (ImportError, ValueError):
        missing.append("PyGObject / GTK4 / Libadwaita")

    if missing:
        sys.stderr.write(
            f"Error: Missing required Python dependencies: {', '.join(missing)}\n\n"
            "  • openSUSE:      sudo zypper install python3-Pillow python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 tesseract-ocr tesseract-ocr-traineddata-english wl-clipboard\n"
            "  • Fedora:        sudo dnf install python3-pillow python3-gobject gtk4 libadwaita tesseract\n"
            "  • Debian/Ubuntu: sudo apt install python3-pil python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 tesseract-ocr\n"
            "  • Arch Linux:    sudo pacman -S python-pillow python-gobject gtk4 libadwaita tesseract\n\n"
        )
        sys.exit(1)


def main() -> None:
    args = parse_args()

    # Configure structured logging
    setup_logging(debug=args.debug, verbose=args.verbose)

    # Shortcut management commands
    if args.setup_shortcuts:
        from glyph.shortcuts import setup_global_shortcuts
        success = setup_global_shortcuts(auto_yes=args.yes)
        sys.exit(0 if success else 1)

    if args.remove_shortcuts:
        from glyph.shortcuts import remove_global_shortcuts
        remove_global_shortcuts()
        sys.exit(0)

    # Verify runtime dependencies before executing capture or pipeline
    check_runtime_dependencies()

    # 1. Load configuration from XDG location
    config_mgr = ConfigManager()
    cfg = config_mgr.load_config()

    # 2. Resolve settings with CLI > Config > Factory Default precedence
    # OCR Language
    lang = args.lang if args.lang is not None else cfg.get("ocr", {}).get("default_language", "eng")

    # OCR PSM & Smart Detection
    psm = args.psm if args.psm is not None else None
    smart_psm = cfg.get("ocr", {}).get("smart_psm", True)
    enhance_edges = cfg.get("ocr", {}).get("enhance_edges", True)

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
        edit_mode = (cfg.get("general", {}).get("default_mode", "edit") == "edit")

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
            print_stdout=args.stdout or bool(args.file),
            enhance_edges=enhance_edges,
            auto_psm=smart_psm
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

