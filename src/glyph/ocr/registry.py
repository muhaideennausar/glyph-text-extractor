"""
Registry and factory for pluggable OCR engines.
"""

from typing import Dict, Type
from glyph.ocr.base import BaseOCREngine
from glyph.errors import EngineNotFoundError


class OCREngineRegistry:
    """Registry and factory for pluggable OCR engines."""

    _registry: Dict[str, Type[BaseOCREngine]] = {}

    @classmethod
    def register(cls, engine_cls: Type[BaseOCREngine]) -> None:
        cls._registry[engine_cls.name] = engine_cls

    @classmethod
    def get_engine(cls, name: str = "tesseract", **kwargs) -> BaseOCREngine:
        if name not in cls._registry:
            raise EngineNotFoundError(
                f"Unknown OCR engine '{name}'.",
                details=f"Available engines: {list(cls._registry.keys())}"
            )
        engine_cls = cls._registry[name]
        return engine_cls(**kwargs)

    @classmethod
    def list_engines(cls) -> Dict[str, Dict[str, str]]:
        return {
            name: {
                "display_name": cls._registry[name].display_name,
                "description": cls._registry[name].description,
            }
            for name in cls._registry
        }

