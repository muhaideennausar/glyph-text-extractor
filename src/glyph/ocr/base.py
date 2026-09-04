"""
Base contract for pluggable OCR engines.
"""

from abc import ABC, abstractmethod
from typing import List
from PIL import Image


class BaseOCREngine(ABC):
    """Abstract base class defining the contract for any OCR backend."""

    name: str = "base"
    display_name: str = "Base OCR"
    description: str = "Base OCR interface"

    @abstractmethod
    def extract_text(self, image: Image.Image, **kwargs) -> str:
        """Extract text from a PIL Image instance."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine's dependencies are installed on the host system."""
        pass

    def get_supported_languages(self) -> List[str]:
        """Returns a list of supported language codes."""
        return ["eng"]

