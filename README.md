# Glyph - Text Extractor 🔍

<div align="center">
  <img src="assets/icons/scalable/io.github.muhaideennausar.Glyph.svg" width="128" height="128" alt="Glyph - Text Extractor Logo" />
  <h3>Lightning-Fast Screen Text Extractor for Linux</h3>
  <p>PowerToys Text Extractor alternative designed natively for Wayland and X11 desktops.</p>

[![CI](https://github.com/muhaideennausar/glyph-text-extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/muhaideennausar/glyph-text-extractor/actions)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Wayland%20%7C%20X11-green.svg)](#)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](#)

</div>

---

<div align="center">
  <img src="assets/screenshots/banner.png" width="800" alt="Glyph - Text Extractor Banner" />
</div>

---

## ⚡ Why Glyph - Text Extractor?

- **Instant Execution:** Snappy background pipeline with in-memory image streaming and lazy UI loading (~20ms latency).
- **Two Operating Modes:**
  - **Mode A (Instant):** Crop a screen region and have text copied directly to your clipboard with a desktop notification.
  - **Mode B (Review & Edit):** Clean, inspect, join broken PDF lines, or trim whitespace in a native Libadwaita modal before copying.
- **Compositor Agnostic:** Works seamlessly on GNOME, KDE Plasma, Hyprland, Sway, XFCE, and i3 via standard XDG Desktop Portals or native CLI grabbers (`grim`, `slurp`, `maim`, `scrot`).
- **Offline & Private:** Zero telemetry, no cloud APIs, private `0o600` temporary capture permissions with instant file shredding.
- **Resource Light:** Consumes < 35MB RAM. Runs smoothly even on low-spec hardware.

---

## 📸 Screenshots

|                             Mode A: Instant Screen Crop                              |                        Mode B: Interactive Review & Format                         |
| :----------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------: |
| <img src="assets/screenshots/mode_a_capture.png" width="400" alt="Mode A Capture" /> | <img src="assets/screenshots/mode_b_editor.png" width="400" alt="Mode B Editor" /> |

---

## 📦 Multi-Distro Installation

Glyph is engineered to install natively across all major Linux distributions.

### Option 1: Debian / Ubuntu / Linux Mint / Pop!\_OS (.deb)

Download the latest `.deb` package from the official [Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases) page and install it with one command (all dependencies resolve automatically):

```bash
sudo apt install ./glyph-text-extractor_*_all.deb
```

### Option 2: Fedora / RHEL / CentOS / Rocky (.rpm)

Download the latest `.rpm` package from the [Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases) page:

```bash
sudo dnf install ./glyph-text-extractor-*.rpm
```

*On openSUSE:*
```bash
sudo zypper install ./glyph-text-extractor-*.rpm
```

### Option 3: Arch Linux / Manjaro / EndeavourOS

Clone the repository and build via `makepkg`:

```bash
git clone https://github.com/muhaideennausar/glyph-text-extractor.git
cd glyph-text-extractor/packaging/arch
makepkg -si
```

### Option 4: Universal Python (`pipx` on any Linux distro)

```bash
pipx install git+https://github.com/muhaideennausar/glyph-text-extractor.git
glyph --setup-shortcuts
```

### Option 5: Native Local Installer (From Source)

```bash
git clone https://github.com/muhaideennausar/glyph-text-extractor.git
cd glyph-text-extractor
./install.sh
```

Ensure system dependencies are installed:

| Distribution                   | Command                                                                                                                               |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| **Ubuntu / Debian / Pop!\_OS** | `sudo apt install tesseract-ocr tesseract-ocr-eng wl-clipboard python3-pil python3-gi gir1.2-gtk-4.0 gir1.2-adw-1`                    |
| **Fedora**                     | `sudo dnf install tesseract tesseract-langpack-eng wl-clipboard python3-pillow python3-gobject gtk4 libadwaita`                       |
| **Arch / Manjaro**             | `sudo pacman -S tesseract tesseract-data-eng wl-clipboard python-pillow python-gobject gtk4 libadwaita`                               |
| **openSUSE**                   | `sudo zypper install tesseract-ocr tesseract-ocr-traineddata-english wl-clipboard python3-Pillow python3-gobject gtk4 libadwaita-1-0` |

---

## ⌨️ Intelligent Global Shortcuts

Glyph includes an automated cross-desktop shortcut setup engine that runs across **GNOME, KDE Plasma, Cinnamon, MATE, XFCE, and tiling WMs (Hyprland, Sway, i3)**:

```bash
glyph --setup-shortcuts
```

* **Collision Detection:** If a key combination (e.g. `<Super><Shift>t`) is already claimed by another application, Glyph retrieves and displays the conflicting shortcut's name, command, and key, and asks for your permission before replacing it.
* **Permission Prompt:** If no collision exists, it still asks for your confirmation before appending the shortcut.
* **Non-Interactive Mode:** For automated scripts, run with `-y`: `glyph --setup-shortcuts -y`.
* **Clean Removal:** Run `glyph --remove-shortcuts` to deregister shortcuts at any time.

---

## 🔐 First-Time Launch & Wayland Permissions

When you trigger Glyph - Text Extractor (`glyph --grab`) for the first time on modern GNOME (Ubuntu 24.04+, Fedora 39+, etc. running Wayland), your desktop will present a system security dialog:

<div align="center">
  <blockquote>
    <strong>Allow Apps to Take Screenshots?</strong><br />
    <em>An app wants to take screenshots at any time</em><br />
    <code>[Deny]</code> &nbsp; <code><strong>[Allow]</strong></code>
  </blockquote>
</div>

### Why does this appear?

- **Wayland Security Isolation:** On modern Wayland compositors, applications are strictly isolated from one another so that background programs cannot silently spy on your screen, passwords, or personal data.
- **Silent Sniper Snapshot:** To provide an instant screen freeze with Glyph - Text Extractor's custom GTK4 sniper overlay—bypassing GNOME's camera shutter sound, flash, and duplicate OS notifications—Glyph requests a background screenshot via the standard XDG Desktop Portal (`org.freedesktop.portal.Screenshot`).
- **One-Time Authorization:** Click **Allow**. GNOME permanently remembers your decision in **Settings → Privacy & Security → Screen Capture**. All future extractions will launch instantly without any prompts.

> [!TIP]
> If you ever accidentally click "Deny", you can re-enable permission at any time by opening **Settings → Privacy & Security → Screen Capture** and enabling the permission.

---

## ⌨️ Set Up Global Keyboard Shortcuts

To make Glyph - Text Extractor feel like a built-in OS tool (similar to PowerToys Text Extractor on Windows):

### GNOME / Ubuntu (Wayland or X11)

1. Open **Settings** → **Keyboard** → **View and Customize Shortcuts** → **Custom Shortcuts**.
2. Click **+** to add a new shortcut:
   - **Instant Capture (Mode A):**
     - **Name:** `Glyph - Text Extractor`
     - **Command:** `/home/<your-user>/.local/bin/glyph --grab`
     - **Shortcut:** <kbd>Super</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd>
   - **Review & Edit (Mode B):**
     - **Name:** `Glyph - Text Extractor (Review & Edit)`
     - **Command:** `/home/<your-user>/.local/bin/glyph --grab --edit`
     - **Shortcut:** <kbd>Super</kbd> + <kbd>Shift</kbd> + <kbd>E</kbd>

### Hyprland (`~/.config/hypr/hyprland.conf`)

```ini
bind = SUPER SHIFT, T, exec, glyph --grab
bind = SUPER SHIFT, E, exec, glyph --grab --edit
```

### Sway (`~/.config/sway/config`)

```ini
bindsym $mod+Shift+t exec glyph --grab
bindsym $mod+Shift+e exec glyph --grab --edit
```

### KDE Plasma

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**.
2. Add **Edit** → **New** → **Global Shortcut** → **Command/URL**.
3. Set Trigger to <kbd>Meta</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd> and Command to `glyph --grab`.

---

## 🛠️ CLI Usage & Options

```bash
# Instant interactive screen capture and copy (Mode A)
glyph --grab
glyph -g

# Interactive screen capture with review & edit modal (Mode B)
glyph --grab --edit
glyph -g -e

# Extract text directly from an existing image
glyph -f document_scan.png

# Extract in another language (requires tesseract-ocr-<lang>)
glyph --grab -l deu   # German
glyph --grab -l fra   # French
glyph --grab -l spa   # Spanish

# Custom Page Segmentation Mode (PSM)
glyph --grab --psm 7  # Single text line

# Suppress desktop notifications
glyph --grab --no-notify

# Debug diagnostics (detailed image and OCR logs)
glyph --grab --debug
```

---

## ⚙️ Configuration (`~/.config/glyph/config.json`)

Glyph follows the XDG Base Directory specification. Configuration settings are automatically created on first launch:

```json
{
  "general": {
    "default_mode": "instant",
    "notify_on_success": true,
    "notify_on_empty": true
  },
  "ocr": {
    "default_engine": "tesseract",
    "default_language": "eng",
    "default_psm": 6
  },
  "editor": {
    "window_width": 640,
    "window_height": 440,
    "show_char_count": true
  }
}
```

Precedence order:
`CLI Flags > ~/.config/glyph/config.json > Factory Defaults`

---

## 🧪 Testing

Glyph comes with a comprehensive unit and edge-case test suite covering corrupt headers, 0-byte aborts, 100MP gigapixel bombs, portal timeouts, and multi-line formatting:

```bash
PYTHONPATH=src python3 -m unittest discover tests -v
```

---

## 📄 License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.
