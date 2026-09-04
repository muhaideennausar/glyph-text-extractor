"""
Mode B: Interactive Review & Edit Modal (GTK4 / Libadwaita).
Allows users to review, edit, clean up, and reformat extracted text before copying.
"""

import sys
from typing import Optional, Callable
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib, Gio

from glyph.config import ConfigManager


def format_single_line(text: str) -> str:
    """Joins broken lines into a single continuous sentence, collapsing redundant whitespace."""
    if not text:
        return ""
    return " ".join(text.split())


def format_trim_whitespace(text: str) -> str:
    """Removes trailing/leading whitespace per line and discards redundant blank lines."""
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


class TextEditorWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, initial_text: str, on_complete_callback: Callable[[Optional[str]], None]):
        super().__init__(application=app)
        self.on_complete = on_complete_callback
        self.confirmed_text: Optional[str] = None
        self.config_manager = ConfigManager()
        cfg = self.config_manager.load_config()
        editor_cfg = cfg.get("editor", {})

        self.set_title("Glyph - Review & Edit")
        init_w = editor_cfg.get("window_width", 640)
        init_h = editor_cfg.get("window_height", 440)
        self.set_default_size(init_w, init_h)
        self.set_modal(True)

        # Main Layout
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root_box)

        # 1. Libadwaita HeaderBar
        header = Adw.HeaderBar()
        root_box.append(header)

        # Cancel Button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", self._on_cancel)
        header.pack_start(cancel_btn)

        # Copy & Close Button
        self.copy_btn = Gtk.Button(label="Copy & Close (Ctrl+Enter)")
        self.copy_btn.add_css_class("suggested-action")
        self.copy_btn.connect("clicked", self._on_confirm)
        header.pack_end(self.copy_btn)

        # 2. Text View Area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        root_box.append(scrolled)

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(18)
        self.text_view.set_right_margin(18)
        self.text_view.set_top_margin(18)
        self.text_view.set_bottom_margin(18)
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.set_text(initial_text)
        self.text_buffer.connect("changed", self._on_text_changed)

        scrolled.set_child(self.text_view)

        # 3. Bottom Toolbar & Status
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_bar.set_margin_start(16)
        bottom_bar.set_margin_end(16)
        bottom_bar.set_margin_top(8)
        bottom_bar.set_margin_bottom(10)
        root_box.append(bottom_bar)

        # Format helpers
        single_line_btn = Gtk.Button(label="Single Line")
        single_line_btn.set_tooltip_text("Join broken lines into a single continuous sentence")
        single_line_btn.connect("clicked", self._on_single_line)
        bottom_bar.append(single_line_btn)

        clean_spaces_btn = Gtk.Button(label="Trim Whitespace")
        clean_spaces_btn.set_tooltip_text("Remove trailing spaces and redundant blank lines")
        clean_spaces_btn.connect("clicked", self._on_trim_whitespace)
        bottom_bar.append(clean_spaces_btn)

        # Stats Label
        self.stats_label = Gtk.Label()
        self.stats_label.set_hexpand(True)
        self.stats_label.set_halign(Gtk.Align.END)
        self.stats_label.add_css_class("dim-label")
        bottom_bar.append(self.stats_label)

        self._update_stats()

        # Keyboard shortcut controller (Ctrl+Enter to save, Escape to cancel)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _get_current_text(self) -> str:
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        return self.text_buffer.get_text(start_iter, end_iter, True)

    def _update_stats(self) -> None:
        text = self._get_current_text()
        words = len(text.split())
        chars = len(text)
        self.stats_label.set_text(f"{words} words • {chars} characters")

    def _on_text_changed(self, buffer: Gtk.TextBuffer) -> None:
        self._update_stats()

    def _on_single_line(self, button: Gtk.Button) -> None:
        text = self._get_current_text()
        self.text_buffer.set_text(format_single_line(text))

    def _on_trim_whitespace(self, button: Gtk.Button) -> None:
        text = self._get_current_text()
        self.text_buffer.set_text(format_trim_whitespace(text))

    def _on_key_pressed(self, controller: Gtk.EventControllerKey, keyval: int, keycode: int, state: int) -> bool:
        if keyval == Gdk.KEY_Escape:
            self._on_cancel(None)
            return True
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._on_confirm(None)
            return True
        return False

    def _save_geometry(self) -> None:
        try:
            w = self.get_width()
            h = self.get_height()
            if w > 0 and h > 0:
                self.config_manager.update_editor_window_size(w, h)
        except Exception:
            pass

    def _on_confirm(self, button: Optional[Gtk.Button]) -> None:
        self._save_geometry()
        self.confirmed_text = self._get_current_text()
        self.on_complete(self.confirmed_text)
        self.close()

    def _on_cancel(self, button: Optional[Gtk.Button]) -> None:
        self._save_geometry()
        self.confirmed_text = None
        self.on_complete(None)
        self.close()


def launch_edit_modal(extracted_text: str) -> Optional[str]:
    """
    Spawns the GTK4/Libadwaita review window, blocking until user confirms or cancels.
    Returns the final edited text, or None if cancelled.
    """
    result = {"text": None}
    app = Adw.Application(
        application_id="io.github.glyph.Glyph",
        flags=Gio.ApplicationFlags.NON_UNIQUE
    )

    def on_complete(edited_text: Optional[str]) -> None:
        result["text"] = edited_text
        app.quit()

    def on_activate(application: Adw.Application) -> None:
        win = TextEditorWindow(application, extracted_text, on_complete)
        win.present()

    app.connect("activate", on_activate)
    app.run([])

    return result["text"]

