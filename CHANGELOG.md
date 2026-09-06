# Changelog

All notable changes to **Glyph - Text Extractor** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.4] - 2026-09-06

### Fixed

- **KDE Plasma Multi-Tier Shortcuts:** Added dedicated command shortcut desktop entries (`~/.local/share/applications/glyph-mode-*.desktop`) with `X-KDE-GlobalAccel-CommandShortcut=true` for KDE Plasma 6.
- **Hierarchical Configuration:** Structured `kglobalshortcutsrc` writes to target nested `[services]` groups in Plasma 6 and root groups in Plasma 5 via `kwriteconfig6`/`kwriteconfig5`.
- **D-Bus Runtime Registration:** Added direct D-Bus `setShortcutKeys` calls to `org.kde.kglobalaccel` for immediate keybinding registration without session restart.
- **Daemon Refresh:** Automated multi-signal reload sequence (`kbuildsycoca6/5`, `KWin.reconfigure`, and `plasma-kglobalaccel.service`).
- **Desktop Entry Extensions:** Added `X-KDE-Shortcuts` entries (`Meta+Shift+T`, `Meta+Shift+I`) to primary desktop entry.

---

## [0.2.3] - 2026-09-06

### Fixed

- **KDE Plasma Action Mapping:** Corrected desktop action mapping (`_launch`, `Editor`, `Instant`) with standard Qt key sequences.
- **Virtual Machine Software Rendering:** Added automatic software rendering fallback (`GSK_RENDERER=cairo` and `LIBGL_ALWAYS_SOFTWARE=1`) to prevent Mesa Zink errors in virtualized environments.

### Added

- **KDE Spectacle Capture Backend:** Added native KDE Spectacle screenshot engine support (`spectacle -b -n -o`) for Wayland environments without `grim`.
- **Shortcut Configuration Prompt:** Integrated automated global shortcut registration prompt in `install.sh`.

---

## [0.2.2] - 2026-09-06

### Fixed

- **openSUSE RPM Package Resolution:** Added rich Boolean dependencies (`python3dist(pillow)`, `python3-Pillow`, `libadwaita-1-0`, `tesseract-ocr`) in RPM spec for clean installation via `zypper`.
- **Multi-Python Interpreter Resolution:** Enhanced launcher scripts to dynamically discover Python 3 interpreters (>= 3.10) with verified PIL and PyGObject bindings.
- **Dependency Validation:** Added startup dependency checks (`check_runtime_dependencies()`) providing distribution-specific installation commands.

### Added

- **Flathub Flatpak Manifest:** Added GNOME 49 runtime manifest ([`io.github.muhaideennausar.Glyph.yaml`](io.github.muhaideennausar.Glyph.yaml)) and Flatpak documentation.
- **AppStream Branding:** Embedded primary branding colors in metainfo XML for software center showcases.

---

## [0.2.1] - 2026-09-06

### Added

- **Arch Linux Support:** Updated `packaging/arch/PKGBUILD` and added `tesseract-data-eng` to pre-flight dependency checks.
- **Shell PATH Detection:** Added automatic `~/.local/bin` export detection and configuration for `~/.bashrc` and `~/.zshrc`.
- **Session Boundary Guidance:** Documented root and user session boundary for package managers.

### Fixed

- **Shortcut Keybinding Alignment:** Aligned manual desktop shortcut guidance for tiling window managers (Hyprland, Sway, i3) with v0.2.0 defaults (`Super+Shift+T` for Review & Edit, `Super+Shift+I` for Instant Capture).

---

## [0.2.0] - 2026-09-05

### Added

- **Geometry-Aware Smart PSM Selection:** Dynamically switches Tesseract Page Segmentation Mode based on crop dimensions (PSM 7 for single-line >= 3:1, PSM 6 for blocks <= 300px, PSM 3 for multi-paragraph clips).
- **Otsu Binarization Fallback:** Multi-pass recognition cascade triggers an automated Otsu thresholding pass on low-contrast backgrounds.
- **Unsharp Mask Edge Sharpening:** Font edge enhancement via `ImageFilter.UnsharpMask` for thin antialiased typography on high-DPI displays.
- **TSV Structured Data Extraction:** Word-level coordinate and confidence score extraction from Tesseract TSV output.
- **Config Migration:** Automatic upgrade from configuration v1 to v2, setting Mode B (`"edit"`) as default while preserving user settings.

### Changed

- **Default Workflow:** Mode B (Review & Edit window) is now the default mode for `glyph --grab` and `Super+Shift+T`.
- **Instant Shortcut:** Added `Super+Shift+I` for Mode A screen OCR directly to clipboard.
- **Desktop Entry:** Updated desktop actions for Review & Edit and Instant Capture.

---

## [0.1.4] - 2026-09-05

### Added

- **XDG Portal Screenshot Pre-authorization:** Pre-authorizes `org.freedesktop.impl.portal.PermissionStore` over D-Bus for background capture in GNOME Wayland.
- **Compositor Settle Delay:** Added 250ms stabilization delay before snapshot capture so window animations settle cleanly.

### Fixed

- **Line Break Preservation:** Preserves double newlines (`\n\n`) and code indentation across OCR passes.
- **Notification Entity Escaping:** XML and HTML entity escaping for notification summaries and bodies.

---

## [0.1.3] - 2026-09-05

### Changed

- **Capture Pipeline Optimization:** In-memory image processing pipeline reducing capture latency.
- **Icon Assets:** Complete SVG and high-resolution PNG icon suite in hicolor themes.

---

## [0.1.2] - 2026-09-05

### Added

- **FreeDesktop Notifications:** Application icon and desktop-entry hint in system notifications.
- **Screenshots:** Added application screenshots for region selection and GTK4 review editor.

---

## [0.1.1] - 2026-09-05

### Added

- **Global Shortcut Manager:** Automatic collision detection and shortcut registration for GNOME, KDE Plasma, Cinnamon, MATE, XFCE, Hyprland, Sway, and i3.
- **Packaging Scripts:** Package builders for Fedora/RHEL (`build_rpm.sh`), Debian/Ubuntu (`build_deb.sh`), and Arch Linux (`PKGBUILD`).

---

## [0.1.0] - 2026-09-05

### Added

- Initial release of Glyph - Text Extractor: screen OCR utility for Linux.
- GTK4 and Libadwaita interactive selection overlay and review editor.
- Tesseract OCR engine backend.
- XDG Base Directory configuration support.
