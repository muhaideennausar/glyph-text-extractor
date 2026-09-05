"""
Cross-desktop screen capture module with XDG Desktop Portal and compositor fallbacks.
"""

import os
import shutil
import logging
import subprocess
import tempfile
import uuid
import time
from typing import Optional
from urllib.parse import urlparse, unquote
from gi.repository import Gio, GLib

from glyph.errors import (
    CaptureError,
    PortalTimeoutError,
    PortalCancelledError,
    PortalUnavailableError,
)

logger = logging.getLogger("glyph.capture")


def _create_secure_temp_file(prefix: str = "glyph_capture_", suffix: str = ".png") -> str:
    """Creates a temporary file with restrictive 0o600 permissions."""
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def ensure_portal_screenshot_permission(app_id: Optional[str] = None) -> bool:
    """Pre-grants screenshot permission in the XDG Permission Store.

    This ensures xdg-desktop-portal marks permission_store_checked=True,
    allowing xdg-desktop-portal-gnome to take 100% silent background snapshots
    without prompting 'Share this screenshot with...'.
    """
    if app_id:
        target_ids = [app_id]
    else:
        target_ids = ["io.github.muhaideennausar.Glyph", "glyph"]

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.impl.portal.PermissionStore",
            "/org/freedesktop/impl/portal/PermissionStore",
            "org.freedesktop.impl.portal.PermissionStore",
            None,
        )
        for aid in target_ids:
            for table in ("screenshot", "devices"):
                try:
                    proxy.call_sync(
                        "SetPermission",
                        GLib.Variant("(sbssas)", (table, True, "screenshot", aid, ["yes"])),
                        Gio.DBusCallFlags.NONE,
                        1500,
                        None,
                    )
                except Exception:
                    pass
        logger.debug(f"Pre-authorized screenshot permission for {target_ids} in XDG PermissionStore.")
        return True
    except Exception as e:
        logger.debug(f"PermissionStore pre-authorization skipped or failed: {e}")
        return False


