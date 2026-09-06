# Changelog

All notable changes to **Glyph - Text Extractor** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.4] - 2026-09-06

### Fixed

- **KDE Plasma Multi-Tier Shortcuts:** Implemented dedicated command shortcut launchers (`~/.local/share/applications/glyph-mode-*.desktop`) with `X-KDE-GlobalAccel-CommandShortcut=true` for seamless KDE Plasma 6 integration.
- **Cross-Version Config Structure:** Structured `kglobalshortcutsrc` entries targeting both nested `[services]` groups (Plasma 6 native) and root groups (Plasma 5 legacy) via `kwriteconfig6`/`kwriteconfig5`.
- **Active Daemon Reload & D-Bus Binding:** Integrated multi-signal daemon reload pipeline (`kbuildsycoca6/5`, `KWin.reconfigure`, `plasma-kglobalaccel.service` refresh) and direct D-Bus `setShortcutKeys` call to `org.kde.kglobalaccel` for instant shortcut binding without logout.
- **Freedesktop Desktop Extensions:** Added `X-KDE-Shortcuts` entries (`Meta+Shift+T`, `Meta+Shift+I`) to primary desktop entry.

---

## [0.2.3] - 2026-09-06

### Fixed

- **KDE Plasma Shortcut Mapping:** Corrected desktop action mapping (`_launch`, `Editor`, `Instant`) with standard Qt key sequences.
- **Virtual Machine Software Rendering:** Added automatic software rendering fallback (`GSK_RENDERER=cairo` and `LIBGL_ALWAYS_SOFTWARE=1`) to prevent Mesa Zink errors in virtualized environments.

### Added

- **Native KDE Spectacle Capture:** Added native KDE Spectacle screenshot engine (`spectacle -b -n -o`) for Wayland environments without `grim`.
- **Automated Shortcut Setup:** Automated global shortcut registration prompt in `install.sh` and added post-install shortcut registration instructions to packaging tools.

---

## [0.2.2] - 2026-09-06

### Fixed

- **openSUSE RPM Compatibility:** Updated RPM spec with rich Boolean dependencies (`python3dist(pillow)`, `python3-Pillow`, `libadwaita-1-0`, `tesseract-ocr`, `tesseract-ocr-traineddata-english`) enabling clean, automated package resolution via `zypper` without dependency break prompts.
- **Multi-Python Runtime Resolution:** RPM launcher (`/usr/bin/glyph`) and local launcher (`~/.local/bin/glyph`) dynamically discover compatible Python 3 interpreters ($\ge$ 3.10) with installed PIL and PyGObject bindings, resolving "PIL is not found" errors on distros with parallel Python stacks (such as openSUSE Leap).
- **Graceful Dependency Validation:** Added startup dependency validation (`check_runtime_dependencies()`) providing user-friendly, distro-specific package installation commands for openSUSE, Fedora, Debian/Ubuntu, and Arch Linux.

### Added

- **Flathub Flatpak Packaging:** Added GNOME 49 runtime manifest ([`io.github.muhaideennausar.Glyph.yaml`](io.github.muhaideennausar.Glyph.yaml)), sandbox picture portal permissions, and comprehensive Flathub submission guide ([`docs/FLATHUB_GUIDE.md`](docs/FLATHUB_GUIDE.md)).
- **Store Banner Branding:** Embedded AppStream `<branding>` primary colors (`#0040ff` / `#0030bf`) in metainfo XML for Flathub and GNOME Software showcase banners.

---

## [0.2.1] - 2026-09-06

### Added

- **Arch Linux Native Support:** Updated `packaging/arch/PKGBUILD` and added `tesseract-data-eng` to dependencies and pre-flight checks.
- **Shell PATH Automation:** `install.sh` automatically detects if `~/.local/bin` is missing from `$PATH` in interactive shells (e.g. minimal Arch Linux or clean distro setups) and adds it to `~/.bashrc` and `~/.zshrc`.
- **Session-Aware Documentation:** Documented the root/user D-Bus session boundary for system package managers (`dnf`, `rpm`, `apt`, `pacman`), clarifying that `glyph --setup-shortcuts` should be run in user space.

