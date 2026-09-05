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

    @staticmethod
    def notify_success(text: str) -> None:
        """Notifies the user that text was copied, previewing the first characters."""
        preview = text.strip().replace("\n", " ")
        if len(preview) > 60:
            preview = preview[:57] + "..."

        body = f"Copied to clipboard:\n\"{preview}\""
        NotificationManager._send(
            title="Glyph - Text Extractor",
            body=body,
            icon="edit-copy",
            urgency="normal"
        )

    @staticmethod
    def notify_no_text() -> None:
        """Notifies the user that no text was detected."""
        NotificationManager._send(
            title="Glyph - Text Extractor",
            body="No text detected in selected region.",
            icon="dialog-information",
            urgency="low"
        )

    @staticmethod
    def notify_error(message: str) -> None:
        """Notifies the user of an error."""
        NotificationManager._send(
            title="Glyph - Text Extractor (Error)",
            body=message,
            icon="dialog-error",
            urgency="critical"
        )

    @staticmethod
    def _send(title: str, body: str, icon: str = "dialog-information", urgency: str = "normal") -> None:
        if shutil.which("notify-send"):
            try:
                subprocess.run(
                    [
                        "notify-send",
                        "-a", "Glyph - Text Extractor",
                        "-i", icon,
                        "-u", urgency,
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
            proxy.call_sync(
                "Notify",
                GLib.Variant(
                    "(susssasa{sv}i)",
                    ("Glyph - Text Extractor", 0, icon, title, body, [], {}, 4000)
                ),
                Gio.DBusCallFlags.NONE,
                3000,
                None
            )
        except Exception as e:
            logger.debug(f"D-Bus notification failed: {e}")

