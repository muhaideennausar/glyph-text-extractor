#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/lib/glyph"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
METAINFO_DIR="$HOME/.local/share/metainfo"
ICONS_DIR="$HOME/.local/share/icons/hicolor"

echo "=== Installing Glyph - Text Extractor ==="

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$METAINFO_DIR"

# Pre-flight runtime dependency check
MISSING_PKGS=()
if ! python3 -c "import PIL" 2>/dev/null; then
    MISSING_PKGS+=("python3-pil")
fi
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null; then
    MISSING_PKGS+=("python3-gi" "gir1.2-gtk-4.0" "gir1.2-adw-1")
fi
if ! command -v tesseract >/dev/null 2>&1; then
    MISSING_PKGS+=("tesseract-ocr" "tesseract-ocr-eng")
fi
if [ -n "$WAYLAND_DISPLAY" ] && ! command -v wl-copy >/dev/null 2>&1; then
    MISSING_PKGS+=("wl-clipboard")
fi

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "⚠️  Missing runtime dependencies detected:"
    for pkg in "${MISSING_PKGS[@]}"; do
        echo "   - $pkg"
    done
    echo ""
    echo "Please install them using your package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y ${MISSING_PKGS[*]}"
    echo "  Fedora:        sudo dnf install -y python3-pillow python3-gobject gtk4 libadwaita tesseract wl-clipboard"
    echo "  Arch:          sudo pacman -S --needed python-pillow python-gobject gtk4 libadwaita tesseract tesseract-data-eng wl-clipboard"
    echo "  openSUSE:      sudo zypper install -y python3-Pillow python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 tesseract-ocr tesseract-ocr-traineddata-english wl-clipboard"
    echo ""
fi

# Pre-seed XDG Desktop Portal screenshot permission in user session
if command -v busctl >/dev/null 2>&1; then
    busctl --user call org.freedesktop.impl.portal.PermissionStore /org/freedesktop/impl/portal/PermissionStore org.freedesktop.impl.portal.PermissionStore SetPermission sbssas screenshot true screenshot io.github.muhaideennausar.Glyph 1 yes 2>/dev/null || true
    busctl --user call org.freedesktop.impl.portal.PermissionStore /org/freedesktop/impl/portal/PermissionStore org.freedesktop.impl.portal.PermissionStore SetPermission sbssas devices true screenshot io.github.muhaideennausar.Glyph 1 yes 2>/dev/null || true
fi

# Copy package files from src/glyph
rm -rf "$INSTALL_DIR/glyph"
cp -r src/glyph "$INSTALL_DIR/"
find "$INSTALL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

if [ -x "/usr/bin/glyph" ]; then
    echo "ℹ️  Notice: System package detected at /usr/bin/glyph."
    echo "   This local installation in $BIN_DIR/glyph will take precedence."
    echo "   To revert to the system package later, run './uninstall.sh'."
fi

# Install launcher script to ~/.local/bin/glyph
cat << 'EOF' > "$BIN_DIR/glyph"
#!/usr/bin/env bash
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export PYTHONPATH="$HOME/.local/lib/glyph:$PYTHONPATH"

# Fall back to software rendering if running in a VM without 3D acceleration
if [ -z "$LIBGL_ALWAYS_SOFTWARE" ] && ! ls /dev/dri/renderD* >/dev/null 2>&1; then
    export LIBGL_ALWAYS_SOFTWARE=1
    if [ -z "$GSK_RENDERER" ]; then
        export GSK_RENDERER=cairo
    fi
fi

# Locate Python 3 interpreter (>= 3.10) with PIL and gi support
PYTHON_CMD=""
for py in python3 python3.13 python3.12 python3.11 python3.10 /usr/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then
        if "$py" -c "import sys, PIL, gi; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            PYTHON_CMD="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

exec "$PYTHON_CMD" -m glyph "$@"
EOF

chmod +x "$BIN_DIR/glyph"

# Ensure user desktop session and systemd services see ~/.local/bin in PATH
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user set-environment PATH="$BIN_DIR:$PATH" 2>/dev/null || true
fi

# Ensure ~/.local/bin is in PATH for future interactive shells
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$rc" ] && ! grep -q 'PATH=.*\.local/bin' "$rc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
        fi
    done
fi

# Install Desktop Entry & Metainfo
cp data/io.github.muhaideennausar.Glyph.desktop "$DESKTOP_DIR/io.github.muhaideennausar.Glyph.desktop"
sed -i "s|^Exec=glyph|Exec=$BIN_DIR/glyph|g" "$DESKTOP_DIR/io.github.muhaideennausar.Glyph.desktop"
cp data/io.github.muhaideennausar.Glyph.metainfo.xml "$METAINFO_DIR/io.github.muhaideennausar.Glyph.metainfo.xml"

# Auto-sync user custom SVG icon if present
if [ -f "assets/Glyph - Text Extractor.svg" ]; then
    cp "assets/Glyph - Text Extractor.svg" assets/icons/scalable/io.github.muhaideennausar.Glyph.svg
fi

# Auto-render pixel-perfect PNG suite from scalable SVG
if python3 -c "import gi; gi.require_version('Rsvg', '2.0')" 2>/dev/null; then
    python3 -c "
import os, cairo, gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
svg_path = 'assets/icons/scalable/io.github.muhaideennausar.Glyph.svg'
if os.path.exists(svg_path):
    handle = Rsvg.Handle.new_from_file(svg_path)
    dim = handle.get_dimensions()
    for s in [48, 64, 128, 256, 512]:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, s, s)
        cr = cairo.Context(surf)
        cr.scale(s / dim.width, s / dim.height)
        handle.render_cairo(cr)
        out_dir = f'assets/icons/hicolor/{s}x{s}/apps'
        os.makedirs(out_dir, exist_ok=True)
        surf.write_to_png(f'{out_dir}/io.github.muhaideennausar.Glyph.png')
" 2>/dev/null || true
fi

# Install Icons
mkdir -p "$ICONS_DIR/scalable/apps"
cp assets/icons/scalable/io.github.muhaideennausar.Glyph.svg "$ICONS_DIR/scalable/apps/"
cp assets/icons/scalable/io.github.muhaideennausar.Glyph-symbolic.svg "$ICONS_DIR/scalable/apps/"

for size in 48x48 64x64 128x128 256x256 512x512; do
    mkdir -p "$ICONS_DIR/$size/apps"
    if [ -f "assets/icons/hicolor/$size/apps/io.github.muhaideennausar.Glyph.png" ]; then
        cp "assets/icons/hicolor/$size/apps/io.github.muhaideennausar.Glyph.png" "$ICONS_DIR/$size/apps/"
    fi
done

# Update desktop and icon databases if tools are installed
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$ICONS_DIR" || true
fi

echo "✓ Glyph - Text Extractor installed to $BIN_DIR/glyph"
echo "✓ Desktop entry created at $DESKTOP_DIR/io.github.muhaideennausar.Glyph.desktop"
echo "✓ AppStream metainfo installed at $METAINFO_DIR/io.github.muhaideennausar.Glyph.metainfo.xml"
echo "✓ High-resolution & symbolic icons installed to $ICONS_DIR"

# Configure global desktop shortcuts interactively
if [ -t 0 ]; then
    "$BIN_DIR/glyph" --setup-shortcuts || true
else
    "$BIN_DIR/glyph" --setup-shortcuts -y || true
fi

echo ""
echo "To test now, run:"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "  source ~/.bashrc && glyph --grab"
    echo "  (or directly: $BIN_DIR/glyph --grab)"
else
    echo "  glyph --grab"
fi
echo ""
