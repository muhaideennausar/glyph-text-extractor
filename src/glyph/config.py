"""
XDG Base Directory compliant configuration manager for Glyph.
Handles reading, writing, schema validation, and persistence of user preferences.
"""

import copy
import json
import logging
import os
import tempfile
from typing import Any, Dict, Optional

from glyph.errors import ConfigurationError

logger = logging.getLogger("glyph.config")

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 2,
    "general": {
        "default_mode": "edit",
        "auto_copy_to_clipboard": True,
        "show_notifications": True,
    },
    "ocr": {
        "default_engine": "tesseract",
        "default_language": "eng",
        "default_psm": 3,
        "enable_adaptive_scaling": True,
        "smart_psm": True,
        "enhance_edges": False,
        "preserve_spaces": True,
    },
    "editor": {
        "window_width": 640,
        "window_height": 440,
        "remember_window_size": True,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges override dictionary into a deep copy of base dictionary."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class ConfigManager:
    """Manages Glyph configuration in compliance with XDG specifications."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = os.path.abspath(config_path)
            self.config_dir = os.path.dirname(self.config_path)
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
            self.config_dir = os.path.join(xdg_config, "glyph")
            self.config_path = os.path.join(self.config_dir, "config.json")

        xdg_cache = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
        self.cache_dir = os.path.join(xdg_cache, "glyph")

    def get_config_path(self) -> str:
        return self.config_path

    def get_cache_dir(self) -> str:
        return self.cache_dir

    def ensure_directories(self) -> None:
        """Ensures XDG config and cache directories exist with 0o700 permissions."""
        for directory in (self.config_dir, self.cache_dir):
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, mode=0o700, exist_ok=True)
                except OSError as e:
                    logger.warning(f"Could not create directory {directory}: {e}")

    def load_config(self) -> Dict[str, Any]:
        """
        Loads configuration from disk, creating default if not found.
        Merges with factory defaults to ensure forward-compatibility.
        """
        if not os.path.exists(self.config_path):
            logger.debug(f"Configuration file not found at {self.config_path}. Initializing default.")
            config = copy.deepcopy(DEFAULT_CONFIG)
            try:
                self.save_config(config)
            except Exception as e:
                logger.warning(f"Failed to write initial default configuration: {e}")
            return config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            if not isinstance(raw_data, dict):
                logger.warning("Configuration root is not a dictionary. Falling back to defaults.")
                return copy.deepcopy(DEFAULT_CONFIG)

            # Auto-migrate v1 configs where default_mode was factory-set to "instant"
            if "version" in raw_data and raw_data["version"] < 2:
                if raw_data.get("general", {}).get("default_mode") == "instant":
                    raw_data.setdefault("general", {})["default_mode"] = "edit"
                raw_data["version"] = 2
                try:
                    self.save_config(_deep_merge(DEFAULT_CONFIG, raw_data))
                except Exception:
                    pass

            merged = _deep_merge(DEFAULT_CONFIG, raw_data)
            validated = self._validate_and_sanitize(merged)
            return validated
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupt JSON in {self.config_path}: {e}. Using factory defaults.")
            return copy.deepcopy(DEFAULT_CONFIG)
        except Exception as e:
            logger.warning(f"Error reading configuration {self.config_path}: {e}. Using factory defaults.")
            return copy.deepcopy(DEFAULT_CONFIG)

    def save_config(self, config: Dict[str, Any]) -> None:
        """Atomically saves configuration to disk with 0o600 permissions."""
        self.ensure_directories()
        temp_file = None
        try:
            fd, temp_path = tempfile.mkstemp(prefix="config_", suffix=".tmp", dir=self.config_dir)
            temp_file = temp_path
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                f.write("\n")

            os.chmod(temp_path, 0o600)
            os.replace(temp_path, self.config_path)
            temp_file = None
            logger.debug(f"Saved configuration to {self.config_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {self.config_path}: {e}")
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    def update_editor_window_size(self, width: int, height: int) -> None:
        """Persists window geometry if remember_window_size is enabled."""
        try:
            config = self.load_config()
            if config.get("editor", {}).get("remember_window_size", False):
                config["editor"]["window_width"] = max(300, width)
                config["editor"]["window_height"] = max(200, height)
                self.save_config(config)
        except Exception as e:
            logger.debug(f"Failed to update window dimensions: {e}")

    @staticmethod
    def _validate_and_sanitize(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validates configuration types and sanitizes out-of-bounds values."""
        general = config.get("general", {})
        if general.get("default_mode") not in ("instant", "edit"):
            general["default_mode"] = DEFAULT_CONFIG["general"]["default_mode"]
        if not isinstance(general.get("auto_copy_to_clipboard"), bool):
            general["auto_copy_to_clipboard"] = DEFAULT_CONFIG["general"]["auto_copy_to_clipboard"]
        if not isinstance(general.get("show_notifications"), bool):
            general["show_notifications"] = DEFAULT_CONFIG["general"]["show_notifications"]

        ocr = config.get("ocr", {})
        if not isinstance(ocr.get("default_language"), str) or not ocr["default_language"].strip():
            ocr["default_language"] = DEFAULT_CONFIG["ocr"]["default_language"]
        if not isinstance(ocr.get("default_psm"), int) or not (0 <= ocr["default_psm"] <= 13):
            ocr["default_psm"] = DEFAULT_CONFIG["ocr"]["default_psm"]
        if not isinstance(ocr.get("enable_adaptive_scaling"), bool):
            ocr["enable_adaptive_scaling"] = DEFAULT_CONFIG["ocr"]["enable_adaptive_scaling"]
        if not isinstance(ocr.get("smart_psm"), bool):
            ocr["smart_psm"] = DEFAULT_CONFIG["ocr"]["smart_psm"]
        if not isinstance(ocr.get("enhance_edges"), bool):
            ocr["enhance_edges"] = DEFAULT_CONFIG["ocr"]["enhance_edges"]
        if not isinstance(ocr.get("preserve_spaces"), bool):
            ocr["preserve_spaces"] = DEFAULT_CONFIG["ocr"]["preserve_spaces"]

        editor = config.get("editor", {})
        if not isinstance(editor.get("window_width"), int) or editor["window_width"] < 300:
            editor["window_width"] = DEFAULT_CONFIG["editor"]["window_width"]
        if not isinstance(editor.get("window_height"), int) or editor["window_height"] < 200:
            editor["window_height"] = DEFAULT_CONFIG["editor"]["window_height"]
        if not isinstance(editor.get("remember_window_size"), bool):
            editor["remember_window_size"] = DEFAULT_CONFIG["editor"]["remember_window_size"]

        return config

