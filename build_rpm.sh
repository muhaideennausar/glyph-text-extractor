#!/usr/bin/env bash
set -e

VERSION="${1:-$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)}"
RPM_TOPDIR="$(pwd)/dist/rpmbuild"

if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "[-] rpmbuild is not installed. To build RPMs locally, install rpm / rpm-build."
    exit 0
fi

echo "=== Building RPM package for Glyph v${VERSION} ==="

rm -rf "$RPM_TOPDIR"
mkdir -p "$RPM_TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS,tmp}

cat << SPEC_EOF > "$RPM_TOPDIR/SPECS/glyph.spec"
Name:           glyph-text-extractor
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Lightning-fast screen text extractor for Linux
License:        GPL-3.0-or-later
URL:            https://github.com/muhaideennausar/glyph-text-extractor
BuildArch:      noarch
Requires:       python3, python3-pillow, python3-gobject, gtk4, libadwaita, tesseract, tesseract-langpack-eng, wl-clipboard

%description
PowerToys Text Extractor alternative designed natively for Wayland and X11 desktops.
Offers instant Mode A screen OCR directly to clipboard and interactive Mode B review editor.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/glyph
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/metainfo
mkdir -p %{buildroot}/usr/share/icons/hicolor/scalable/apps

# Install executable launcher
cat << 'BIN_EOF' > %{buildroot}/usr/bin/glyph
#!/usr/bin/env bash
export PYTHONPATH="/usr/share/glyph:\${PYTHONPATH}"
exec /usr/bin/python3 -m glyph "\$@"
BIN_EOF
chmod 755 %{buildroot}/usr/bin/glyph

# Install Python modules
cp -r $(pwd)/src/glyph %{buildroot}/usr/share/glyph/
find %{buildroot}/usr/share/glyph -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Install Desktop file and metainfo
cp $(pwd)/data/io.github.muhaideennausar.Glyph.desktop %{buildroot}/usr/share/applications/
cp $(pwd)/data/io.github.muhaideennausar.Glyph.metainfo.xml %{buildroot}/usr/share/metainfo/

# Install icons
cp $(pwd)/assets/icons/scalable/io.github.muhaideennausar.Glyph.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/
cp $(pwd)/assets/icons/scalable/io.github.muhaideennausar.Glyph-symbolic.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/

for size in 48x48 64x64 128x128 256x256 512x512; do
  mkdir -p %{buildroot}/usr/share/icons/hicolor/\$size/apps
  if [ -f "$(pwd)/assets/icons/hicolor/\$size/apps/io.github.muhaideennausar.Glyph.png" ]; then
    cp "$(pwd)/assets/icons/hicolor/\$size/apps/io.github.muhaideennausar.Glyph.png" %{buildroot}/usr/share/icons/hicolor/\$size/apps/
  fi
done

%files
%defattr(-,root,root,-)
/usr/bin/glyph
/usr/share/glyph
/usr/share/applications/io.github.muhaideennausar.Glyph.desktop
/usr/share/metainfo/io.github.muhaideennausar.Glyph.metainfo.xml
/usr/share/icons/hicolor/*/apps/io.github.muhaideennausar.Glyph*

%changelog
* Sat Sep 05 2026 Muhaideen Nausar <muhaideennausar@gmail.com> - ${VERSION}-1
- Release of Glyph - Text Extractor v${VERSION}
SPEC_EOF

rpmbuild --define "_topdir $RPM_TOPDIR" \
         --define "_builddir $RPM_TOPDIR/BUILD" \
         --define "_rpmdir $RPM_TOPDIR/RPMS" \
         --define "_srcrpmdir $RPM_TOPDIR/SRPMS" \
         -bb "$RPM_TOPDIR/SPECS/glyph.spec"

cp "$RPM_TOPDIR"/RPMS/noarch/*.rpm dist/
echo "✓ Successfully built RPM: \$(ls dist/*.rpm)"
