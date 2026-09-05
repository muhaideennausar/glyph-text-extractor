#!/usr/bin/env bash
set -e

echo "=== Removing local Glyph development installation ==="

# Remove launcher & library
rm -f "$HOME/.local/bin/glyph"
rm -rf "$HOME/.local/lib/glyph"

# Remove desktop entries & metainfo
rm -f "$HOME/.local/share/applications/io.github.glyph.Glyph.desktop"
rm -f "$HOME/.local/share/applications/io.github.muhaideennausar.Glyph.desktop"
rm -f "$HOME/.local/share/metainfo/io.github.glyph.Glyph.metainfo.xml"
rm -f "$HOME/.local/share/metainfo/io.github.muhaideennausar.Glyph.metainfo.xml"

# Remove icons
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.glyph.Glyph.svg"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.glyph.Glyph-symbolic.svg"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.muhaideennausar.Glyph.svg"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.muhaideennausar.Glyph-symbolic.svg"

for size in 48x48 64x64 128x128 256x256 512x512; do
    rm -f "$HOME/.local/share/icons/hicolor/$size/apps/io.github.glyph.Glyph.png"
    rm -f "$HOME/.local/share/icons/hicolor/$size/apps/io.github.muhaideennausar.Glyph.png"
done

# Refresh databases
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "✓ Local installation completely removed."
