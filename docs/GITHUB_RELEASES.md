# GitHub Release Notes Reference

This document provides standardized, factual release notes for each published version of Glyph - Text Extractor. Use these notes when creating or updating release entries on [GitHub Releases](https://github.com/muhaideennausar/glyph-text-extractor/releases).

---

## v0.2.4 (2026-09-06)

### Summary
KDE Plasma global shortcut architecture overhaul with dedicated command shortcut launchers, D-Bus runtime binding, and desktop specification alignment.

### Changes
- **Dedicated KDE Shortcut Launchers**: Created `~/.local/share/applications/glyph-mode-*.desktop` launchers with `X-KDE-GlobalAccel-CommandShortcut=true` for native KDE Plasma 6 compatibility.
- **Hierarchical Configuration**: Structured `kglobalshortcutsrc` definitions to write to nested `[services]` groups in Plasma 6 and fallback root groups in Plasma 5 via `kwriteconfig6`/`kwriteconfig5`.
- **Active D-Bus Shortcut Registration**: Added `org.kde.kglobalaccel` `setShortcutKeys` D-Bus invocation to apply shortcuts immediately without requiring desktop logout.
- **Daemon Refresh Pipeline**: Automated multi-signal reload (`kbuildsycoca6`, `KWin.reconfigure`, and `plasma-kglobalaccel.service`).
- **Freedesktop Desktop Action Extensions**: Added `X-KDE-Shortcuts` keys to primary desktop entry.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.2.3 (2026-09-06)

### Summary
KDE Plasma desktop action mapping fix, native Spectacle snapshot capture support, and software rendering fallbacks for virtual machines.

### Changes
- **Spectacle Capture Engine**: Added native KDE Spectacle capture backend (`spectacle -b -n -o`) for Wayland sessions without `grim`.
- **Software Rendering Fallback**: Automatically sets `GSK_RENDERER=cairo` and `LIBGL_ALWAYS_SOFTWARE=1` in virtual machine environments lacking hardware 3D acceleration to prevent Mesa Zink failures.
- **Desktop Action Mappings**: Corrected Qt key sequence mappings for default actions (`_launch`, `Editor`, and `Instant`).
- **Automated Installer Prompts**: Added interactive desktop shortcut configuration prompts to `install.sh`.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.2.2 (2026-09-06)

### Summary
Cross-distribution package compatibility for openSUSE RPM, dynamic multi-Python interpreter resolution, and Flathub packaging preparation.

### Changes
- **openSUSE RPM Compatibility**: Configured rich Boolean dependencies in RPM spec (`python3dist(pillow)`, `python3-Pillow`, `libadwaita-1-0`, `tesseract-ocr`) enabling clean resolution via `zypper`.
- **Multi-Python Runtime Resolution**: Enhanced `/usr/bin/glyph` launcher to dynamically discover Python 3 interpreters ($\ge$ 3.10) with verified PIL and PyGObject bindings.
- **Graceful Dependency Validation**: Added startup validation with distribution-specific package installation guidance.
- **Flathub Flatpak Manifest**: Added GNOME 49 runtime manifest and AppStream branding configuration.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.2.1 (2026-09-06)

### Summary
Arch Linux native support, automatic shell PATH detection, and tiling window manager configuration alignment.

### Changes
- **Arch Linux Support**: Updated `packaging/arch/PKGBUILD` and added `tesseract-data-eng` to pre-flight dependency checks.
- **Shell PATH Automation**: Configured `install.sh` to ensure `~/.local/bin` is exported in `~/.bashrc` and `~/.zshrc` when missing.
- **Tiling WM Keybindings**: Aligned shortcut examples for Hyprland, Sway, and i3 with v0.2.0 defaults (`Super+Shift+T` for Review & Edit, `Super+Shift+I` for Instant Capture).

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.2.0 (2026-09-05)

### Summary
Dynamic geometry-based Page Segmentation Mode (PSM) selection, Otsu thresholding fallback, font edge sharpening, and configuration migration.

### Changes
- **Geometry-Aware Smart PSM**: Dynamically sets Page Segmentation Mode based on crop dimensions:
  - Single-line crops ($\ge$ 3:1 aspect ratio) use PSM 7.
  - Standard text snippets ($\le$ 300px height) use PSM 6.
  - Multi-paragraph or full page clips use PSM 3.
- **Otsu Binarization Fallback**: Automatically applies Otsu thresholding when low-contrast or noisy backgrounds are detected.
- **Edge Sharpening**: Unsharp mask filtering for antialiased screen fonts.
- **Structured Coordinate Extraction**: TSV parsing for bounding box coordinates and word confidence scores.
- **Mode B Promoted to Default**: Review & Edit modal is now the default mode for `glyph --grab` and `Super+Shift+T`; Instant Capture is mapped to `Super+Shift+I`.
- **Config Migration (v1 -> v2)**: Automatically upgrades `~/.config/glyph/config.json` while preserving custom settings.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.1.4 (2026-09-05)

### Summary
XDG Desktop Portal permission pre-authorization, compositor stabilization delay, and character escaping for desktop notifications.

### Changes
- **Portal Permission Pre-seed**: Automatically pre-seeds `org.freedesktop.impl.portal.PermissionStore` over D-Bus to prevent repeated permission prompts on GNOME Wayland.
- **Compositor Settle Delay**: Added 250ms stabilization delay prior to screen capture to avoid capturing window exit animations or shortcut transitions.
- **Notification Escaping**: Comprehensive XML/HTML entity escaping for notification titles and bodies.
- **Dual-Install Diagnostics**: Added detection and warnings when both user-space and system package binaries exist simultaneously.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.1.3 (2026-09-05)

### Summary
In-memory capture pipeline optimization, SVG icon theme synchronization, and desktop launcher integration.

### Changes
- **Pipeline Latency**: Streamlined in-memory image processing pipeline, reducing capture latency.
- **Icon Suite**: Added complete hicolor icon suite (48x48 through 512x512 PNGs and scalable SVG).
- **Desktop Entry Hardening**: Improved binary path resolution in desktop launchers.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.1.2 (2026-09-05)

### Summary
FreeDesktop notification integration, application branding icons, and portable archive packaging.

### Changes
- **System Notifications**: FreeDesktop notifications with application icon and desktop-entry hint.
- **Portable Distribution**: Added `glyph-*-linux-portable.tar.gz` distribution packaging with bundled installer.

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.1.1 (2026-09-05)

### Summary
Cross-desktop global shortcut manager with collision detection, and automated package builders.

### Changes
- **Shortcut Configuration Engine**: Automated configuration with collision detection across GNOME, KDE Plasma, XFCE, Cinnamon, MATE, Hyprland, Sway, and i3.
- **Native Package Builders**: Added `build_deb.sh` (Debian/Ubuntu) and `build_rpm.sh` (Fedora/openSUSE).

### Verification
```bash
sha256sum -c SHA256SUMS.txt
```

---

## v0.1.0 (2026-09-05)

### Summary
Initial release of Glyph - Text Extractor.

### Features
- Screen region selection with GTK4 and Libadwaita interface.
- Mode A (instant copy to clipboard) and Mode B (review and edit window).
- Tesseract OCR engine backend.
- Wayland and X11 compositor support via XDG Desktop Portal and CLI grabbers.
- XDG Base Directory configuration support.