### Fixed

- **Shortcut Advice Alignment:** Aligned manual desktop shortcut guidance for tiling window managers (Hyprland, Sway, i3) with v0.2.0 defaults (`Super+Shift+T` for Review & Edit, `Super+Shift+I` for Instant Capture).
- **Completion Output:** Dynamic post-install CLI output that alerts the user whether to reload their shell or run directly.

---

## [0.2.0] - 2026-09-05

### Added

- **Geometry-Aware Smart PSM Selection:** Dynamically switches Page Segmentation Mode based on crop dimensions (PSM 7 for single-line $\ge 3:1$, PSM 6 for blocks $\le 300\text{px}$, PSM 3 for full pages).
- **Otsu Binarization Fallback:** Multi-pass recognition cascade triggers an automated 256-int lookup table Otsu thresholding pass on low-contrast or noisy backgrounds.
- **Unsharp Mask Edge Sharpening:** Fine font edge enhancement via `ImageFilter.UnsharpMask` for thin antialiased typography on high-DPI displays.
- **TSV Structured Data Extraction:** Added word-level coordinate and confidence score extraction from Tesseract TSV output.
- **Automatic Config Migration (v1 $\to$ v2):** Seamlessly upgrades existing user `config.json` files on disk, promoting Mode B (`"edit"`) as default without discarding custom preferences.

### Changed

- **Default Mode:** Mode B (Review & Edit modal) is now the primary default mode for `glyph --grab` and `<Super><Shift>T`.
- **Secondary Shortcut:** Added `<Super><Shift>I` for Instant Mode A screen OCR directly to clipboard.
- **Desktop Entry:** `data/io.github.muhaideennausar.Glyph.desktop` updated with `Capture & Edit` as primary action and `Instant Capture & Copy` (`--instant`) as secondary desktop action.

---

## [0.1.4] - 2026-09-05

### Added

- **Pre-grant XDG Portal Screenshot Permission:** Proactively pre-authorizes `org.freedesktop.impl.portal.PermissionStore` over session D-Bus for silent background capture in GNOME Wayland.
- **Compositor Settle Delay:** Added 250ms stabilization delay before snapshot capture so GNOME Overview exit animations and shortcut key releases settle cleanly.

### Fixed

- **Statement Break Preservation:** Retains double newlines (`\n\n`) and code indentation across OCR passes.
- **Notification Escaping:** Comprehensive XML and HTML entity escaping for notification summaries and bodies.

---

## [0.1.3] - 2026-09-05

### Changed

- **Streamlined Capture Pipeline:** In-memory image processing pipeline reducing capture latency down to ~20ms.
- **GNOME Integration:** Synchronized SVG and high-resolution PNG icon suite into hicolor icon themes.

---

## [0.1.2] - 2026-09-05

### Added

- **Branded FreeDesktop Notifications:** Branded app icon and categorized notification channels across GNOME, KDE, and XFCE.
- **Authentic Raw Screenshots:** Added high-resolution screenshots for Mode A sniper capture and Mode B GTK4 editor.

---

## [0.1.1] - 2026-09-05

### Added

- **Cross-Desktop Global Shortcut Manager:** Automatic collision detection and shortcut registration for GNOME, KDE Plasma, Cinnamon, MATE, XFCE, Hyprland, Sway, and i3.
- **Multi-Distro Packaging:** Automated package builders for Fedora/RHEL (`build_rpm.sh`), Debian/Ubuntu (`build_deb.sh`), and Arch Linux (`PKGBUILD`).

---

## [0.1.0] - 2026-09-05

### Added

- Initial release of Glyph - Text Extractor: Lightning-fast screen OCR utility for Linux.
- GTK4 + Libadwaita interactive sniper selection overlay and review editor.
- Multi-engine OCR architecture with Tesseract backend.
- XDG Base Directory configuration support.
