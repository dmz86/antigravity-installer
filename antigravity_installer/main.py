"""
Main entry point for Google Antigravity Suite Installer & Manager.
Supports both modern Libadwaita GUI mode and non-interactive CLI automation.
"""

import argparse
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib

from antigravity_installer import __version__
from antigravity_installer.api import fetch_all_releases
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
from antigravity_installer.ui.window import MainWindow


class AntigravityInstallerApp(Adw.Application):
    """Antigravity Suite Installer Application."""

    def __init__(self):
        super().__init__(
            application_id="google.antigravity.installer",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        GLib.set_prgname("google.antigravity.installer")
        GLib.set_application_name(_("app_title"))

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(self)
        win.present()


def run_cli_mode(args):
    """Runs automated CLI operation without GUI."""
    print("==================================================")
    print("🚀 GOOGLE ANTIGRAVITY SUITE INSTALLER (CLI MODE)")
    print("==================================================")

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
        # Launch Adw.Application GUI
        app = AntigravityInstallerApp()
        # Pass remaining arguments to GTK app
        sys.exit(app.run([sys.argv[0]] + unknown))


if __name__ == "__main__":
    main()
