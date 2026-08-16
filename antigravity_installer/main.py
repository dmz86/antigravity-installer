"""
Main entry point for Google Antigravity Suite Installer & Manager.
Supports both modern Libadwaita GUI mode and non-interactive CLI automation.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from antigravity_installer import __version__
from antigravity_installer.api import fetch_all_releases
from antigravity_installer.config import BUNDLED_ICONS_DIR, get_icon_path
from antigravity_installer.i18n import _, init_i18n, set_language
from antigravity_installer.operations import (
    OperationContext,
    install_cli,
    install_hub,
    install_ide,
    repair_all,
    uninstall_cli,
    uninstall_hub,
    uninstall_ide,
)


def ensure_user_desktop_integration():
    """Ensures local user desktop entry and multi-res icons exist so GNOME dock displays the app icon."""
    try:
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf

        home = Path.home()
        src_icon = get_icon_path("antigravity")
        if not src_icon or not src_icon.exists():
            src_icon = BUNDLED_ICONS_DIR / "antigravity.png"

        if not src_icon or not src_icon.exists():
            return

        hicolor_dir = home / ".local" / "share" / "icons" / "hicolor"
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(src_icon))
        sizes = [512, 256, 128, 64, 48, 32, 16]

        # Generate all hicolor resolutions
        for size in sizes:
            target_dir = hicolor_dir / f"{size}x{size}" / "apps"
            target_dir.mkdir(parents=True, exist_ok=True)
            if size == pixbuf.get_width():
                shutil.copy2(src_icon, target_dir / "google.antigravity.installer.png")
                shutil.copy2(src_icon, target_dir / "antigravity-installer.png")
            else:
                scaled = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
                if scaled:
                    scaled.savev(str(target_dir / "google.antigravity.installer.png"), "png", [], [])
                    scaled.savev(str(target_dir / "antigravity-installer.png"), "png", [], [])

        # Ensure index.theme exists
        index_theme = hicolor_dir / "index.theme"
        if not index_theme.exists():
            dirs_section = ",".join(f"{s}x{s}/apps" for s in sizes)
            entries = "\n".join(
                f"[{s}x{s}/apps]\nSize={s}\nContext=Applications\nType=Fixed\n"
                for s in sizes
            )
            index_theme.write_text(
                f"[Icon Theme]\nName=Hicolor\nComment=Fallback Icon Theme\n"
                f"Hidden=true\nDirectories={dirs_section}\n\n{entries}",
                encoding="utf-8",
            )

        # Pixmaps directory
        user_pixmap_dir = home / ".local" / "share" / "pixmaps"
        user_pixmap_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_icon, user_pixmap_dir / "google.antigravity.installer.png")
        shutil.copy2(src_icon, user_pixmap_dir / "antigravity-installer.png")

        # Desktop entry
        user_apps_dir = home / ".local" / "share" / "applications"
        user_apps_dir.mkdir(parents=True, exist_ok=True)

        appimage_env = os.environ.get("APPIMAGE")
        exec_target = appimage_env if appimage_env else "antigravity-installer"

        desktop_content = f"""[Desktop Entry]
