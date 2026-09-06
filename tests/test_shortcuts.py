"""Unit tests for the cross-desktop global shortcut manager."""

import os
import unittest
from unittest.mock import MagicMock, patch

from glyph.shortcuts import (
    DEFAULT_SHORTCUTS,
    ConflictDetail,
    GnomeShortcutManager,
    ShortcutTarget,
    bindings_equal,
    detect_desktop_environment,
    normalize_binding,
    prompt_user_for_shortcut,
    setup_global_shortcuts,
)


class TestShortcutNormalization(unittest.TestCase):
    """Tests normalization and semantic equivalence of shortcut key combinations."""

    def test_angle_bracket_gnome_format(self):
        mods, key = normalize_binding("<Super><Shift>t")
        self.assertEqual(mods, frozenset({"super", "shift"}))
        self.assertEqual(key, "t")

    def test_plus_separated_format(self):
        mods, key = normalize_binding("Meta+Shift+T")
        self.assertEqual(mods, frozenset({"super", "shift"}))
        self.assertEqual(key, "t")

    def test_order_invariance(self):
        self.assertTrue(bindings_equal("<Super><Shift>t", "<Shift><Super>t"))
        self.assertTrue(bindings_equal("<Super><Shift>t", "Meta+Shift+T"))
        self.assertTrue(bindings_equal("<Ctrl><Alt>v", "<Alt><Ctrl>v"))
        self.assertTrue(bindings_equal("Control+Alt+V", "<Ctrl><Alt>v"))

    def test_different_keys_not_equal(self):
        self.assertFalse(bindings_equal("<Super><Shift>t", "<Super><Shift>e"))
        self.assertFalse(bindings_equal("<Super><Shift>t", "<Ctrl><Shift>t"))


class TestDesktopDetection(unittest.TestCase):
    """Tests desktop environment detection based on environment variables."""

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"})
    def test_gnome_detection(self):
        self.assertEqual(detect_desktop_environment(), "gnome")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_kde_detection(self):
        self.assertEqual(detect_desktop_environment(), "kde")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "X-Cinnamon"})
    def test_cinnamon_detection(self):
        self.assertEqual(detect_desktop_environment(), "cinnamon")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "XFCE"})
    def test_xfce_detection(self):
        self.assertEqual(detect_desktop_environment(), "xfce")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "Hyprland"})
    def test_hyprland_detection(self):
        self.assertEqual(detect_desktop_environment(), "hyprland")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "sway"})
    def test_sway_detection(self):
        self.assertEqual(detect_desktop_environment(), "sway")


class TestShortcutPromptLogic(unittest.TestCase):
    """Tests permission prompt logic for both collision and clean registration."""

    def setUp(self):
        self.target = ShortcutTarget(
            identifier="test-shortcut",
            name="Test Tool",
            command="test-tool --grab",
            binding="<Super><Shift>t",
            description="Test description",
        )

    def test_existing_glyph_shortcut_recognized(self):
        conflict = ConflictDetail(
            name="Glyph Text Extractor",
            command="glyph",
            binding="<Super><Shift>t",
            path_or_source="custom0",
        )
        # Should return True without prompting user
        res = prompt_user_for_shortcut(self.target, conflict, auto_yes=False)
        self.assertTrue(res)

    @patch("sys.stdin.readline", return_value="y\n")
    def test_conflict_user_confirms_replacement(self, _mock_stdin):
        conflict = ConflictDetail(
            name="Other App",
            command="other-app --capture",
            binding="<Super><Shift>t",
            path_or_source="custom99",
        )
        res = prompt_user_for_shortcut(self.target, conflict, auto_yes=False)
        self.assertTrue(res)

    @patch("sys.stdin.readline", return_value="n\n")
    def test_conflict_user_declines_replacement(self, _mock_stdin):
        conflict = ConflictDetail(
            name="Other App",
            command="other-app --capture",
            binding="<Super><Shift>t",
            path_or_source="custom99",
        )
        res = prompt_user_for_shortcut(self.target, conflict, auto_yes=False)
        self.assertFalse(res)

    @patch("sys.stdin.readline", return_value="\n")
    def test_no_conflict_user_accepts_default(self, _mock_stdin):
        res = prompt_user_for_shortcut(self.target, None, auto_yes=False)
        self.assertTrue(res)

    @patch("sys.stdin.readline", return_value="n\n")
    def test_no_conflict_user_declines_append(self, _mock_stdin):
        res = prompt_user_for_shortcut(self.target, None, auto_yes=False)
        self.assertFalse(res)

    def test_auto_yes_skips_external_conflict(self):
        conflict = ConflictDetail(
            name="Other App",
            command="other-app --capture",
            binding="<Super><Shift>t",
            path_or_source="custom99",
        )
        res = prompt_user_for_shortcut(self.target, conflict, auto_yes=True)
        self.assertFalse(res)


