"""
Clipboard and system notification dispatch for modern Linux (Wayland and X11).
"""

import os
import shutil
import logging
import subprocess
from typing import Optional

logger = logging.getLogger("glyph.clipboard")


class ClipboardManager:
    """Handles system clipboard operations across Wayland and X11 desktops."""

    @staticmethod
    def copy(text: str) -> bool:
        """
        Copies text to the system clipboard using the best available backend:
        1. wl-copy (Wayland native)
        2. xclip / xsel (X11)
        3. PyGObject Gdk.Clipboard fallback
        """
        if not text:
            return False

        # 1. Wayland backend
        if shutil.which("wl-copy") and (os.environ.get("WAYLAND_DISPLAY") or not os.environ.get("DISPLAY")):
            try:
                proc = subprocess.run(
                    ["wl-copy"],
                    input=text.encode("utf-8"),
                    check=False,
                    timeout=3
                )
                if proc.returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                logger.warning("wl-copy timed out after 3 seconds.")
            except Exception as e:
                logger.debug(f"wl-copy failed: {e}")

        # 2. X11 xclip backend
        if shutil.which("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=False,
                    timeout=3
                )
                if proc.returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                logger.warning("xclip timed out after 3 seconds.")
            except Exception as e:
                logger.debug(f"xclip failed: {e}")

        # 3. X11 xsel backend
        if shutil.which("xsel"):
            try:
                proc = subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    check=False,
                    timeout=3
                )
                if proc.returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                logger.warning("xsel timed out after 3 seconds.")
            except Exception as e:
                logger.debug(f"xsel failed: {e}")

        # 4. GDK Fallback
        try:
            from gi.repository import Gdk
            display = Gdk.Display.get_default()
            if display:
                clipboard = display.get_clipboard()
                clipboard.set(text)
                return True
        except Exception as e:
            logger.debug(f"GDK clipboard fallback failed: {e}")

        return False


class NotificationManager:
    """Dispatches user feedback notifications via FreeDesktop desktop notifications."""

    APP_ID = "io.github.muhaideennausar.Glyph"

    @classmethod
    def _get_app_icon(cls) -> str:
        """Returns the best available application icon identifier or path."""
        # 1. Check if the icon is installed in standard system icon paths
        for icon_path in [
            f"/usr/share/icons/hicolor/scalable/apps/{cls.APP_ID}.svg",
            f"/usr/share/icons/hicolor/512x512/apps/{cls.APP_ID}.png",
            f"/usr/local/share/icons/hicolor/scalable/apps/{cls.APP_ID}.svg",
        ]:
            if os.path.exists(icon_path):
                return cls.APP_ID

        # 2. Check local repo / portable layout assets
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidate_svg = os.path.join(base_dir, "assets", "icons", "scalable", f"{cls.APP_ID}.svg")
        if os.path.exists(candidate_svg):
            return candidate_svg
        candidate_png = os.path.join(base_dir, "assets", "icons", "hicolor", "512x512", "apps", f"{cls.APP_ID}.png")
        if os.path.exists(candidate_png):
            return candidate_png

        # Fallback to the app ID
        return cls.APP_ID

    @classmethod
    def notify_success(cls, text: str) -> None:
        """Notifies the user that text was copied, previewing the first characters."""
        preview = text.strip().replace("\n", " ")
        if len(preview) > 60:
            preview = preview[:57] + "..."

        body = f"Copied to clipboard:\n\"{preview}\""
        cls._send(
            title="Glyph - Text Extractor",
            body=body,
            icon=cls._get_app_icon(),
            urgency="normal"
        )

    @classmethod
    def notify_no_text(cls) -> None:
        """Notifies the user that no text was detected."""
        cls._send(
            title="Glyph - Text Extractor",
            body="No text detected in selected region.",
            icon=cls._get_app_icon(),
            urgency="low"
        )

    @classmethod
    def notify_error(cls, message: str) -> None:
        """Notifies the user of an error."""
        cls._send(
            title="Glyph - Text Extractor (Error)",
            body=message,
            icon="dialog-error",
            urgency="critical"
        )

    @classmethod
    def _send(cls, title: str, body: str, icon: Optional[str] = None, urgency: str = "normal") -> None:
        app_icon = icon or cls._get_app_icon()

        if shutil.which("notify-send"):
            try:
                subprocess.run(
                    [
                        "notify-send",
                        "-a", "Glyph",
                        "-i", app_icon,
                        "-u", urgency,
                        "-h", f"string:desktop-entry:{cls.APP_ID}",
                        title,
                        body
                    ],
                    check=False,
                    timeout=3
                )
                return
            except subprocess.TimeoutExpired:
                logger.warning("notify-send timed out after 3 seconds.")
            except Exception as e:
                logger.debug(f"notify-send failed: {e}")

        # Fallback to D-Bus notification if notify-send is absent
        try:
            from gi.repository import Gio, GLib
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications",
                None
            )
            hints = {
                "desktop-entry": GLib.Variant("s", cls.APP_ID),
            }
            proxy.call_sync(
                "Notify",
                GLib.Variant(
                    "(susssasa{sv}i)",
                    ("Glyph", 0, app_icon, title, body, [], hints, 4000)
                ),
                Gio.DBusCallFlags.NONE,
                3000,
                None
            )
        except Exception as e:
            logger.debug(f"D-Bus notification failed: {e}")

