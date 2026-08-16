#!/usr/bin/env bash
set -e

# ==============================================================================
# Smart Bootstrap Launcher for Google Antigravity Suite Installer
# Automatically checks FUSE2 / libfuse2t64 and launches the AppImage seamlessly
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_BIN="${SCRIPT_DIR}/dist/Antigravity-Installer-x86_64.AppImage"

if [ ! -f "${APPIMAGE_BIN}" ]; then
    APPIMAGE_BIN="${SCRIPT_DIR}/Antigravity-Installer-x86_64.AppImage"
fi

if [ ! -f "${APPIMAGE_BIN}" ]; then
    # Fallback to local dev run.sh
    if [ -f "${SCRIPT_DIR}/run.sh" ]; then
        exec "${SCRIPT_DIR}/run.sh" "$@"
    else
        echo "❌ Error: Antigravity-Installer-x86_64.AppImage not found in ${SCRIPT_DIR}." >&2
        exit 1
    fi
fi

chmod +x "${APPIMAGE_BIN}"

# Check if libfuse.so.2 is available on system
HAS_FUSE2=0
if ldconfig -p 2>/dev/null | grep -q "libfuse.so.2"; then
    HAS_FUSE2=1
fi

# If on modern Ubuntu 24.04+ without libfuse2, offer to install or auto fallback
if [ "${HAS_FUSE2}" -eq 0 ]; then
    # Test if direct execution succeeds
    if ! "${APPIMAGE_BIN}" -v >/dev/null 2>&1; then
        echo "ℹ️  libfuse2 / libfuse2t64 is missing (standard on fresh Ubuntu 24.04)."
        echo "⚡ Launching Antigravity Installer using automatic extract-and-run mode..."
        exec "${APPIMAGE_BIN}" --appimage-extract-and-run "$@"
    fi
fi

exec "${APPIMAGE_BIN}" "$@"
