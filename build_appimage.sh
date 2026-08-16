#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Build Script for Google Antigravity Suite Installer AppImage (Linux x86_64)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build/appimage"
APPDIR="${BUILD_DIR}/AppDir"
DIST_DIR="${SCRIPT_DIR}/dist"
APPIMAGETOOL="${BUILD_DIR}/appimagetool"

echo "=================================================="
echo "🔨 Building Antigravity Suite Installer AppImage"
echo "=================================================="

# 1. Clean previous build artifacts
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/antigravity-installer"
mkdir -p "${DIST_DIR}"
mkdir -p "${BUILD_DIR}"

# 2. Download appimagetool if not present
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "⬇️  Downloading appimagetool..."
    curl -fsSL -o "${APPIMAGETOOL}" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" || \
    curl -fsSL -o "${APPIMAGETOOL}" "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "${APPIMAGETOOL}"
fi

# 3. Copy application package and assets into AppDir
echo "📦 Packaging application files..."
cp -r "${SCRIPT_DIR}/antigravity_installer" "${APPDIR}/usr/share/antigravity-installer/"
cp -r "${SCRIPT_DIR}/assets" "${APPDIR}/usr/share/antigravity-installer/"

# 4. Copy Desktop Entry and Icons across all standard hicolor resolutions
echo "🎨 Setting up desktop entries and multi-resolution icons..."
cat << 'EOF' > "${APPDIR}/google.antigravity.installer.desktop"
[Desktop Entry]
Name=Antigravity Suite Installer
Comment=Installer, manager and updater for Google Antigravity Suite (Hub, IDE, CLI)
Exec=antigravity-installer %u
Icon=google.antigravity.installer
Terminal=false
Type=Application
Categories=Development;Utility;
Keywords=google;antigravity;installer;ide;cli;agent;
StartupNotify=true
StartupWMClass=google.antigravity.installer
EOF

cp "${APPDIR}/google.antigravity.installer.desktop" "${APPDIR}/antigravity-installer.desktop"
cp "${APPDIR}/google.antigravity.installer.desktop" "${APPDIR}/usr/share/applications/"
cp "${APPDIR}/antigravity-installer.desktop" "${APPDIR}/usr/share/applications/"

# Generate all standard resolution icons for AppImage and Freedesktop
python3 -c "
import gi, shutil
from pathlib import Path
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

src_icon = Path('${SCRIPT_DIR}/assets/icons/antigravity.png')
appdir = Path('${APPDIR}')

shutil.copy2(src_icon, appdir / 'google.antigravity.installer.png')
shutil.copy2(src_icon, appdir / 'antigravity-installer.png')
shutil.copy2(src_icon, appdir / '.DirIcon')

pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(src_icon))
sizes = [512, 256, 128, 64, 48, 32, 16]

for size in sizes:
    target_dir = appdir / 'usr' / 'share' / 'icons' / 'hicolor' / f'{size}x{size}' / 'apps'
    target_dir.mkdir(parents=True, exist_ok=True)
    if size == pixbuf.get_width():
        shutil.copy2(src_icon, target_dir / 'google.antigravity.installer.png')
        shutil.copy2(src_icon, target_dir / 'antigravity-installer.png')
    else:
        scaled = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
        if scaled:
            scaled.savev(str(target_dir / 'google.antigravity.installer.png'), 'png', [], [])
            scaled.savev(str(target_dir / 'antigravity-installer.png'), 'png', [], [])
"

# 5. Create AppRun entry point
echo "🚀 Creating AppRun entry point..."
cat << 'EOF' > "${APPDIR}/AppRun"
#!/usr/bin/env bash
set -e

# Resolve directory of this AppImage bundle
HERE="$(cd "$(dirname "$(readlink -f "${0}")")" && pwd)"

export APPDIR="${HERE}"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/share/antigravity-installer:${PYTHONPATH:-}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Locate system python3
if command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
else
    echo "Error: python3 is required to run Antigravity Installer." >&2
    exit 1
fi

# Launch application
exec "${PYTHON_EXE}" "${HERE}/usr/share/antigravity-installer/antigravity_installer/main.py" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

# 6. Create binary symlink in usr/bin
cat << 'EOF' > "${APPDIR}/usr/bin/antigravity-installer"
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$(readlink -f "${0}")")/../.." && pwd)"
exec "${HERE}/AppRun" "$@"
EOF
chmod +x "${APPDIR}/usr/bin/antigravity-installer"

# 7. Generate AppImage using appimagetool
echo "⚡ Generating standalone AppImage..."
OUTPUT_APPIMAGE="${DIST_DIR}/Antigravity-Installer-x86_64.AppImage"
rm -f "${OUTPUT_APPIMAGE}"

ARCH=x86_64 "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "${OUTPUT_APPIMAGE}"
chmod +x "${OUTPUT_APPIMAGE}"

echo "=================================================="
echo "✅ AppImage successfully built!"
echo "📍 Location: ${OUTPUT_APPIMAGE}"
echo "📏 Size: $(du -h "${OUTPUT_APPIMAGE}" | cut -f1)"
echo "=================================================="
