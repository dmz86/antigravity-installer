"""
Finished/Summary view with success/error status and quick launch buttons.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from antigravity_installer.config import (
    BIN_DIR,
    INSTALL_DIR_HUB,
    INSTALL_DIR_IDE,
    get_icon_path,
)
from antigravity_installer.i18n import _


class ViewFinish(Gtk.Box):
    """View displaying final completion status and launcher shortcuts."""

    def __init__(
        self,
        on_done_clicked: Callable[[], None],
        on_back_clicked: Callable[[], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_done_clicked = on_done_clicked
        self.on_back_clicked = on_back_clicked

        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build_ui()

    def _build_ui(self):
        # Status page banner
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("emblem-default-symbolic")
        self.status_page.set_title(_("finish_title_success"))
        self.status_page.set_description(_("finish_desc_success"))

        # Launch buttons container
        self.launch_group = Adw.PreferencesGroup()
        self.launch_group.set_title("Quick Launch")

        # Launch Hub Button Row
        self.row_launch_hub = Adw.ActionRow()
        self.row_launch_hub.set_title(_("btn_launch_hub"))
        self.row_launch_hub.set_subtitle("Experience liftoff")
        hub_icon_path = get_icon_path("antigravity")
        if hub_icon_path and hub_icon_path.exists():
            img = Gtk.Image.new_from_file(str(hub_icon_path))
            img.set_pixel_size(36)
            img.set_margin_start(4)
            img.set_margin_end(6)
            self.row_launch_hub.add_prefix(img)
        else:
            self.row_launch_hub.set_icon_name("antigravity")

        btn_hub = Gtk.Button(label="Launch")
        btn_hub.set_valign(Gtk.Align.CENTER)
        btn_hub.get_style_context().add_class("suggested-action")
        btn_hub.connect("clicked", lambda b: self._launch_app([str(BIN_DIR / "antigravity")]))
        self.row_launch_hub.add_suffix(btn_hub)
        self.launch_group.add(self.row_launch_hub)

        # Launch IDE Button Row
        self.row_launch_ide = Adw.ActionRow()
        self.row_launch_ide.set_title(_("btn_launch_ide"))
        self.row_launch_ide.set_subtitle("AI-first Integrated Development Environment")
        ide_icon_path = get_icon_path("antigravity-ide")
        if ide_icon_path and ide_icon_path.exists():
            img = Gtk.Image.new_from_file(str(ide_icon_path))
            img.set_pixel_size(36)
            img.set_margin_start(4)
            img.set_margin_end(6)
            self.row_launch_ide.add_prefix(img)
        else:
            self.row_launch_ide.set_icon_name("antigravity-ide")

        btn_ide = Gtk.Button(label="Launch")
        btn_ide.set_valign(Gtk.Align.CENTER)
        btn_ide.get_style_context().add_class("suggested-action")
        btn_ide.connect("clicked", lambda b: self._launch_app([str(BIN_DIR / "antigravity-ide")]))
        self.row_launch_ide.add_suffix(btn_ide)
        self.launch_group.add(self.row_launch_ide)

        # Launch CLI Button Row
        self.row_launch_cli = Adw.ActionRow()
        self.row_launch_cli.set_title(_("btn_launch_cli"))
        self.row_launch_cli.set_subtitle("Terminal interface")
        cli_icon_path = get_icon_path("antigravity-cli")
        if cli_icon_path and cli_icon_path.exists():
            img = Gtk.Image.new_from_file(str(cli_icon_path))
            img.set_pixel_size(36)
            img.set_margin_start(4)
            img.set_margin_end(6)
            self.row_launch_cli.add_prefix(img)
        else:
            self.row_launch_cli.set_icon_name("utilities-terminal")

        btn_cli = Gtk.Button(label="Launch")
        btn_cli.set_valign(Gtk.Align.CENTER)
        btn_cli.connect("clicked", lambda b: self._launch_terminal_agy())
        self.row_launch_cli.add_suffix(btn_cli)
        self.launch_group.add(self.row_launch_cli)

        # Action Buttons (Back & Done)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(16)

        self.btn_back = Gtk.Button(label=_("btn_back"))
        self.btn_back.get_style_context().add_class("big-btn")
        self.btn_back.connect("clicked", lambda b: self.on_back_clicked())
        btn_box.append(self.btn_back)

        self.btn_done = Gtk.Button(label=_("btn_finish"))
        self.btn_done.get_style_context().add_class("suggested-action")
        self.btn_done.get_style_context().add_class("big-btn")
        self.btn_done.connect("clicked", lambda b: self.on_done_clicked())
        btn_box.append(self.btn_done)

        # Add everything to main layout
        self.append(self.status_page)
        self.append(self.launch_group)
        self.append(btn_box)

    def _launch_app(self, cmd_args):
        try:
            subprocess.Popen(
                cmd_args,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[Finish] Failed to launch {cmd_args}: {e}")

    def _launch_terminal_agy(self):
        terminals = [
            ["gnome-terminal", "--", "agy"],
            ["ptyxis", "--", "agy"],
            ["konsole", "-e", "agy"],
            ["xfce4-terminal", "-e", "agy"],
            ["xterm", "-e", "agy"],
        ]
        for term in terminals:
            if shutil.which(term[0]):
                try:
                    subprocess.Popen(
                        term,
                        start_new_session=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except Exception:
                    pass

    def set_result(self, success: bool, operation_type: str = "install"):
        if success:
            self.status_page.set_icon_name("emblem-default-symbolic")
            self.status_page.set_title(_("finish_title_success"))
            self.status_page.set_description(_("finish_desc_success"))
            self.launch_group.set_visible(operation_type != "uninstall")
        else:
            self.status_page.set_icon_name("dialog-error-symbolic")
            self.status_page.set_title(_("finish_title_error"))
            self.status_page.set_description(_("finish_desc_error"))
            self.launch_group.set_visible(False)

        # Check binary existence for launch rows
        hub_exists = (BIN_DIR / "antigravity").exists() or (INSTALL_DIR_HUB / "antigravity").exists()
        ide_exists = (BIN_DIR / "antigravity-ide").exists() or (INSTALL_DIR_IDE / "antigravity-ide").exists()
        cli_exists = shutil.which("agy") is not None

        self.row_launch_hub.set_visible(hub_exists)
        self.row_launch_ide.set_visible(ide_exists)
        self.row_launch_cli.set_visible(cli_exists)

    def refresh_translations(self):
        self.btn_back.set_label(_("btn_back"))
        self.btn_done.set_label(_("btn_finish"))
        self.row_launch_hub.set_title(_("btn_launch_hub"))
        self.row_launch_ide.set_title(_("btn_launch_ide"))
        self.row_launch_cli.set_title(_("btn_launch_cli"))
