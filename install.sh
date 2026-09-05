#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/lib/glyph"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
METAINFO_DIR="$HOME/.local/share/metainfo"
ICONS_DIR="$HOME/.local/share/icons/hicolor"

echo "=== Installing Glyph Text Extractor ==="

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$METAINFO_DIR"

# Copy package files from src/glyph
rm -rf "$INSTALL_DIR/glyph"
cp -r src/glyph "$INSTALL_DIR/"

# Install launcher script to ~/.local/bin/glyph
cat << 'EOF' > "$BIN_DIR/glyph"
#!/usr/bin/env bash
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export PYTHONPATH="$HOME/.local/lib/glyph:$PYTHONPATH"
exec /usr/bin/python3 -m glyph "$@"
EOF

chmod +x "$BIN_DIR/glyph"

# Install Desktop Entry & Metainfo
cp data/io.github.glyph.Glyph.desktop "$DESKTOP_DIR/io.github.glyph.Glyph.desktop"
cp data/io.github.glyph.Glyph.metainfo.xml "$METAINFO_DIR/io.github.glyph.Glyph.metainfo.xml"

# Auto-sync user custom SVG icon if present
if [ -f "assets/Glyph - Text Extractor.svg" ]; then
    cp "assets/Glyph - Text Extractor.svg" assets/icons/scalable/io.github.glyph.Glyph.svg
fi

# Auto-render pixel-perfect PNG suite from scalable SVG
if python3 -c "import gi; gi.require_version('Rsvg', '2.0')" 2>/dev/null; then
    python3 -c "
import os, cairo, gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
svg_path = 'assets/icons/scalable/io.github.glyph.Glyph.svg'
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
        surf.write_to_png(f'{out_dir}/io.github.glyph.Glyph.png')
" 2>/dev/null || true
fi

# Install Icons
mkdir -p "$ICONS_DIR/scalable/apps"
cp assets/icons/scalable/io.github.glyph.Glyph.svg "$ICONS_DIR/scalable/apps/"
cp assets/icons/scalable/io.github.glyph.Glyph-symbolic.svg "$ICONS_DIR/scalable/apps/"

for size in 48x48 64x64 128x128 256x256 512x512; do
    mkdir -p "$ICONS_DIR/$size/apps"
    if [ -f "assets/icons/hicolor/$size/apps/io.github.glyph.Glyph.png" ]; then
        cp "assets/icons/hicolor/$size/apps/io.github.glyph.Glyph.png" "$ICONS_DIR/$size/apps/"
    fi
done

# Update desktop and icon databases if tools are installed
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$ICONS_DIR" || true
fi

echo "✓ Glyph installed to $BIN_DIR/glyph"
echo "✓ Desktop entry created at $DESKTOP_DIR/io.github.glyph.Glyph.desktop"
echo "✓ AppStream metainfo installed at $METAINFO_DIR/io.github.glyph.Glyph.metainfo.xml"
echo "✓ High-resolution & symbolic icons installed to $ICONS_DIR"
echo ""
echo "To test now, run:"
echo "  glyph --grab"
echo ""
echo "To bind to Super + Shift + T in GNOME / Ubuntu:"
echo "  1. Open Settings -> Keyboard -> View and Customize Shortcuts -> Custom Shortcuts"
echo "  2. Name: Glyph Text Extractor"
echo "  3. Command: $BIN_DIR/glyph"
echo "  4. Shortcut: Super + Shift + T"
