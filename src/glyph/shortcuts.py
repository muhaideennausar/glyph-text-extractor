"""Cross-desktop global shortcut manager for Linux environments.

Supports GNOME, KDE Plasma, Cinnamon, MATE, XFCE, and tiling WMs (Hyprland, Sway, i3).
Performs intelligent collision detection with existing shortcuts and prompts the
user for permission before creating or modifying shortcuts.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ShortcutTarget:
    """Represents a shortcut Glyph wishes to register."""
    identifier: str
    name: str
    command: str
    binding: str  # e.g. "<Super><Shift>t"
    description: str


@dataclass
class ConflictDetail:
    """Details of an existing shortcut colliding with a proposed target."""
    name: str
    command: str
    binding: str
    path_or_source: str


def _resolve_glyph_binary() -> str:
    """Finds the absolute path to the glyph binary to ensure desktop daemons find it."""
    # 1. If currently executing from a specific executable path, prioritize it
    if sys.argv and sys.argv[0]:
        argv0 = sys.argv[0]
        if os.path.isabs(argv0) and os.path.isfile(argv0) and os.access(argv0, os.X_OK):
            return argv0
        which_argv0 = shutil.which(argv0)
        if which_argv0 and os.path.isabs(which_argv0) and os.access(which_argv0, os.X_OK):
            return which_argv0

    # 2. Check candidates in order: system binary, standard local, or PATH
    for candidate in [
        "/usr/bin/glyph",
        "/usr/local/bin/glyph",
        shutil.which("glyph"),
        os.path.expanduser("~/.local/bin/glyph"),
    ]:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "glyph"


_GLYPH_BIN = _resolve_glyph_binary()

DEFAULT_SHORTCUTS = [
    ShortcutTarget(
        identifier="glyph-mode-b",
        name="Glyph - Review & Edit",
        command=f"{_GLYPH_BIN} --grab",
        binding="<Super><Shift>t",
        description="Mode B Interactive Review & Edit modal (Default)",
    ),
    ShortcutTarget(
        identifier="glyph-mode-a",
        name="Glyph - Instant Text Extractor",
        command=f"{_GLYPH_BIN} --grab --instant",
        binding="<Super><Shift>i",
        description="Instant Mode A Screen OCR directly to clipboard",
    ),
]


def normalize_binding(binding: str) -> Tuple[FrozenSet[str], str]:
    """Normalizes key combinations to compare them irrespective of modifier ordering.

    Examples:
        '<Super><Shift>t'  -> (frozenset({'super', 'shift'}), 't')
        '<Shift><Super>t'  -> (frozenset({'super', 'shift'}), 't')
        'Meta+Shift+T'     -> (frozenset({'super', 'shift'}), 't')
        'Ctrl+Alt+V'       -> (frozenset({'ctrl', 'alt'}), 'v')
    """
    cleaned = binding.strip().lower()

    # Convert GNOME angle-bracket format: <Super><Shift>t -> super+shift+t
    if "<" in cleaned:
        cleaned = re.sub(r"<([^>]+)>", r"\1+", cleaned)

    parts = [p.strip() for p in cleaned.split("+") if p.strip()]
    if not parts:
        return frozenset(), ""

    modifiers: set[str] = set()
    key = parts[-1]

    mod_mapping = {
        "ctrl": "ctrl",
        "control": "ctrl",
        "primary": "ctrl",
        "alt": "alt",
        "mod1": "alt",
        "shift": "shift",
        "super": "super",
        "mod4": "super",
        "meta": "super",
        "hyper": "hyper",
    }

    for p in parts[:-1]:
        mod = mod_mapping.get(p, p)
        modifiers.add(mod)

    return frozenset(modifiers), key


def bindings_equal(bind1: str, bind2: str) -> bool:
    """Returns True if two shortcut representations are semantically equivalent."""
    norm1 = normalize_binding(bind1)
    norm2 = normalize_binding(bind2)
    return norm1 == norm2 and norm1[1] != ""


def detect_desktop_environment() -> str:
    """Detects the running Linux desktop environment."""
    xdg_current = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    desktop_session = os.environ.get("DESKTOP_SESSION", "").upper()

    if "GNOME" in xdg_current or "UBUNTU" in xdg_current or "POP" in xdg_current:
        return "gnome"
    if "KDE" in xdg_current or "PLASMA" in xdg_current:
        return "kde"
    if "X-CINNAMON" in xdg_current or "CINNAMON" in xdg_current:
        return "cinnamon"
    if "MATE" in xdg_current:
        return "mate"
    if "XFCE" in xdg_current:
        return "xfce"
    if "HYPRLAND" in xdg_current:
        return "hyprland"
    if "SWAY" in xdg_current:
        return "sway"
    if "I3" in xdg_current:
        return "i3"

    if "GNOME" in desktop_session:
        return "gnome"
    if "KDE" in desktop_session or "PLASMA" in desktop_session:
        return "kde"

    return "unknown"


class GnomeShortcutManager:
    """Handles global shortcut management on GNOME, Ubuntu, and Pop!_OS via gsettings."""

    SCHEMA_ROOT = "org.gnome.settings-daemon.plugins.media-keys"
    SCHEMA_CUSTOM = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
    PATH_PREFIX = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("gsettings") is not None

    @classmethod
    def get_custom_bindings(cls) -> List[Dict[str, str]]:
        """Returns all currently registered GNOME custom keybindings."""
        if not cls.is_available():
            return []
        try:
            out = subprocess.check_output(
                ["gsettings", "get", cls.SCHEMA_ROOT, "custom-keybindings"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            return []

        paths = re.findall(r"'([^']+)'", out)
        bindings = []
        for path in paths:
            try:
                name = subprocess.check_output(
                    ["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "name"],
                    stderr=subprocess.DEVNULL,
                ).decode().strip().strip("'")
                cmd = subprocess.check_output(
                    ["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "command"],
                    stderr=subprocess.DEVNULL,
                ).decode().strip().strip("'")
                bind = subprocess.check_output(
                    ["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "binding"],
                    stderr=subprocess.DEVNULL,
                ).decode().strip().strip("'")
                bindings.append({
                    "path": path,
                    "name": name,
                    "command": cmd,
                    "binding": bind,
                })
            except Exception:
                continue
        return bindings

    @classmethod
    def find_conflict(cls, target_binding: str) -> Optional[ConflictDetail]:
        """Checks if a key combination is already assigned to a GNOME custom keybinding."""
        for b in cls.get_custom_bindings():
            if bindings_equal(b["binding"], target_binding):
                return ConflictDetail(
                    name=b["name"],
                    command=b["command"],
                    binding=b["binding"],
                    path_or_source=b["path"],
                )
        return None

    @classmethod
    def set_shortcut(cls, target: ShortcutTarget, replace_path: Optional[str] = None) -> bool:
        """Registers or replaces a custom shortcut in GNOME."""
        if not cls.is_available():
            return False

        path = replace_path or f"{cls.PATH_PREFIX}/{target.identifier}/"

        try:
            # Set name, command, binding
            subprocess.check_call(
                ["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "name", target.name],
                stderr=subprocess.DEVNULL,
            )
            subprocess.check_call(
                ["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "command", target.command],
                stderr=subprocess.DEVNULL,
            )
            subprocess.check_call(
                ["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "binding", target.binding],
                stderr=subprocess.DEVNULL,
            )

            # Ensure path is present in the list
            out = subprocess.check_output(
                ["gsettings", "get", cls.SCHEMA_ROOT, "custom-keybindings"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()

            existing_paths = re.findall(r"'([^']+)'", out)
            if path not in existing_paths:
                existing_paths.append(path)
                formatted = "[" + ", ".join(f"'{p}'" for p in existing_paths) + "]"
                subprocess.check_call(
                    ["gsettings", "set", cls.SCHEMA_ROOT, "custom-keybindings", formatted],
                    stderr=subprocess.DEVNULL,
                )

            # Pre-grant silent screenshot permission in XDG PermissionStore for GNOME Wayland
            try:
                from glyph.capture import ensure_portal_screenshot_permission
                ensure_portal_screenshot_permission()
            except Exception:
                pass

            return True
        except Exception as e:
            logger.error(f"Failed to set GNOME shortcut {target.identifier}: {e}")
            return False

    @classmethod
    def remove_shortcuts(cls) -> bool:
        """Removes all Glyph shortcuts from GNOME."""
        if not cls.is_available():
            return False
        try:
            out = subprocess.check_output(
                ["gsettings", "get", cls.SCHEMA_ROOT, "custom-keybindings"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            existing_paths = re.findall(r"'([^']+)'", out)
            kept_paths = []
            for path in existing_paths:
                try:
                    cmd = subprocess.check_output(
                        ["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "command"],
                        stderr=subprocess.DEVNULL,
                    ).decode().strip().strip("'")
                    if "glyph" in cmd.lower() or "glyph-mode" in path:
                        # Clear properties
                        subprocess.call(["gsettings", "reset-recursively", f"{cls.SCHEMA_CUSTOM}:{path}"], stderr=subprocess.DEVNULL)
                    else:
                        kept_paths.append(path)
                except Exception:
                    kept_paths.append(path)

            formatted = "[" + ", ".join(f"'{p}'" for p in kept_paths) + "]"
            subprocess.check_call(
                ["gsettings", "set", cls.SCHEMA_ROOT, "custom-keybindings", formatted],
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to remove GNOME shortcuts: {e}")
            return False


class CinnamonShortcutManager:
    """Handles global shortcut management on Cinnamon (Linux Mint)."""

    SCHEMA_ROOT = "org.cinnamon.desktop.keybindings"
    SCHEMA_CUSTOM = "org.cinnamon.desktop.keybindings.custom-keybinding"
    PATH_PREFIX = "/org/cinnamon/desktop/keybindings/custom-keybindings"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("gsettings") is not None

    @classmethod
    def find_conflict(cls, target_binding: str) -> Optional[ConflictDetail]:
        if not cls.is_available():
            return None
        try:
            out = subprocess.check_output(
                ["gsettings", "get", cls.SCHEMA_ROOT, "custom-list"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            return None

        entries = re.findall(r"'([^']+)'", out)
        for entry in entries:
            path = f"{cls.PATH_PREFIX}/{entry}/"
            try:
                name = subprocess.check_output(["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "name"], stderr=subprocess.DEVNULL).decode().strip().strip("'")
                cmd = subprocess.check_output(["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "command"], stderr=subprocess.DEVNULL).decode().strip().strip("'")
                raw_bind = subprocess.check_output(["gsettings", "get", f"{cls.SCHEMA_CUSTOM}:{path}", "binding"], stderr=subprocess.DEVNULL).decode().strip()
                bind_match = re.findall(r"'([^']+)'", raw_bind)
                for b in bind_match:
                    if bindings_equal(b, target_binding):
                        return ConflictDetail(name=name, command=cmd, binding=b, path_or_source=path)
            except Exception:
                continue
        return None

    @classmethod
    def set_shortcut(cls, target: ShortcutTarget, replace_path: Optional[str] = None) -> bool:
        if not cls.is_available():
            return False
        entry_id = replace_path.split("/")[-2] if replace_path else target.identifier
        path = f"{cls.PATH_PREFIX}/{entry_id}/"
        try:
            subprocess.check_call(["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "name", target.name], stderr=subprocess.DEVNULL)
            subprocess.check_call(["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "command", target.command], stderr=subprocess.DEVNULL)
            subprocess.check_call(["gsettings", "set", f"{cls.SCHEMA_CUSTOM}:{path}", "binding", f"['{target.binding}']"], stderr=subprocess.DEVNULL)

            out = subprocess.check_output(["gsettings", "get", cls.SCHEMA_ROOT, "custom-list"], stderr=subprocess.DEVNULL).decode().strip()
            entries = re.findall(r"'([^']+)'", out)
            if entry_id not in entries:
                entries.append(entry_id)
                formatted = "[" + ", ".join(f"'{e}'" for e in entries) + "]"
                subprocess.check_call(["gsettings", "set", cls.SCHEMA_ROOT, "custom-list", formatted], stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.error(f"Failed to set Cinnamon shortcut: {e}")
            return False


class XfceShortcutManager:
    """Handles global shortcut management on XFCE via xfconf-query."""

    CHANNEL = "xfce4-keyboard-shortcuts"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("xfconf-query") is not None

    @classmethod
    def find_conflict(cls, target_binding: str) -> Optional[ConflictDetail]:
        if not cls.is_available():
            return None
        # Convert <Super><Shift>t to XFCE format: <Super><Shift>t
        prop = f"/commands/custom/{target_binding}"
        try:
            cmd = subprocess.check_output(
                ["xfconf-query", "-c", cls.CHANNEL, "-p", prop],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            if cmd:
                return ConflictDetail(name="XFCE Custom Shortcut", command=cmd, binding=target_binding, path_or_source=prop)
        except Exception:
            pass
        return None

    @classmethod
    def set_shortcut(cls, target: ShortcutTarget, replace_path: Optional[str] = None) -> bool:
        if not cls.is_available():
            return False
        prop = replace_path or f"/commands/custom/{target.binding}"
        try:
            subprocess.check_call(
                ["xfconf-query", "-c", cls.CHANNEL, "-p", prop, "-n", "-t", "string", "-s", target.command],
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set XFCE shortcut: {e}")
            return False


def to_kde_binding(binding: str) -> str:
    """Converts a binding (e.g. '<Super><Shift>t') to Qt/KDE KeySequence format (e.g. 'Meta+Shift+T')."""
    b = binding
    b = re.sub(r"<Super>", "Meta+", b, flags=re.IGNORECASE)
    b = re.sub(r"<Shift>", "Shift+", b, flags=re.IGNORECASE)
    b = re.sub(r"<Ctrl>", "Ctrl+", b, flags=re.IGNORECASE)
    b = re.sub(r"<Alt>", "Alt+", b, flags=re.IGNORECASE)
    b = b.replace("<", "").replace(">", "")
    b = b.replace("meta+", "Meta+").replace("shift+", "Shift+").replace("ctrl+", "Ctrl+").replace("alt+", "Alt+")
    parts = b.split("+")
    if parts and len(parts[-1]) == 1:
        parts[-1] = parts[-1].upper()
    return "+".join(parts)


class KdeShortcutManager:
    """Handles global shortcut management on KDE Plasma 5 and 6."""

    CONFIG_PATH = Path.home() / ".config" / "kglobalshortcutsrc"
    DESKTOP_ENTRY = "io.github.muhaideennausar.Glyph.desktop"

    @classmethod
    def is_available(cls) -> bool:
        return cls.CONFIG_PATH.exists() or shutil.which("kwriteconfig6") is not None or shutil.which("kwriteconfig5") is not None

    @classmethod
    def find_conflict(cls, target_binding: str) -> Optional[ConflictDetail]:
        if not cls.CONFIG_PATH.exists():
            return None
        try:
            content = cls.CONFIG_PATH.read_text(encoding="utf-8", errors="ignore")
            # Look for lines like: action=Meta+Shift+T,none,Description
            norm_target = normalize_binding(target_binding)
            for line in content.splitlines():
                if "=" in line and ("Meta" in line or "Ctrl" in line or "Alt" in line):
                    k, v = line.split("=", 1)
                    parts = v.split(",")
                    if parts:
                        b = parts[0].strip()
                        if normalize_binding(b) == norm_target:
                            return ConflictDetail(name=k.strip(), command=v.strip(), binding=b, path_or_source=str(cls.CONFIG_PATH))
        except Exception:
            pass
        return None

    @classmethod
    def _run_kwriteconfig(cls, kwrite: str, group: str, key: str, value: str) -> bool:
        """Executes kwriteconfig6/5 with --notify if supported, falling back without."""
        # Try with --notify first (supported on kwriteconfig6)
        try:
            subprocess.check_call(
                [kwrite, "--file", "kglobalshortcutsrc", "--group", group, "--key", key, "--notify", value],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass
        try:
            subprocess.check_call(
                [kwrite, "--file", "kglobalshortcutsrc", "--group", group, "--key", key, value],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    @classmethod
    def _run_kwriteconfig_delete(cls, kwrite: str, group: str, key: str) -> None:
        """Deletes a key from kglobalshortcutsrc."""
        for args in [
            [kwrite, "--file", "kglobalshortcutsrc", "--group", group, "--key", key, "--delete", "--notify"],
            [kwrite, "--file", "kglobalshortcutsrc", "--group", group, "--key", key, "--delete"],
        ]:
            try:
                subprocess.check_call(args, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                break
            except Exception:
                continue

    @classmethod
    def _ensure_desktop_file(cls) -> None:
        """Ensures io.github.muhaideennausar.Glyph.desktop exists in application paths for KDE."""
        user_apps = Path.home() / ".local" / "share" / "applications"
        user_desktop = user_apps / cls.DESKTOP_ENTRY
        sys_desktop = Path(f"/usr/share/applications/{cls.DESKTOP_ENTRY}")

        if sys_desktop.exists() or user_desktop.exists():
            return

        bundled = Path(__file__).resolve().parent.parent.parent / "data" / cls.DESKTOP_ENTRY
        if bundled.exists():
            try:
                user_apps.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundled, user_desktop)
                if shutil.which("update-desktop-database"):
                    subprocess.run(["update-desktop-database", str(user_apps)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception as e:
                logger.debug(f"Could not copy desktop file for KDE: {e}")

    @classmethod
    def set_shortcut(cls, target: ShortcutTarget, replace_path: Optional[str] = None) -> bool:
        kwrite = shutil.which("kwriteconfig6") or shutil.which("kwriteconfig5")
        if not kwrite:
            return False

        cls._ensure_desktop_file()
        kde_binding = to_kde_binding(target.binding)
        group = cls.DESKTOP_ENTRY

        # 1. Set friendly component name
        cls._run_kwriteconfig(kwrite, group, "_k_friendly_name", "Glyph - Text Extractor")

        # 2. Map desktop actions:
        # Mode B (Review & Edit) maps to _launch and Editor
        # Mode A (Instant Capture) maps to Instant
        val = f"{kde_binding},none,{target.name}"
        if target.identifier == "glyph-mode-b":
            s1 = cls._run_kwriteconfig(kwrite, group, "_launch", val)
            s2 = cls._run_kwriteconfig(kwrite, group, "Editor", val)
            success = s1 or s2
        elif target.identifier == "glyph-mode-a":
            success = cls._run_kwriteconfig(kwrite, group, "Instant", val)
        else:
            success = cls._run_kwriteconfig(kwrite, group, target.identifier, val)

        # 3. Reload KDE daemon if running (Plasma 5)
        if shutil.which("kquitapp5") and shutil.which("kglobalaccel5"):
            try:
                subprocess.run(["kquitapp5", "kglobalaccel"], timeout=2, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.Popen(["kglobalaccel5"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except Exception:
                pass

        return success

    @classmethod
    def remove_shortcuts(cls) -> bool:
        kwrite = shutil.which("kwriteconfig6") or shutil.which("kwriteconfig5")
        if not kwrite:
            return False
        group = cls.DESKTOP_ENTRY
        for key in ["_launch", "Editor", "Instant", "glyph-mode-a", "glyph-mode-b"]:
            cls._run_kwriteconfig_delete(kwrite, group, key)
        return True


def prompt_user_for_shortcut(target: ShortcutTarget, conflict: Optional[ConflictDetail], auto_yes: bool = False) -> bool:
    """Prompts the user in the terminal for permission to register or overwrite a shortcut.

    - If collision detected: Displays conflict details and asks to overwrite.
    - If no collision: Displays proposal and asks for permission to append.
    """
    if conflict and ("glyph" in conflict.command.lower() or "glyph" in conflict.name.lower()):
        print(f"✓ Shortcut already assigned to Glyph: {target.binding} → '{conflict.command}'")
        return True

    if auto_yes:
        # Non-interactive mode (-y / --yes): append if free, do not blindly overwrite collision
        if conflict:
            print(f"[-] Skipping {target.binding}: Conflict detected with existing shortcut '{conflict.name}'")
            return False
        return True

    print("\n" + "=" * 60)
    if conflict:
        print(f"⚠️  SHORTCUT COLLISION DETECTED for {target.binding}!")
        print(f"   Currently claimed by:")
        print(f"     • Name:    {conflict.name}")
        print(f"     • Command: {conflict.command}")
        print(f"     • Source:  {conflict.path_or_source}")
        print(f"\n   Glyph wants to assign it to:")
        print(f"     • {target.name} (`{target.command}`)")
        sys.stdout.write(f"\nDo you want to REPLACE this existing shortcut with Glyph? [y/N]: ")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        return choice in ("y", "yes")
    else:
        print(f"📌 NEW SHORTCUT PROPOSAL:")
        print(f"   • Combination: {target.binding} (Super + Shift + {target.binding[-1].upper()})")
        print(f"   • Action:      {target.name}")
        print(f"   • Command:     `{target.command}`")
        print(f"   • Details:     {target.description}")
        sys.stdout.write(f"\nWould you like to register this global shortcut on your desktop? [Y/n]: ")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        return choice in ("", "y", "yes")


def setup_global_shortcuts(auto_yes: bool = False, desktop_override: Optional[str] = None) -> bool:
    """Configures global shortcuts for Glyph on the detected desktop environment.

    Prompts the user for permission, inspecting and reporting collisions when present.
    """
    desktop = desktop_override or detect_desktop_environment()
    print(f"\n=== Glyph - Text Extractor Global Shortcut Setup ===")
    print(f"Detected Desktop Environment: {desktop.upper()}")

    success_count = 0

    if desktop in ("gnome", "unknown") and GnomeShortcutManager.is_available():
        for target in DEFAULT_SHORTCUTS:
            conflict = GnomeShortcutManager.find_conflict(target.binding)
            if prompt_user_for_shortcut(target, conflict, auto_yes=auto_yes):
                replace_path = conflict.path_or_source if conflict else None
                if GnomeShortcutManager.set_shortcut(target, replace_path=replace_path):
                    print(f"✓ Registered: {target.binding} → {target.command}")
                    success_count += 1
                else:
                    print(f"✗ Failed to register {target.binding}")
            else:
                print(f"[-] Skipped: {target.binding}")

    elif desktop == "cinnamon" and CinnamonShortcutManager.is_available():
        for target in DEFAULT_SHORTCUTS:
            conflict = CinnamonShortcutManager.find_conflict(target.binding)
            if prompt_user_for_shortcut(target, conflict, auto_yes=auto_yes):
                replace_path = conflict.path_or_source if conflict else None
                if CinnamonShortcutManager.set_shortcut(target, replace_path=replace_path):
                    print(f"✓ Registered: {target.binding} → {target.command}")
                    success_count += 1
                else:
                    print(f"✗ Failed to register {target.binding}")
            else:
                print(f"[-] Skipped: {target.binding}")

    elif desktop == "xfce" and XfceShortcutManager.is_available():
        for target in DEFAULT_SHORTCUTS:
            conflict = XfceShortcutManager.find_conflict(target.binding)
            if prompt_user_for_shortcut(target, conflict, auto_yes=auto_yes):
                replace_path = conflict.path_or_source if conflict else None
                if XfceShortcutManager.set_shortcut(target, replace_path=replace_path):
                    print(f"✓ Registered: {target.binding} → {target.command}")
                    success_count += 1
            else:
                print(f"[-] Skipped: {target.binding}")

    elif desktop == "kde" and KdeShortcutManager.is_available():
        for target in DEFAULT_SHORTCUTS:
            conflict = KdeShortcutManager.find_conflict(target.binding)
            if prompt_user_for_shortcut(target, conflict, auto_yes=auto_yes):
                if KdeShortcutManager.set_shortcut(target):
                    print(f"✓ Registered: {target.binding} → {target.command}")
                    success_count += 1
            else:
                print(f"[-] Skipped: {target.binding}")
        if success_count > 0:
            print("\n💡 KDE Plasma Note: If shortcuts do not trigger immediately, please log out and back in once to reload KWin.")

    elif desktop in ("hyprland", "sway", "i3"):
        print(f"\nTiling Window Manager ({desktop.upper()}) detected!")
        print("To bind Glyph global shortcuts, add these lines to your config file:")
        if desktop == "hyprland":
            print("  ~/.config/hypr/hyprland.conf:")
            print("    bind = $mainMod SHIFT, T, exec, glyph --grab")
            print("    bind = $mainMod SHIFT, I, exec, glyph --grab --instant")
        elif desktop in ("sway", "i3"):
            cfg = "~/.config/sway/config" if desktop == "sway" else "~/.config/i3/config"
            print(f"  {cfg}:")
            print("    bindsym $mod+Shift+t exec glyph --grab")
            print("    bindsym $mod+Shift+i exec glyph --grab --instant")
        return True

    else:
        print(f"⚠️  Automatic configuration not supported for desktop environment: {desktop}")
        print("You can manually configure keyboard shortcuts in your system settings:")
        print("  • Super + Shift + T  → glyph --grab")
        print("  • Super + Shift + I  → glyph --grab --instant")
        return False

    print("\n" + "=" * 60)
    if success_count > 0:
        print(f"🎉 Setup complete: {success_count} shortcut(s) active!")
    else:
        print("Setup finished. No changes made.")
    return success_count > 0


def remove_global_shortcuts(desktop_override: Optional[str] = None) -> bool:
    """Removes all Glyph global shortcuts from the desktop environment."""
    desktop = desktop_override or detect_desktop_environment()
    print(f"=== Removing Glyph Global Shortcuts ({desktop.upper()}) ===")
    if desktop == "gnome" or GnomeShortcutManager.is_available():
        res = GnomeShortcutManager.remove_shortcuts()
        if res:
            print("✓ Glyph custom shortcuts removed from GNOME.")
            return True
    elif desktop == "kde" and KdeShortcutManager.is_available():
        res = KdeShortcutManager.remove_shortcuts()
        if res:
            print("✓ Glyph custom shortcuts removed from KDE Plasma.")
            return True
    print("Removal complete.")
    return True
