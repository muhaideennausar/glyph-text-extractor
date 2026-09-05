#!/usr/bin/env bash
set -e

VERSION="${1:-$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)}"
PKG_DIR="dist/deb/glyph-text-extractor_${VERSION}_all"

rm -rf "$PKG_DIR" dist/*.deb
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/lib/python3/dist-packages"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/metainfo"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor"

# 1. Control file
cat << CONTROL_EOF > "$PKG_DIR/DEBIAN/control"
Package: glyph-text-extractor
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pil, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, tesseract-ocr, tesseract-ocr-eng, wl-clipboard
Maintainer: Muhaideen Nausar <muhaideennausar@gmail.com>
Homepage: https://github.com/muhaideennausar/glyph-text-extractor
Description: Lightning-fast screen text extractor for Linux
 PowerToys Text Extractor alternative designed natively for Wayland and X11 desktops.
 Offers instant Mode A screen OCR directly to clipboard and interactive Mode B review editor.
CONTROL_EOF

# 2. Launcher binary
cat << 'BIN_EOF' > "$PKG_DIR/usr/bin/glyph"
#!/usr/bin/env bash
exec /usr/bin/python3 -m glyph "$@"
BIN_EOF
chmod 755 "$PKG_DIR/usr/bin/glyph"

# 3. Python package
cp -r src/glyph "$PKG_DIR/usr/lib/python3/dist-packages/"
find "$PKG_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 4. Desktop & AppStream metadata
cp data/io.github.muhaideennausar.Glyph.desktop "$PKG_DIR/usr/share/applications/"
cp data/io.github.muhaideennausar.Glyph.metainfo.xml "$PKG_DIR/usr/share/metainfo/"

# 5. Icons
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/scalable/apps"
cp assets/icons/scalable/io.github.muhaideennausar.Glyph.svg "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/"
cp assets/icons/scalable/io.github.muhaideennausar.Glyph-symbolic.svg "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/"

for size in 48x48 64x64 128x128 256x256 512x512; do
  mkdir -p "$PKG_DIR/usr/share/icons/hicolor/$size/apps"
  if [ -f "assets/icons/hicolor/$size/apps/io.github.muhaideennausar.Glyph.png" ]; then
    cp "assets/icons/hicolor/$size/apps/io.github.muhaideennausar.Glyph.png" "$PKG_DIR/usr/share/icons/hicolor/$size/apps/"
  fi
done

# 6. Postinst triggers
cat << 'POSTINST_EOF' > "$PKG_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
fi
exit 0
POSTINST_EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# 7. Build deb package
dpkg-deb --build --root-owner-group "$PKG_DIR" "dist/glyph-text-extractor_${VERSION}_all.deb"
echo "Successfully built: dist/glyph-text-extractor_${VERSION}_all.deb"
