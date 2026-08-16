"""
Main Application Window for Antigravity Suite Installer.
Coordinates ViewStack navigation, async data fetching, threading, and theme/i18n switching.
"""

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gdk, Gio, Gtk

from antigravity_installer import __version__
from antigravity_installer.api import check_installer_github_update, fetch_all_releases
from antigravity_installer.config import ReleaseInfo
from antigravity_installer.detector import InstalledState, detect_all
from antigravity_installer.i18n import (
    AVAILABLE_LANGUAGES,
    _,
    add_language_listener,
    get_current_language,
    set_language,
)
from antigravity_installer.polkit import run_privileged_worker
from antigravity_installer.ui.view_components import ViewComponents
from antigravity_installer.ui.view_finish import ViewFinish
from antigravity_installer.ui.view_progress import ViewProgress


class MainWindow(Adw.ApplicationWindow):
    """Main window with Adw.HeaderBar and 3-page ViewStack."""

    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.set_title(_("app_title"))
        self.set_default_size(780, 680)

        # State storage
        self.installed_state: Dict[str, InstalledState] = {}
        self.hub_releases: List[ReleaseInfo] = []
        self.ide_releases: List[ReleaseInfo] = []
        self.sdk_version: Optional[str] = None
        self.current_op_type = "install"

        # Theme & CSS & Icons
        self._load_custom_css()
        self._register_icon_theme()
        self.set_icon_name("google.antigravity.installer")

        # Build UI
        self._build_ui()

        # Connect language listener
        add_language_listener(self._on_language_changed)

        # Start initial async load
        self._start_data_fetch()

        # Check if first run from portable AppImage to offer stable /opt install
        GLib.idle_add(self._check_first_run_opt_install)

    def _register_icon_theme(self):
        from antigravity_installer.config import BUNDLED_ICONS_DIR
        display = Gdk.Display.get_default()
        if display and BUNDLED_ICONS_DIR.exists():
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_search_path(str(BUNDLED_ICONS_DIR))
            icon_theme.add_search_path(str(BUNDLED_ICONS_DIR.parent))

    def _load_custom_css(self):
        css_file = Path(__file__).parent / "style.css"
        if css_file.exists():
            provider = Gtk.CssProvider()
            provider.load_from_path(str(css_file))
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # 1. HeaderBar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Gtk.Label(label=_("app_title")))

        # Language selection menu button
        self.btn_lang = Gtk.MenuButton()
        self.btn_lang.set_icon_name("preferences-desktop-locale-symbolic")
        self.btn_lang.set_tooltip_text(_("language"))
        self._build_language_menu()
        self.header.pack_end(self.btn_lang)

        # Dark/Light theme toggle
        self.btn_theme = Gtk.Button.new_from_icon_name("weather-clear-night-symbolic")
        self.btn_theme.set_tooltip_text(_("theme"))
        self.btn_theme.connect("clicked", self._toggle_dark_theme)
        self.header.pack_end(self.btn_theme)

        # About button
        self.btn_about = Gtk.Button.new_from_icon_name("help-about-symbolic")
        self.btn_about.set_tooltip_text(_("about_title"))
        self.btn_about.connect("clicked", self._show_about_dialog)
        self.header.pack_end(self.btn_about)

        main_box.append(self.header)

        # 2. ViewStack with 3 pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_vexpand(True)

        # View 1: Components
        self.view_comp = ViewComponents(
            on_start_operation=self._on_start_operation,
            on_refresh_requested=self._start_data_fetch,
        )
        self.stack.add_named(self.view_comp, "components")

        # View 2: Progress
        self.view_prog = ViewProgress(
            on_cancel_requested=self._on_cancel_requested,
        )
        self.stack.add_named(self.view_prog, "progress")

        # View 3: Finish
        self.view_fini = ViewFinish(
            on_done_clicked=lambda: self.close(),
            on_back_clicked=lambda: self.stack.set_visible_child_name("components"),
        )
        self.stack.add_named(self.view_fini, "finish")

        # Wrap in ScrolledWindow for smaller screen adaptability
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.stack)
        scroller.set_vexpand(True)
        main_box.append(scroller)

        self.set_content(main_box)

    def _build_language_menu(self):
        menu = Gio.Menu()
        curr_lang = get_current_language()

        for code, name in AVAILABLE_LANGUAGES:
            tag = " ✓" if code == curr_lang else ""
            item = Gio.MenuItem.new(f"{name}{tag}", f"app.lang_{code}")
            menu.append_item(item)

            # Register action on app
            action = Gio.SimpleAction.new(f"lang_{code}", None)
            action.connect("activate", lambda a, p, c=code: set_language(c))
            self.get_application().add_action(action)

        self.btn_lang.set_menu_model(menu)

    def _toggle_dark_theme(self, btn):
        style_mgr = Adw.StyleManager.get_default()
        if style_mgr.get_dark():
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            btn.set_icon_name("weather-clear-night-symbolic")
        else:
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            btn.set_icon_name("weather-clear-symbolic")

    def _show_about_dialog(self, btn):
        if hasattr(Adw, "AboutDialog"):
            dialog = Adw.AboutDialog(
                application_name=_("app_title"),
                application_icon="google-antigravity",
                version=__version__,
                developer_name="dmz86 / Google DeepMind Antigravity Community",
                comments=_("about_desc"),
                website="https://github.com/dmz86/antigravity-installer",
                issue_url="https://github.com/dmz86/antigravity-installer/issues",
                support_url="https://antigravity.google",
            )
            dialog.present(self)
        else:
            dialog = Adw.AboutWindow(
                transient_for=self,
                application_name=_("app_title"),
                application_icon="google-antigravity",
                version=__version__,
                developer_name="dmz86 / Google DeepMind Antigravity Community",
                comments=_("about_desc"),
                website="https://github.com/dmz86/antigravity-installer",
                issue_url="https://github.com/dmz86/antigravity-installer/issues",
                support_url="https://antigravity.google",
            )
            dialog.present()

    def _check_first_run_opt_install(self):
        """Checks if running from an uninstalled AppImage and prompts user for /opt installation."""
        appimage_path = os.environ.get("APPIMAGE", "")
        if not appimage_path:
            return False

        if appimage_path.startswith("/opt/antigravity-installer/"):
            return False

        config_dir = Path.home() / ".config" / "antigravity-installer"
        config_file = config_dir / "settings.json"
        config_data = {}
        if config_file.exists():
            try:
                config_data = json.loads(config_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        if config_data.get("opt_prompt_dismissed"):
            return False

        def on_install_confirmed():
            config_dir.mkdir(parents=True, exist_ok=True)
            config_data["opt_prompt_dismissed"] = True
            config_data["opt_installed"] = True
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            def worker():
                run_privileged_worker(
                    action_type="install_self",
                    payload={"source_appimage": appimage_path},
                )
            threading.Thread(target=worker, daemon=True).start()

        def on_install_declined():
            config_dir.mkdir(parents=True, exist_ok=True)
            config_data["opt_prompt_dismissed"] = True
            config_data["opt_installed"] = False
            config_file.write_text(json.dumps(config_data), encoding="utf-8")

            user_desk = Path.home() / ".local" / "share" / "applications" / "google.antigravity.installer.desktop"
            if user_desk.exists():
                txt = user_desk.read_text(encoding="utf-8")
                if "NoDisplay=" in txt:
                    txt = "\n".join(
                        line if not line.startswith("NoDisplay=") else "NoDisplay=true"
                        for line in txt.splitlines()
                    )
                else:
                    txt += "\nNoDisplay=true\n"
                user_desk.write_text(txt, encoding="utf-8")
                if shutil.which("update-desktop-database"):
                    subprocess.run(["update-desktop-database", str(user_desk.parent)], capture_output=True)

        if hasattr(Adw, "AlertDialog"):
            dialog = Adw.AlertDialog(
                heading=_("dialog_opt_install_title"),
                body=_("dialog_opt_install_body"),
            )
            dialog.add_response("cancel", _("btn_not_now"))
            dialog.add_response("install", _("btn_install_opt"))
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("install")
            dialog.set_close_response("cancel")

            def on_response(d, response_id):
                if response_id == "install":
                    on_install_confirmed()
                else:
                    on_install_declined()

            dialog.connect("response", on_response)
            dialog.present(self)

        elif hasattr(Adw, "MessageDialog"):
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading=_("dialog_opt_install_title"),
                body=_("dialog_opt_install_body"),
            )
            dialog.add_response("cancel", _("btn_not_now"))
            dialog.add_response("install", _("btn_install_opt"))
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("install")
            dialog.set_close_response("cancel")

            def on_response(d, response_id):
                if response_id == "install":
                    on_install_confirmed()
                else:
                    on_install_declined()

            dialog.connect("response", on_response)
            dialog.present()

        return False

    def _start_data_fetch(self):
        """Fetches installed state, API releases, and GitHub installer updates in background thread."""
        self.view_comp.lbl_status.set_text(_("checking_versions"))

        def worker():
            try:
                installed = detect_all()
                hub, ide = fetch_all_releases()
                inst_update = check_installer_github_update(__version__)

                def update_ui():
                    self.installed_state = installed
                    self.hub_releases = hub
                    self.ide_releases = ide
                    self.view_comp.set_system_data(installed, hub, ide)
                    self.view_comp.set_installer_update(inst_update)
                    return False

                GLib.idle_add(update_ui)
            except Exception as e:
                print(f"[Main] Error in data fetch: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _on_start_operation(self, op_type: str, payload: dict):
        """Starts privileged or unprivileged operation in background."""
        self.current_op_type = op_type
        self.view_prog.reset(_("progress_title"))
        self.stack.set_visible_child_name("progress")

        def on_log_cb(level: str, text: str):
            GLib.idle_add(lambda: self.view_prog.append_log(level, text))

        def on_progress_cb(pct: float, msg: str):
            GLib.idle_add(lambda: self.view_prog.update_progress(pct, msg))

        def worker():
            success = run_privileged_worker(
                action_type=op_type,
                payload=payload,
                on_log=on_log_cb,
                on_progress=on_progress_cb,
            )

            def finalize_ui():
                self.view_prog.finish_state(success)
                self.view_fini.set_result(success, operation_type=op_type)
                # Auto switch to finish page after short delay
                GLib.timeout_add(
                    1200, lambda: self.stack.set_visible_child_name("finish")
                )
                # Also refresh detected data
                self._start_data_fetch()
                return False

            GLib.idle_add(finalize_ui)

        threading.Thread(target=worker, daemon=True).start()

    def _on_cancel_requested(self):
        self.stack.set_visible_child_name("components")

    def _on_language_changed(self, lang_code: str):
        """Updates all window titles and subviews when language changes."""
        self.set_title(_("app_title"))
        self.header.set_title_widget(Gtk.Label(label=_("app_title")))
        self._build_language_menu()
        self.view_comp.refresh_translations()
        self.view_prog.refresh_translations()
        self.view_fini.refresh_translations()