Name=Antigravity Suite Installer
Comment=Installer, manager and updater for Google Antigravity Suite (Hub, IDE, CLI)
Exec={exec_target} %u
Icon=google.antigravity.installer
Terminal=false
Type=Application
Categories=Development;Utility;
StartupNotify=true
StartupWMClass=google.antigravity.installer
"""
        desktop_file = user_apps_dir / "google.antigravity.installer.desktop"
        desktop_file.write_text(desktop_content, encoding="utf-8")
        (user_apps_dir / "antigravity-installer.desktop").write_text(desktop_content, encoding="utf-8")

        if shutil.which("update-desktop-database"):
            subprocess.run(["update-desktop-database", str(user_apps_dir)], capture_output=True)
        if shutil.which("gtk-update-icon-cache"):
            subprocess.run(
                ["gtk-update-icon-cache", "-q", "-f", "-t", str(hicolor_dir)],
                capture_output=True,
            )
    except Exception:
        pass


def run_gui_mode(unknown_args):
    """Initializes and runs the Libadwaita GUI application."""
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import Adw, Gio, GLib

        from antigravity_installer.ui.window import MainWindow
    except Exception as e:
        print("=================================================================")
        print("⚠️  AVVISO / WARNING: Interfaccia grafica GTK4/Libadwaita non trovata.")
        print("   Graphical interface requires GTK4 & Libadwaita packages.")
        print(f"   Dettagli errore: {e}")
        print("-----------------------------------------------------------------")
        print("👉 Per Ubuntu Desktop (22.04 LTS o 24.04 LTS), installa:")
        print("   sudo apt update && sudo apt install gir1.2-adw-1 gir1.2-gtk-4.0 python3-gi")
        print()
        print("👉 In alternativa, puoi eseguire subito il setup da terminale:")
        print("   ./Antigravity-Installer-x86_64.AppImage --non-interactive")
        print("=================================================================")
        sys.exit(1)

    class AntigravityInstallerApp(Adw.Application):
        """Antigravity Suite Installer Application."""

        def __init__(self):
            super().__init__(
                application_id="google.antigravity.installer",
                flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            )

        def do_activate(self):
            win = self.props.active_window
            if not win:
                win = MainWindow(self)
            win.present()

    # Crucial for GNOME / Wayland / X11 dock icon matching
    GLib.set_prgname("google.antigravity.installer")
    GLib.set_application_name(_("app_title"))
    ensure_user_desktop_integration()

    app = AntigravityInstallerApp()
    sys.exit(app.run([sys.argv[0]] + unknown_args))


def run_cli_mode(args):
    """Runs automated CLI operation without GUI."""
    print("==================================================")
    print("🚀 GOOGLE ANTIGRAVITY SUITE INSTALLER (CLI MODE)")
    print("==================================================")

    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get("DESKTOP_SESSION", "")
    if desktop and "gnome" not in desktop.lower() and "ubuntu" not in desktop.lower():
        print(f"⚠️  [Notice] Desktop environment '{desktop}' detected.")
        print("   Antigravity Suite is primarily optimized for GNOME / Ubuntu Desktop.\n")

    ctx = OperationContext(
        on_log=lambda lvl, msg: print(f"[{lvl}] {msg}"),
        on_progress=lambda pct, msg: print(f"[{int(pct*100)}%] {msg}"),
    )

    if args.action == "repair":
        success = repair_all(ctx)
        sys.exit(0 if success else 1)

    elif args.action == "uninstall":
        success = True
        if not uninstall_hub(ctx):
            success = False
        if not uninstall_ide(ctx):
            success = False
        if not uninstall_cli(ctx):
            success = False
        sys.exit(0 if success else 1)

    else:
        # Install
        print("🌐 Fetching release manifests...")
        hub_releases, ide_releases = fetch_all_releases()

        # Find target Hub version
        hub_rel = hub_releases[0]
        if args.hub_version:
            for r in hub_releases:
                if r.version == args.hub_version:
                    hub_rel = r
                    break

        # Find target IDE version
        ide_rel = ide_releases[0]
        if args.ide_version:
            for r in ide_releases:
                if r.version == args.ide_version:
                    ide_rel = r
                    break

        print(f"Installing Hub v{hub_rel.version} and IDE v{ide_rel.version}...")
        success = True
        if not install_hub(hub_rel.version, hub_rel.download_url, ctx, 0.0, 0.45):
            success = False
        if not install_ide(ide_rel.version, ide_rel.download_url, ctx, 0.45, 0.9):
            success = False
        if not install_cli(ctx):
            success = False

        print("==================================================")
        if success:
            print("🎉 ANTIGRAVITY SUITE INSTALLED SUCCESSFULLY!")
        else:
            print("⚠️ Installation finished with errors.")
        print("==================================================")
        sys.exit(0 if success else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Google Antigravity Suite Installer & Manager (GUI & CLI)"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-y", "--non-interactive", action="store_true", help="Run in non-interactive CLI mode")
    parser.add_argument("--action", choices=["install", "uninstall", "repair"], default="install", help="Action to perform in CLI mode")
    parser.add_argument("--hub-version", type=str, help="Specify Antigravity Hub version")
    parser.add_argument("--ide-version", type=str, help="Specify Antigravity IDE version")
    parser.add_argument("--lang", type=str, help="Force language code (it, en, es, fr, de)")

    args, unknown = parser.parse_known_args()

    # Initialize i18n
    init_i18n(args.lang)

    if args.non_interactive:
        run_cli_mode(args)
    else:
        run_gui_mode(unknown)


if __name__ == "__main__":
    main()