class TestGnomeShortcutManager(unittest.TestCase):
    """Tests GNOME gsettings interaction with mocking."""

    @patch("shutil.which", return_value="/usr/bin/gsettings")
    @patch("subprocess.check_output")
    def test_find_conflict_detected(self, mock_output, _mock_which):
        # 1. custom-keybindings list
        # 2. name of path 1
        # 3. command of path 1
        # 4. binding of path 1
        mock_output.side_effect = [
            b"['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']",
            b"'My Old Tool'",
            b"'old-tool-cmd'",
            b"'<Shift><Super>t'",
        ]
        conflict = GnomeShortcutManager.find_conflict("<Super><Shift>t")
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.name, "My Old Tool")
        self.assertEqual(conflict.command, "old-tool-cmd")


class TestKdeShortcutManager(unittest.TestCase):
    """Tests KDE Plasma shortcut management, key sequence conversion, and action mappings."""

    def test_to_kde_binding_conversion(self):
        from glyph.shortcuts import to_kde_binding
        self.assertEqual(to_kde_binding("<Super><Shift>t"), "Meta+Shift+T")
        self.assertEqual(to_kde_binding("<Super><Shift>i"), "Meta+Shift+I")
        self.assertEqual(to_kde_binding("<Ctrl><Alt>v"), "Ctrl+Alt+V")
        self.assertEqual(to_kde_binding("<Super>e"), "Meta+E")

    @patch("shutil.which", return_value="/usr/bin/kwriteconfig6")
    @patch("subprocess.check_call")
    def test_set_shortcut_mode_b_registers_launch_and_editor(self, mock_check_call, _mock_which):
        from glyph.shortcuts import KdeShortcutManager
        target = ShortcutTarget(
            identifier="glyph-mode-b",
            name="Glyph - Review & Edit",
            command="glyph --grab",
            binding="<Super><Shift>t",
            description="Mode B Review & Edit",
        )
        success = KdeShortcutManager.set_shortcut(target)
        self.assertTrue(success)

        # Check call arguments
        calls = [c[0][0] for c in mock_check_call.call_args_list]
        groups = [c[c.index("--group") + 1] for c in calls if "--group" in c]
        keys = [c[c.index("--key") + 1] for c in calls if "--key" in c]

        self.assertIn("io.github.muhaideennausar.Glyph.desktop", groups)
        self.assertIn("services", groups)
        self.assertIn("glyph-mode-b.desktop", groups)
        self.assertIn("_k_friendly_name", keys)
        self.assertIn("_launch", keys)
        self.assertIn("Editor", keys)

    @patch("shutil.which", return_value="/usr/bin/kwriteconfig6")
    @patch("subprocess.check_call")
    def test_set_shortcut_mode_a_registers_instant(self, mock_check_call, _mock_which):
        from glyph.shortcuts import KdeShortcutManager
        target = ShortcutTarget(
            identifier="glyph-mode-a",
            name="Glyph - Instant Text Extractor",
            command="glyph --grab --instant",
            binding="<Super><Shift>i",
            description="Mode A Instant",
        )
        success = KdeShortcutManager.set_shortcut(target)
        self.assertTrue(success)

        calls = [c[0][0] for c in mock_check_call.call_args_list]
        keys = [c[c.index("--key") + 1] for c in calls if "--key" in c]
        self.assertIn("Instant", keys)

    @patch("shutil.which", return_value="/usr/bin/kwriteconfig6")
    @patch("subprocess.check_call")
    def test_remove_shortcuts_kde(self, mock_check_call, _mock_which):
        from glyph.shortcuts import KdeShortcutManager
        res = KdeShortcutManager.remove_shortcuts()
        self.assertTrue(res)

        calls = [c[0][0] for c in mock_check_call.call_args_list]
        keys = [c[c.index("--key") + 1] for c in calls if "--key" in c]
        self.assertIn("_launch", keys)
        self.assertIn("Editor", keys)
        self.assertIn("Instant", keys)


if __name__ == "__main__":
    unittest.main()
