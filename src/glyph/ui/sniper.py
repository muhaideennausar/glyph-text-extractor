"""
Native GTK4 Sniper Overlay Window (PowerToys Text Extractor Style).
Freezes the screen with a darkened translucent overlay, allowing precision crosshair crop
without camera shutter sounds, GNOME toolbars, or duplicate OS notifications.
"""

import os
import logging
from typing import Optional, Tuple, Callable
from PIL import Image
import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Gio

from glyph.capture import _create_secure_temp_file

logger = logging.getLogger("glyph.ui.sniper")


def calculate_crop_box(
    x1: float, y1: float, x2: float, y2: float, max_w: int, max_h: int, min_size: int = 5
) -> Optional[Tuple[int, int, int, int]]:
    """
    Computes clamped integer bounding box (x, y, w, h) from drag coordinates.
    Handles reverse drags (bottom-right to top-left) and rejects micro-clicks (< min_size).
    """
    rx = min(x1, x2)
    ry = min(y1, y2)
    rw = abs(x2 - x1)
    rh = abs(y2 - y1)

    # Boundary clamping
    rx = max(0.0, min(rx, float(max_w)))
    ry = max(0.0, min(ry, float(max_h)))
    rw = max(0.0, min(rw, float(max_w) - rx))
    rh = max(0.0, min(rh, float(max_h) - ry))

    ix = int(round(rx))
    iy = int(round(ry))
    iw = int(round(rw))
    ih = int(round(rh))

    if iw < min_size or ih < min_size:
        return None

    return (ix, iy, iw, ih)


