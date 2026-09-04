"""
Domain exception hierarchy for Glyph.
Provides structured, typed errors across all pipeline subsystems.
"""

from typing import Optional


class GlyphError(Exception):
    """Base exception for all Glyph errors."""
    exit_code: int = 1

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class ConfigurationError(GlyphError):
    """Raised when configuration cannot be loaded or is invalid."""
    exit_code: int = 2


class CaptureError(GlyphError):
    """Base exception for screen capture failures."""
    exit_code: int = 3


class PortalTimeoutError(CaptureError):
    """Raised when XDG Desktop Portal fails to respond within the timeout threshold."""
    exit_code: int = 4


class PortalCancelledError(CaptureError):
    """Raised when user cancels the portal screen capture request."""
    exit_code: int = 0


class PortalUnavailableError(CaptureError):
    """Raised when no compatible portal or capture backend is available."""
    exit_code: int = 5


class PreprocessError(GlyphError):
    """Base exception for image preprocessing errors."""
    exit_code: int = 6


class ImageValidationError(PreprocessError):
    """Raised when image format is invalid, corrupt, or empty."""
    exit_code: int = 7


class DimensionLimitExceededError(PreprocessError):
    """Raised when image dimensions or pixel budget exceeds safety limits."""
    exit_code: int = 8


class OCRError(GlyphError):
    """Base exception for OCR engine failures."""
    exit_code: int = 9


class EngineNotFoundError(OCRError):
    """Raised when a requested OCR engine is not installed or found in PATH."""
    exit_code: int = 10


class RecognitionFailedError(OCRError):
    """Raised when OCR recognition fails critically."""
    exit_code: int = 11


class ClipboardError(GlyphError):
    """Raised when copying to clipboard fails."""
    exit_code: int = 12