class ScreenCapture:
    """
    Captures user-selected screen areas interactively across Wayland and X11 desktops.
    """

    @classmethod
    def capture_interactive(cls) -> Optional[str]:
        """
        Executes interactive screen selection using the best available method:
        1. Native GTK4 Sniper Overlay (True PowerToys Text Extractor experience)
        2. slurp + grim (wlroots: Sway, Hyprland fallback)
        3. maim / scrot (X11 desktops fallback)
        4. Universal XDG Desktop Portal Screenshot (GNOME, KDE Plasma, Flatpak safety net)
        Returns the absolute filesystem path of the captured image, or None if cancelled.
        """
        # 1. Primary: Native GTK4 Sniper Overlay (True PowerToys Text Extractor experience)
        try:
            fullscreen_path = cls._capture_fullscreen_snapshot()
            if fullscreen_path and os.path.exists(fullscreen_path):
                from glyph.ui.sniper import interactive_sniper_crop
                crop_path = interactive_sniper_crop(fullscreen_path)
                # Ensure full-screen background snapshot is deleted immediately
                if os.path.exists(fullscreen_path):
                    try:
                        os.unlink(fullscreen_path)
                    except OSError:
                        pass
                return crop_path
        except Exception as e:
            logger.debug(f"Sniper overlay capture failed, trying fallback cascade: {e}")

        # Fallback Cascade
        is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        is_x11 = bool(os.environ.get("DISPLAY")) and not is_wayland

        # 2. Try wlroots (Sway / Hyprland)
        if is_wayland and shutil.which("slurp") and shutil.which("grim"):
            try:
                path = cls._capture_via_grim_slurp()
                if path:
                    return path
            except Exception as e:
                logger.debug(f"wlroots capture failed: {e}")

        # 3. Try X11 maim / scrot
        if is_x11:
            if shutil.which("maim"):
                try:
                    return cls._capture_via_maim()
                except Exception as e:
                    logger.debug(f"maim capture failed: {e}")

            if shutil.which("scrot"):
                try:
                    return cls._capture_via_scrot()
                except Exception as e:
                    logger.debug(f"scrot capture failed: {e}")

        # 4. Universal Safety Net: XDG Desktop Portal (GNOME, KDE Plasma, Flatpak, etc.)
        try:
            portal_path = cls._capture_via_portal(interactive=True)
            if portal_path:
                return portal_path
        except PortalTimeoutError:
            raise
        except Exception as e:
            logger.debug(f"Portal capture failed: {e}")

        raise PortalUnavailableError(
            "No compatible screenshot utility found.\n"
            "Ensure XDG Desktop Portal, slurp+grim, or maim is installed."
        )

    @classmethod
    def _capture_fullscreen_snapshot(cls) -> Optional[str]:
        """
        Captures the entire screen silently to a temporary file.
        Used as the frozen background for the GTK4 sniper overlay.
        """
        is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        is_x11 = bool(os.environ.get("DISPLAY")) and not is_wayland
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

        # 1. Sway / Hyprland (grim captures fullscreen instantly)
        if is_wayland and any(d in desktop for d in ("sway", "hyprland", "wayfire", "river")):
            if shutil.which("grim"):
                temp_path = _create_secure_temp_file(prefix="glyph_full_", suffix=".png")
                try:
                    proc = subprocess.run(["grim", temp_path], timeout=5)
                    if proc.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        return temp_path
                except Exception as e:
                    logger.debug(f"grim fullscreen capture failed: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

        # 2. X11 desktops (maim / scrot)
        if is_x11:
            if shutil.which("maim"):
                temp_path = _create_secure_temp_file(prefix="glyph_full_", suffix=".png")
                try:
                    proc = subprocess.run(["maim", temp_path], timeout=5)
                    if proc.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        return temp_path
                except Exception as e:
                    logger.debug(f"maim fullscreen capture failed: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

            if shutil.which("scrot"):
                temp_path = _create_secure_temp_file(prefix="glyph_full_", suffix=".png")
                try:
                    proc = subprocess.run(["scrot", temp_path], timeout=5)
                    if proc.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        return temp_path
                except Exception as e:
                    logger.debug(f"scrot fullscreen capture failed: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

        # 3. Universal XDG Desktop Portal (GNOME, KDE Plasma, Flatpak)
        try:
            # Pre-grant permission in XDG PermissionStore to enable silent captures
            ensure_portal_screenshot_permission()
            # Brief settle delay to allow GNOME Overview animations or shortcut key releases to settle
            time.sleep(0.25)
            return cls._capture_via_portal(interactive=False)
        except Exception as e:
            logger.debug(f"Non-interactive portal capture failed: {e}")
            return None


    @staticmethod
    def _capture_via_portal(interactive: bool = True) -> Optional[str]:
        """
        Calls org.freedesktop.portal.Screenshot over D-Bus.
        When interactive=True, opens compositor's interactive selection UI (120s timeout).
        When interactive=False, silently captures fullscreen snapshot for sniper overlay (12s timeout).
        """
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            None
        )

        token = f"glyph_{uuid.uuid4().hex[:10]}"
        sender = bus.get_unique_name().lstrip(":").replace(".", "_")
        expected_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"

        loop = GLib.MainLoop()
        result_holder = {"path": None, "cancelled": False, "timed_out": False}

        def on_timeout():
            result_holder["timed_out"] = True
            if loop.is_running():
                loop.quit()
            return False

        # Timeout guard: 120s for interactive, 12s for silent background capture
        timeout_seconds = 120 if interactive else 12
        timeout_source_id = GLib.timeout_add_seconds(timeout_seconds, on_timeout)

        def on_signal(connection, sender_name, object_path, interface_name, signal_name, parameters, user_data):
            if signal_name == "Response" and (object_path == expected_path or token in object_path):
                response_code, results = parameters.unpack()
                if response_code == 0 and "uri" in results:
                    raw_uri = results["uri"]
                    parsed_path = unquote(urlparse(raw_uri).path)
                    result_holder["path"] = parsed_path
                else:
                    result_holder["cancelled"] = True
                if loop.is_running():
                    loop.quit()

        sub_id = bus.signal_subscribe(
            "org.freedesktop.portal.Desktop",
            "org.freedesktop.portal.Request",
            "Response",
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            on_signal,
            None
        )

        # Build options dictionary
        options = {
            "interactive": GLib.Variant("b", interactive),
            "handle_token": GLib.Variant("s", token)
        }

        try:
            proxy.call_sync(
                "Screenshot",
                GLib.Variant("(sa{sv})", ("", options)),
                Gio.DBusCallFlags.NONE,
                10000,
                None
            )
        except Exception as e:
            GLib.source_remove(timeout_source_id)
            bus.signal_unsubscribe(sub_id)
            raise e

        # Wait for user to interact or timeout
        loop.run()
        if not result_holder["timed_out"]:
            try:
                GLib.source_remove(timeout_source_id)
            except Exception:
                pass
        bus.signal_unsubscribe(sub_id)

        if result_holder["timed_out"]:
            raise PortalTimeoutError(f"XDG Desktop Portal screenshot timed out after {timeout_seconds} seconds.")

        if result_holder["cancelled"] or not result_holder["path"]:
            return None

        # Ensure restrictive permissions on portal file if possible
        try:
            if os.path.exists(result_holder["path"]):
                os.chmod(result_holder["path"], 0o600)
        except OSError:
            pass

        return result_holder["path"]

    @staticmethod
    def _capture_via_grim_slurp() -> Optional[str]:
        """Captures region on wlroots (Sway/Hyprland) via slurp and grim with timeouts."""
        try:
            slurp_proc = subprocess.run(["slurp"], capture_output=True, text=True, timeout=30)
            geometry = slurp_proc.stdout.strip()
            if not geometry:
                return None  # Cancelled
        except subprocess.TimeoutExpired:
            logger.warning("slurp region selection timed out after 30 seconds.")
            return None

        temp_path = _create_secure_temp_file()
        try:
            grim_proc = subprocess.run(["grim", "-g", geometry, temp_path], timeout=5)
            if grim_proc.returncode == 0 and os.path.exists(temp_path):
                return temp_path
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.error(f"grim capture failed: {e}")

        # Cleanup if grim failed
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return None

    @staticmethod
    def _capture_via_maim() -> Optional[str]:
        """Captures region on X11 via maim with timeouts."""
        temp_path = _create_secure_temp_file()
        try:
            proc = subprocess.run(["maim", "-s", temp_path], timeout=30)
            if proc.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
        except subprocess.TimeoutExpired:
            logger.warning("maim selection timed out after 30 seconds.")
        except Exception as e:
            logger.error(f"maim capture failed: {e}")

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return None

    @staticmethod
    def _capture_via_scrot() -> Optional[str]:
        """Captures region on X11 via scrot with timeouts."""
        temp_path = _create_secure_temp_file()
        try:
            proc = subprocess.run(["scrot", "-s", temp_path], timeout=30)
            if proc.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return temp_path
        except subprocess.TimeoutExpired:
            logger.warning("scrot selection timed out after 30 seconds.")
        except Exception as e:
            logger.error(f"scrot capture failed: {e}")

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return None