class SniperOverlayWindow(Gtk.ApplicationWindow):
    """
    Fullscreen borderless window rendering the frozen screen capture with darkened overlay,
    cutout preview, coordinate tracking, and dimension HUD.
    """

    def __init__(
        self,
        app: Gtk.Application,
        image_path: str,
        on_complete_callback: Callable[[Optional[Tuple[int, int, int, int]]], None]
    ):
        super().__init__(application=app)
        self.image_path = image_path
        self.on_complete = on_complete_callback

        self.start_pos: Optional[Tuple[float, float]] = None
        self.current_pos: Optional[Tuple[float, float]] = None
        self.is_dragging = False

        # Load background screenshot surface
        try:
            self.bg_surface = cairo.ImageSurface.create_from_png(self.image_path)
            self.img_w = self.bg_surface.get_width()
            self.img_h = self.bg_surface.get_height()
        except Exception as e:
            logger.error(f"Failed to load screenshot surface for sniper overlay: {e}")
            self.bg_surface = None
            self.img_w = 1920
            self.img_h = 1080

        # Window configuration
        self.set_title("Glyph Sniper")
        self.set_decorated(False)
        self.fullscreen()
        self.set_cursor_from_name("crosshair")

        # Main Drawing Area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self._on_draw)
        self.set_child(self.drawing_area)

        # Mouse click gesture
        click_gesture = Gtk.GestureClick.new()
        click_gesture.connect("pressed", self._on_mouse_pressed)
        click_gesture.connect("released", self._on_mouse_released)
        self.drawing_area.add_controller(click_gesture)

        # Mouse motion controller
        motion_controller = Gtk.EventControllerMotion.new()
        motion_controller.connect("motion", self._on_mouse_motion)
        self.drawing_area.add_controller(motion_controller)

        # Keyboard controller (Escape to cancel)
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_draw(self, area: Gtk.DrawingArea, cr: cairo.Context, win_w: int, win_h: int) -> None:
        if not self.bg_surface or self.img_w <= 0 or self.img_h <= 0:
            return

        scale_x = win_w / self.img_w
        scale_y = win_h / self.img_h

        # 1. Paint background screenshot
        cr.save()
        cr.scale(scale_x, scale_y)
        cr.set_source_surface(self.bg_surface, 0, 0)
        cr.paint()
        cr.restore()

        # 2. Paint translucent dark tint
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
        cr.paint()

        # 3. Draw active selection if dragging
        if self.start_pos and self.current_pos:
            x1, y1 = self.start_pos
            x2, y2 = self.current_pos

            rx = min(x1, x2)
            ry = min(y1, y2)
            rw = abs(x2 - x1)
            rh = abs(y2 - y1)

            if rw > 2 and rh > 2:
                # 3a. Illuminate selected area (cut out the dark veil)
                cr.save()
                cr.rectangle(rx, ry, rw, rh)
                cr.clip()
                cr.scale(scale_x, scale_y)
                cr.set_source_surface(self.bg_surface, 0, 0)
                cr.paint()
                cr.restore()

                # 3b. Electric blue dashed selection border
                cr.save()
                cr.set_source_rgb(0.0, 0.25, 1.0)
                cr.set_line_width(2.0)
                cr.set_dash([6.0, 4.0])
                cr.rectangle(rx, ry, rw, rh)
                cr.stroke()
                cr.restore()

                # 3c. Corner brackets (matching app branding)
                cr.save()
                cr.set_source_rgb(0.0, 0.25, 1.0)
                cr.set_line_width(4.0)
                c_len = min(16.0, rw / 3.0, rh / 3.0)

                # Top-Left
                cr.move_to(rx, ry + c_len)
                cr.line_to(rx, ry)
                cr.line_to(rx + c_len, ry)
                cr.stroke()

                # Top-Right
                cr.move_to(rx + rw - c_len, ry)
                cr.line_to(rx + rw, ry)
                cr.line_to(rx + rw, ry + c_len)
                cr.stroke()

                # Bottom-Left
                cr.move_to(rx, ry + rh - c_len)
                cr.line_to(rx, ry + rh)
                cr.line_to(rx + c_len, ry + rh)
                cr.stroke()

                # Bottom-Right
                cr.move_to(rx + rw - c_len, ry + rh)
                cr.line_to(rx + rw, ry + rh)
                cr.line_to(rx + rw, ry + rh - c_len)
                cr.stroke()
                cr.restore()

                # 3d. Dimensions HUD chip
                actual_w = int(round(rw / scale_x))
                actual_h = int(round(rh / scale_y))
                dim_text = f"{actual_w} × {actual_h} px"

                cr.save()
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(12.0)
                ext = cr.text_extents(dim_text)

                pill_w = ext.width + 16
                pill_h = 24
                pill_x = rx + (rw - pill_w) / 2
                pill_y = ry + rh + 10 if ry + rh + 35 < win_h else ry - 30

                # Pill background
                cr.set_source_rgba(0.1, 0.1, 0.1, 0.85)
                cr.rectangle(pill_x, pill_y, pill_w, pill_h)
                cr.fill()

                # Pill text
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.move_to(pill_x + 8, pill_y + 16)
                cr.show_text(dim_text)
                cr.restore()

    def _on_mouse_pressed(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float) -> None:
        button = gesture.get_current_button()
        if button == Gdk.BUTTON_PRIMARY:
            self.start_pos = (x, y)
            self.current_pos = (x, y)
            self.is_dragging = True
            self.drawing_area.queue_draw()
        elif button == Gdk.BUTTON_SECONDARY:
            # Right click cancels
            self._cancel()

    def _on_mouse_motion(self, controller: Gtk.EventControllerMotion, x: float, y: float) -> None:
        if self.is_dragging and self.start_pos:
            self.current_pos = (x, y)
            self.drawing_area.queue_draw()

    def _on_mouse_released(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float) -> None:
        if not self.is_dragging or not self.start_pos:
            return

        self.is_dragging = False
        x1, y1 = self.start_pos
        x2, y2 = x, y

        win_w = self.get_width()
        win_h = self.get_height()

        if win_w <= 0 or win_h <= 0 or not self.bg_surface:
            self._cancel()
            return

        scale_x = win_w / self.img_w
        scale_y = win_h / self.img_h

        # Convert window display pixels to actual image coordinates
        orig_x1 = x1 / scale_x
        orig_y1 = y1 / scale_y
        orig_x2 = x2 / scale_x
        orig_y2 = y2 / scale_y

        box = calculate_crop_box(orig_x1, orig_y1, orig_x2, orig_y2, self.img_w, self.img_h)
        if box:
            self.on_complete(box)
        else:
            self.on_complete(None)

        self.close()

    def _on_key_pressed(self, controller: Gtk.EventControllerKey, keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q):
            self._cancel()
            return True
        return False

    def _cancel(self) -> None:
        self.on_complete(None)
        self.close()


def interactive_sniper_crop(fullscreen_image_path: str) -> Optional[str]:
    """
    Spawns the GTK4 sniper overlay window across the screen, blocking until user selects
    a crop box or cancels with Escape.
    Returns the path to the cropped image file, or None if cancelled.
    """
    if not os.path.exists(fullscreen_image_path) or os.path.getsize(fullscreen_image_path) == 0:
        return None

    result = {"box": None}

    app = Gtk.Application(
        application_id="io.github.glyph.Sniper",
        flags=Gio.ApplicationFlags.NON_UNIQUE
    )

    def on_complete(box: Optional[Tuple[int, int, int, int]]) -> None:
        result["box"] = box
        app.quit()

    def on_activate(application: Gtk.Application) -> None:
        win = SniperOverlayWindow(application, fullscreen_image_path, on_complete)
        win.present()

    app.connect("activate", on_activate)
    app.run([])

    # If user cancelled or selection was too small
    if not result["box"]:
        return None

    crop_x, crop_y, crop_w, crop_h = result["box"]

    # Crop the bounding box directly from the full screenshot using PIL
    try:
        with Image.open(fullscreen_image_path) as full_img:
            cropped_img = full_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            cropped_path = _create_secure_temp_file(prefix="glyph_crop_", suffix=".png")
            cropped_img.save(cropped_path, format="PNG")
            return cropped_path
    except Exception as e:
        logger.error(f"Failed to crop selected sniper region: {e}")
        return None
