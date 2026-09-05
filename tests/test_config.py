"""
Automated unit tests for Glyph configuration management and XDG compliance.
"""

import json
import os
import stat
import sys
import tempfile
import unittest

# Ensure src directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from glyph.config import ConfigManager, DEFAULT_CONFIG


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "glyph", "config.json")
        self.manager = ConfigManager(config_path=self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_config_creation(self):
        """Tests that missing config file is automatically generated with defaults."""
        self.assertFalse(os.path.exists(self.config_path))
        cfg = self.manager.load_config()

        self.assertTrue(os.path.exists(self.config_path))
        self.assertEqual(cfg["version"], 2)
        self.assertEqual(cfg["general"]["default_mode"], "edit")
        self.assertEqual(cfg["ocr"]["default_language"], "eng")
        self.assertEqual(cfg["ocr"]["default_psm"], 3)

        # Verify 0o600 file permissions
        file_stat = os.stat(self.config_path)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o600)

    def test_partial_config_deep_merge(self):
        """Tests that a partial user configuration is cleanly merged with defaults."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        partial = {
            "general": {
                "default_mode": "instant"
            },
            "ocr": {
                "default_language": "deu"
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(partial, f)

        cfg = self.manager.load_config()

        # Overridden values
        self.assertEqual(cfg["general"]["default_mode"], "instant")
        self.assertEqual(cfg["ocr"]["default_language"], "deu")

        # Retained factory defaults
        self.assertTrue(cfg["general"]["auto_copy_to_clipboard"])
        self.assertTrue(cfg["general"]["show_notifications"])
        self.assertEqual(cfg["ocr"]["default_psm"], 3)
        self.assertEqual(cfg["editor"]["window_width"], 640)

    def test_corrupt_json_fallback(self):
        """Tests graceful recovery to factory defaults when config.json is corrupt."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{invalid_json: true, unterminated string...")

        cfg = self.manager.load_config()
        self.assertEqual(cfg["general"]["default_mode"], "edit")
        self.assertEqual(cfg["ocr"]["default_language"], "eng")

    def test_sanitization_of_invalid_values(self):
        """Tests that invalid options are sanitized to safe defaults."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        invalid_data = {
            "general": {
                "default_mode": "unsupported_mode"
            },
            "ocr": {
                "default_psm": 999
            },
            "editor": {
                "window_width": 20  # below minimum 300
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        cfg = self.manager.load_config()
        self.assertEqual(cfg["general"]["default_mode"], "edit")
        self.assertEqual(cfg["ocr"]["default_psm"], 3)
        self.assertEqual(cfg["editor"]["window_width"], 640)

    def test_editor_window_size_persistence(self):
        """Tests that window geometry is updated and persisted."""
        self.manager.load_config()
        self.manager.update_editor_window_size(800, 500)

        updated_cfg = self.manager.load_config()
        self.assertEqual(updated_cfg["editor"]["window_width"], 800)
        self.assertEqual(updated_cfg["editor"]["window_height"], 500)

    def test_v1_to_v2_migration(self):
        """Tests that a version 1 config file with default_mode instant is migrated to edit."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        v1_data = {
            "version": 1,
            "general": {
                "default_mode": "instant"
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(v1_data, f)

        cfg = self.manager.load_config()
        self.assertEqual(cfg["version"], 2)
        self.assertEqual(cfg["general"]["default_mode"], "edit")


if __name__ == "__main__":
    unittest.main(verbosity=2)

