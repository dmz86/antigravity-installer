"""
Freedesktop icon manager for Antigravity Suite.
Extracts icons from ASAR / IDE packages, scales them with GdkPixbuf across all standard
hicolor resolutions (512x512 down to 16x16), places them in /usr/share/pixmaps/ and
/usr/share/icons/hicolor, and refreshes the desktop icon cache.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf

from antigravity_installer.asar import AsarArchive
from antigravity_installer.config import (
    BUNDLED_ICONS_DIR,
    HICOLOR_ICONS_DIR,
    HICOLOR_SIZES,
    INSTALL_DIR_HUB,
    INSTALL_DIR_IDE,
    PIXMAPS_DIR,
)


def get_hub_icon_source() -> Optional[Path]:
    """Finds or extracts the best available icon for Antigravity Hub."""
    bundled = BUNDLED_ICONS_DIR / "antigravity.png"
    if bundled.exists():
        return bundled

    asar_path = INSTALL_DIR_HUB / "resources" / "app.asar"
    if asar_path.exists():
        try:
            tmp_target = Path(f"/tmp/antigravity_hub_icon_{os.getuid()}.png")
            if tmp_target.exists():
                try:
                    tmp_target.unlink()
                except Exception:
                    pass
            archive = AsarArchive(asar_path)
            if archive.extract_file("icon.png", tmp_target):
                return tmp_target
        except Exception:
            pass
    return None


def get_ide_icon_source() -> Optional[Path]:
    """Finds the best available icon for Antigravity IDE."""
    bundled = BUNDLED_ICONS_DIR / "antigravity-ide.png"
    if bundled.exists():
        return bundled

    ide_res_icon = (
        INSTALL_DIR_IDE / "resources" / "app" / "resources" / "linux" / "code.png"
    )
    if ide_res_icon.exists():
        return ide_res_icon
    return None


def get_cli_icon_source() -> Optional[Path]:
    """Finds the ASCII/pixel-art icon for Antigravity CLI."""
    bundled = BUNDLED_ICONS_DIR / "antigravity-cli.png"
    if bundled.exists():
        return bundled
    return None


def register_icon_scales(
    source_icon_path: Path,
    icon_name: str,
    base_icons_dir: Path = HICOLOR_ICONS_DIR,
    pixmaps_dir: Path = PIXMAPS_DIR,
) -> bool:
    """
    Scales source icon to all hicolor resolutions and copies to pixmaps.
    """
    if not source_icon_path.exists():
        return False

    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(source_icon_path))
    except Exception as e:
        print(f"[Icons] Failed to load {source_icon_path}: {e}")
        return False

    # 1. Register to /usr/share/pixmaps/ (512x512 or master)
    try:
        pixmaps_dir.mkdir(parents=True, exist_ok=True)
        master_pixmap = pixmaps_dir / f"{icon_name}.png"
        shutil.copy2(source_icon_path, master_pixmap)
        os.chmod(master_pixmap, 0o644)
    except Exception as e:
        print(f"[Icons] Failed to copy to pixmaps: {e}")

    # 2. Register to hicolor resolutions
    for size in HICOLOR_SIZES:
        try:
            target_dir = base_icons_dir / f"{size}x{size}" / "apps"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{icon_name}.png"

            if pixbuf.get_width() == size and pixbuf.get_height() == size:
                shutil.copy2(source_icon_path, target_file)
            else:
                scaled = pixbuf.scale_simple(
                    size, size, GdkPixbuf.InterpType.BILINEAR
                )
                if scaled:
                    scaled.savev(str(target_file), "png", [], [])

            if target_file.exists():
                os.chmod(target_file, 0o644)
        except Exception as e:
            print(f"[Icons] Error generating {size}x{size} icon for {icon_name}: {e}")

    return True


def remove_icon(
    icon_name: str,
    base_icons_dir: Path = HICOLOR_ICONS_DIR,
    pixmaps_dir: Path = PIXMAPS_DIR,
):
    """Removes all installed icon resolutions for a component."""
    try:
        pixmap_file = pixmaps_dir / f"{icon_name}.png"
        if pixmap_file.exists():
            pixmap_file.unlink()
    except Exception:
        pass

    for size in HICOLOR_SIZES:
        try:
            icon_file = base_icons_dir / f"{size}x{size}" / "apps" / f"{icon_name}.png"
            if icon_file.exists():
                icon_file.unlink()
        except Exception:
            pass


def update_icon_cache(base_icons_dir: Path = HICOLOR_ICONS_DIR):
    """Executes gtk-update-icon-cache to refresh the desktop icon theme."""
    if shutil.which("gtk-update-icon-cache") and base_icons_dir.exists():
        try:
            subprocess.run(
                ["gtk-update-icon-cache", "-q", "-f", "-t", str(base_icons_dir)],
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            print(f"[Icons] gtk-update-icon-cache warning: {e}")
