#!/usr/bin/env bash
# =================================================================
# Google Antigravity Suite Graphical Installer & Manager Launcher
# =================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run Python GUI Application
exec python3 -m antigravity_installer.main "$@"
