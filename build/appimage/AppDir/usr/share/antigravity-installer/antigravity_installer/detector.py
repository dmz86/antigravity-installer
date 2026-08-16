"""
System detector for installed Antigravity suite components, versions, and sandbox permissions.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from antigravity_installer.asar import get_asar_package_json
from antigravity_installer.config import (
    BIN_DIR,
    INSTALL_DIR_HUB,
    INSTALL_DIR_IDE,
)


@dataclass
class InstalledState:
    installed: bool
    version: Optional[str] = None
    binary_path: Optional[Path] = None
    install_dir: Optional[Path] = None
    sandbox_ok: bool = False
    details: Optional[str] = None


def check_sandbox_permissions(sandbox_path: Path) -> bool:
    """
    Checks if chrome-sandbox exists, is owned by root, and has SUID permission (4755).
    """
    if not sandbox_path.exists():
        return False
    try:
        stat_info = sandbox_path.stat()
        is_root = (stat_info.st_uid == 0)
        has_suid = bool(stat_info.st_mode & 0o4000)
        is_executable = bool(stat_info.st_mode & 0o0111)
        return is_root and has_suid and is_executable
    except Exception:
        return False


def detect_hub() -> InstalledState:
    """Detects if Antigravity 2.0 (Hub) is installed and gets its version."""
    bin_path = BIN_DIR / "antigravity"
    main_exe = INSTALL_DIR_HUB / "antigravity"
    asar_path = INSTALL_DIR_HUB / "resources" / "app.asar"
    sandbox_path = INSTALL_DIR_HUB / "chrome-sandbox"

    if not (main_exe.exists() or bin_path.exists()):
        return InstalledState(installed=False)

    version: Optional[str] = None
    if asar_path.exists():
        pkg = get_asar_package_json(asar_path)
        if pkg:
            version = pkg.get("version")

    sandbox_ok = check_sandbox_permissions(sandbox_path)

    return InstalledState(
        installed=True,
        version=version,
        binary_path=bin_path if bin_path.exists() else main_exe,
        install_dir=INSTALL_DIR_HUB,
        sandbox_ok=sandbox_ok,
    )


def detect_ide() -> InstalledState:
    """Detects if Antigravity IDE is installed and gets its version."""
    bin_path = BIN_DIR / "antigravity-ide"
    main_exe = INSTALL_DIR_IDE / "antigravity-ide"
    product_json = INSTALL_DIR_IDE / "resources" / "app" / "product.json"
    package_json = INSTALL_DIR_IDE / "resources" / "app" / "package.json"
    sandbox_path = INSTALL_DIR_IDE / "chrome-sandbox"

    if not (main_exe.exists() or bin_path.exists()):
        return InstalledState(installed=False)

    version: Optional[str] = None
    if product_json.exists():
        try:
            with open(product_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("ideVersion") or data.get("version")
        except Exception:
            pass

    if not version and package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version")
        except Exception:
            pass

    sandbox_ok = check_sandbox_permissions(sandbox_path)

    return InstalledState(
        installed=True,
        version=version,
        binary_path=bin_path if bin_path.exists() else main_exe,
        install_dir=INSTALL_DIR_IDE,
        sandbox_ok=sandbox_ok,
    )


def detect_cli() -> InstalledState:
    """Detects if Antigravity CLI (agy) is installed and gets its version."""
    agy_path = shutil.which("agy")
    user_agy = Path.home() / ".local" / "bin" / "agy"
    sys_agy = Path("/usr/local/bin/agy")
    root_agy = Path("/usr/bin/agy")

    found_path: Optional[Path] = None
    if agy_path:
        found_path = Path(agy_path)
    elif user_agy.exists():
        found_path = user_agy
    elif sys_agy.exists():
        found_path = sys_agy
    elif root_agy.exists():
        found_path = root_agy

    if not found_path:
        return InstalledState(installed=False)

    version: Optional[str] = None
    try:
        res = subprocess.run(
            [str(found_path), "--version"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        out = (res.stdout or res.stderr).strip()
        if out:
            # Output might be "1.1.13" or "agy version 1.1.13"
            version = out.split()[-1].lstrip("v")
    except Exception:
        pass

    return InstalledState(
        installed=True,
        version=version,
        binary_path=found_path,
        sandbox_ok=True,
    )


def detect_all() -> Dict[str, InstalledState]:
    """Detects system status for all components."""
    return {
        "hub": detect_hub(),
        "ide": detect_ide(),
        "cli": detect_cli(),
    }
