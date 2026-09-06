# Glyph - Text Extractor

<div align="center">
  <img src="assets/icons/scalable/io.github.muhaideennausar.Glyph.svg" width="128" height="128" alt="Glyph Logo" />
  <h3>Screen Text Extractor and OCR Utility for Linux</h3>
  <p>Select any screen area to extract text to your clipboard or review and edit it before copying.</p>

[![CI](https://github.com/muhaideennausar/glyph-text-extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/muhaideennausar/glyph-text-extractor/actions)
[![Latest Release](https://img.shields.io/github/v/release/muhaideennausar/glyph-text-extractor?color=blue&label=release)](https://github.com/muhaideennausar/glyph-text-extractor/releases/latest)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-Keep%20a%20Changelog-orange.svg)](CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Wayland%20%7C%20X11-green.svg)](#)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](#)

</div>

---

<div align="center">
  <img src="assets/screenshots/mode_a_capture.png" width="850" alt="Glyph Screen Region Selection" />
</div>

---

## Overview

Glyph is a native screen text extraction tool for Linux desktops running Wayland or X11. Inspired by Microsoft PowerToys Text Extractor, Glyph allows you to select any portion of your display, run optical character recognition locally, and copy the recognized text to your clipboard.

### Operating Modes

Glyph provides two workflows:

- **Review and Edit (Mode B — Default):** Freezes the screen for region selection, extracts text, and opens a Libadwaita modal window. You can inspect the text, join split lines, strip whitespace, and verify accuracy before copying. Triggered via `glyph --grab` or `Super + Shift + T`.
- **Instant Capture (Mode A):** Freezes the screen for region selection, extracts text, and copies it directly to your system clipboard with a desktop notification. Triggered via `glyph --grab --instant` (or `glyph -i`) or `Super + Shift + I`.

---

## Features

- **Compositor Agnostic:** Captures screens on GNOME, KDE Plasma, Hyprland, Sway, XFCE, Cinnamon, and i3 using standard XDG Desktop Portals with automated CLI fallbacks (`spectacle`, `grim`, `slurp`, `maim`, `scrot`).
- **Geometry-Aware Page Segmentation:** Dynamically selects Tesseract Page Segmentation Modes (PSM) based on crop dimensions:
  - Single-line crops (aspect ratio >= 3:1) use **PSM 7** (single text line) to prevent line breaks in URLs, paths, and commands.
  - Text blocks (height <= 300px) use **PSM 6** (single uniform block of text).
  - Multi-paragraph or full-page crops use **PSM 3** (fully automatic page segmentation).
- **Image Preprocessing Pipeline:**
  - Automated Otsu binarization fallback for low-contrast or noisy backgrounds.
  - Unsharp mask sharpening to clarify fine antialiased screen fonts.
  - RGBA alpha channel flattening onto neutral backgrounds.
  - Adaptive 3.0x upscaling for low-resolution selections.
- **Local and Private:** All OCR processing executes locally via Tesseract neural LSTM models. Zero network requests, zero telemetry. Temporary screen captures are written with `0o600` permissions and unlinked immediately after processing.
- **Automated Desktop Shortcuts:** Built-in shortcut configuration engine with collision detection for GNOME, KDE Plasma 6/5, Cinnamon, MATE, XFCE, Hyprland, Sway, and i3.
- **Low Resource Usage:** Uses under 35 MB RAM with lazy GTK initialization.

---

## Screenshots

### Interactive Region Selection (Mode A / Mode B trigger)

Darkens the screen and provides a crosshair selection box with live dimension feedback.

<div align="center">
  <img src="assets/screenshots/mode_a_capture.png" width="800" alt="Screen region selection" />
</div>

### Review and Edit Window (Mode B)

Inspect extracted text, join broken PDF lines into continuous prose, trim whitespace, and view word and character counts.

<div align="center">
  <img src="assets/screenshots/mode_b_editor.png" width="800" alt="Review and edit modal window" />
</div>

---

## Installation

### Debian, Ubuntu, Linux Mint, Pop!_OS (.deb)

Download the `.deb` package from [Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases) and install:

```bash
sudo apt install ./glyph-text-extractor_*_all.deb
glyph --setup-shortcuts
```

### Fedora, RHEL, Rocky Linux (.rpm)

Download the `.rpm` package from [Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases) and install:

```bash
sudo dnf install ./glyph-text-extractor-*.rpm
glyph --setup-shortcuts
```

### openSUSE (.rpm)

```bash
sudo zypper install ./glyph-text-extractor-*.rpm
glyph --setup-shortcuts
```

### Arch Linux, Manjaro, EndeavourOS

Build and install from the provided `PKGBUILD`:

```bash
git clone https://github.com/muhaideennausar/glyph-text-extractor.git
cd glyph-text-extractor/packaging/arch
makepkg -si
glyph --setup-shortcuts
```

### Universal Python (`pipx`)

```bash
pipx install git+https://github.com/muhaideennausar/glyph-text-extractor.git
glyph --setup-shortcuts
```

### Portable Release Archive (.tar.gz)

Download `glyph-*-linux-portable.tar.gz` from [Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases), unpack, and run the installer:

```bash
tar -xzf glyph-*-linux-portable.tar.gz
cd glyph-*-linux-all
./install.sh
```

### Source Installation

```bash
git clone https://github.com/muhaideennausar/glyph-text-extractor.git
cd glyph-text-extractor
./install.sh
```

Ensure system dependencies are installed:

| Distribution | Package Manager Command |
| :--- | :--- |
| **Ubuntu / Debian** | `sudo apt install tesseract-ocr tesseract-ocr-eng wl-clipboard python3-pil python3-gi gir1.2-gtk-4.0 gir1.2-adw-1` |
| **Fedora** | `sudo dnf install tesseract tesseract-langpack-eng wl-clipboard python3-pillow python3-gobject gtk4 libadwaita` |
| **Arch Linux** | `sudo pacman -S tesseract tesseract-data-eng wl-clipboard python-pillow python-gobject gtk4 libadwaita` |
| **openSUSE** | `sudo zypper install tesseract-ocr tesseract-ocr-traineddata-english wl-clipboard python3-Pillow python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1` |

### Flatpak / Flathub

A Flatpak manifest is provided in [`io.github.muhaideennausar.Glyph.yaml`](io.github.muhaideennausar.Glyph.yaml). For build instructions and Flathub submission steps, see [Flathub Publishing Guide](docs/FLATHUB_GUIDE.md).

---

## Keyboard Shortcuts

### Automated Configuration

Run the shortcut setup assistant to configure global keys for your desktop environment:

```bash
glyph --setup-shortcuts
```

- **Collision Detection:** Checks whether keybindings are already registered by the desktop or another application. Displays conflicting commands and prompts for confirmation before overwriting.
- **Non-Interactive Mode:** For provisioning scripts, pass `-y` to accept defaults without prompting:
  ```bash
  glyph --setup-shortcuts -y
  ```
- **Deregistration:** Remove all registered Glyph shortcuts:
  ```bash
  glyph --remove-shortcuts
  ```

### Default Key Combinations

| Shortcut | Action | Command |
| :--- | :--- | :--- |
| `Super + Shift + T` | Review & Edit (Mode B — Default) | `glyph --grab` |
| `Super + Shift + I` | Instant Capture to Clipboard (Mode A) | `glyph --grab --instant` |

### Manual Configuration

If you prefer to configure shortcuts manually:

#### GNOME (Wayland or X11)
1. Open **Settings** -> **Keyboard** -> **View and Customize Shortcuts** -> **Custom Shortcuts**.
2. Add a new shortcut:
   - Name: `Glyph - Review & Edit`
   - Command: `glyph --grab`
   - Shortcut: `Super + Shift + T`
3. Add an instant shortcut (optional):
   - Name: `Glyph - Instant Capture`
   - Command: `glyph --grab --instant`
   - Shortcut: `Super + Shift + I`

#### KDE Plasma
1. Open **System Settings** -> **Shortcuts** -> **Custom Shortcuts** (or **Command Shortcuts** in Plasma 6).
2. Add a new Global Shortcut pointing to `glyph --grab` for `Meta + Shift + T`.
3. Add a second shortcut pointing to `glyph --grab --instant` for `Meta + Shift + I`.

#### Hyprland (`~/.config/hypr/hyprland.conf`)
```ini
bind = SUPER SHIFT, T, exec, glyph --grab
bind = SUPER SHIFT, I, exec, glyph --grab --instant
```

#### Sway (`~/.config/sway/config`) / i3 (`~/.config/i3/config`)
```ini
bindsym $mod+Shift+t exec glyph --grab
bindsym $mod+Shift+i exec glyph --grab --instant
```

---

## Wayland Permissions Notice

On modern Wayland compositors (such as GNOME on Ubuntu 24.04+ or Fedora 39+), the desktop may display a security prompt on first launch:

> **Allow Apps to Take Screenshots?**  
> *An app wants to take screenshots at any time*  
> `[Deny]` &nbsp; `[Allow]`

### Why this prompt appears
Wayland isolates application windows for security. To capture screen contents silently—without system shutter noises or flashes—Glyph requests a background screenshot through the standard FreeDesktop XDG Desktop Portal (`org.freedesktop.portal.Screenshot`).

Selecting **Allow** saves this authorization in your system settings (**Settings -> Privacy & Security -> Screen Capture**). Subsequent captures execute immediately without prompts.

---

## CLI Reference

```
Usage: glyph [OPTIONS]

Options:
  -g, --grab            Trigger screen region selection (default behavior).
  -e, --edit            Open review & edit window before copying text (Mode B).
  -i, --instant         Copy text directly to clipboard without opening editor (Mode A).
  -f, --file PATH       Extract text from an existing image file instead of capturing.
  -l, --lang CODE       Tesseract language code (e.g. eng, deu, fra, spa).
  -p, --psm NUM         Tesseract Page Segmentation Mode (overrides smart PSM).
  -s, --scale FACTOR    Image upscale factor before OCR (default: adaptive 3.0).
  --notify              Enable desktop notifications (overrides config).
  --no-notify           Suppress desktop notifications (overrides config).
  --copy                Enable clipboard copy (overrides config).
  --no-copy             Disable clipboard copy (overrides config).
  --stdout              Print extracted text directly to standard output.
  --debug               Enable debug logging output.
  --setup-shortcuts     Interactively configure global desktop shortcuts.
  -y                    Accept default prompts non-interactively during shortcut setup.
  --remove-shortcuts    Remove registered global desktop shortcuts.
  -v, --version         Show application version and diagnose installation path conflicts.
  -h, --help            Show this help message and exit.
```

### Common Commands

```bash
# Capture screen region and open editor (Mode B — default)
glyph

# Capture screen region and copy directly to clipboard (Mode A)
glyph -i

# Extract text from an existing image file and print to stdout
glyph -f document.png --stdout --no-copy

# Extract text in German using single-line segmentation
glyph -l deu --psm 7

# Run non-interactive shortcut setup
glyph --setup-shortcuts -y
```

---

## Configuration

Glyph complies with the XDG Base Directory specification. Configuration settings are stored in `~/.config/glyph/config.json`:

```json
{
  "version": 2,
  "general": {
    "default_mode": "edit",
    "auto_copy_to_clipboard": true,
    "show_notifications": true
  },
  "ocr": {
    "default_engine": "tesseract",
    "default_language": "eng",
    "default_psm": 3,
    "enable_adaptive_scaling": true,
    "smart_psm": true,
    "enhance_edges": false,
    "preserve_spaces": true
  },
  "editor": {
    "window_width": 640,
    "window_height": 440,
    "remember_window_size": true
  }
}
```

### Configuration Options

| Section | Key | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `general` | `default_mode` | string | `"edit"` | Default behavior: `"edit"` (Mode B modal) or `"instant"` (Mode A clipboard). |
| `general` | `auto_copy_to_clipboard` | boolean | `true` | Automatically copies text to system clipboard. |
| `general` | `show_notifications` | boolean | `true` | Displays desktop notifications after extraction. |
| `ocr` | `default_engine` | string | `"tesseract"` | OCR engine backend. |
| `ocr` | `default_language` | string | `"eng"` | Default Tesseract language code. |
| `ocr` | `default_psm` | integer | `3` | Default Page Segmentation Mode if `smart_psm` is disabled. |
| `ocr` | `smart_psm` | boolean | `true` | Dynamically selects PSM 7 (single line), PSM 6 (block), or PSM 3 (page). |
| `ocr` | `enable_adaptive_scaling` | boolean | `true` | Upscales small crops for improved character recognition. |
| `ocr` | `enhance_edges` | boolean | `false` | Applies unsharp mask filtering prior to recognition. |
| `ocr` | `preserve_spaces` | boolean | `true` | Instructs Tesseract to preserve interword spacing. |
| `editor` | `window_width` | integer | `640` | Initial width of the review editor window. |
| `editor` | `window_height` | integer | `440` | Initial height of the review editor window. |
| `editor` | `remember_window_size` | boolean | `true` | Persists window dimensions between sessions. |

Precedence: `CLI Flags > ~/.config/glyph/config.json > Built-in Defaults`

---

## Testing

Run the automated test suite:

```bash
python3 -m unittest discover -s tests -v
```

The test suite covers:
- Image validation (empty files, non-existent paths, resolution thresholds).
- Preprocessing operations (Otsu thresholding, alpha composition, unsharp masking).
- OCR engine behavior (Page Segmentation Modes, timeout handling, multiline preservation).
- Desktop detection and shortcut managers (GNOME, KDE Plasma, XFCE, Sway, Hyprland).
- Shortcut collision detection and resolution prompts.

---

## Upgrading

### Debian / Ubuntu (.deb)
```bash
sudo apt install --reinstall ./glyph-text-extractor_*_all.deb
```

### Fedora / openSUSE (.rpm)
```bash
sudo dnf upgrade ./glyph-text-extractor-*.rpm
# openSUSE:
sudo zypper update ./glyph-text-extractor-*.rpm
```

### Arch Linux
```bash
cd glyph-text-extractor
git pull origin main
cd packaging/arch && makepkg -si
```

### Python / pipx
```bash
pipx upgrade glyph-text-extractor
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and migration details.

---

## License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE) for details.
