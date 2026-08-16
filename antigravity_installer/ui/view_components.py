"""
Component selection and version configuration view for Antigravity Installer.
"""

import os
from typing import Callable, Dict, List, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from antigravity_installer.config import (
    COMPONENTS,
    ComponentMeta,
    ReleaseInfo,
    get_icon_path,
)
from antigravity_installer.detector import InstalledState
from antigravity_installer.i18n import _


class ComponentRow(Adw.ActionRow):
    """Interactive row for a single Antigravity component."""

    def __init__(
        self,
        meta: ComponentMeta,
        installed_state: InstalledState,
        releases: List[ReleaseInfo],
        on_toggle: Optional[Callable[[str, bool], None]] = None,
    ):
        super().__init__()
        self.meta = meta
        self.installed_state = installed_state
        self.releases = releases
        self.on_toggle = on_toggle

        self.set_title(GLib.markup_escape_text(_(meta.name_key)))
        self.set_subtitle(GLib.markup_escape_text(_(meta.desc_key)))

        # Prefix Checkbox/Switch
        self.switch = Gtk.Switch()
        self.switch.set_active(meta.default_enabled)
        self.switch.set_valign(Gtk.Align.CENTER)
        self.switch.connect("notify::active", self._on_switch_changed)
        self.add_prefix(self.switch)

        # Real Product Icon Image
        icon_path = get_icon_path(meta.icon_name)
        if icon_path and icon_path.exists():
            self.icon_image = Gtk.Image.new_from_file(str(icon_path))
            self.icon_image.set_pixel_size(42)
            self.icon_image.set_valign(Gtk.Align.CENTER)
            self.icon_image.set_margin_start(6)
            self.icon_image.set_margin_end(6)
            self.add_prefix(self.icon_image)
        else:
            self.set_icon_name(meta.icon_name)

        # Right box for Status Badge and Version Selector
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.right_box.set_valign(Gtk.Align.CENTER)

        # Status badge label
        self.badge = Gtk.Label()
        self.badge.set_valign(Gtk.Align.CENTER)
        self._update_badge()
        self.right_box.append(self.badge)

        # Version DropDown
        self.version_dropdown = Gtk.DropDown()
        self.version_dropdown.set_valign(Gtk.Align.CENTER)
        self._populate_versions()
        if meta.supports_versions:
            self.right_box.append(self.version_dropdown)

        self.add_suffix(self.right_box)

    def _on_switch_changed(self, switch, gparam):
        if self.on_toggle:
            self.on_toggle(self.meta.id, switch.get_active())

    def _update_badge(self):
        ctx = self.badge.get_style_context()
        for cls in ("badge-installed", "badge-update", "badge-none"):
            ctx.remove_class(cls)

        if self.installed_state.installed:
            ver = self.installed_state.version or ""
            # Check if update available
            if self.releases and ver and self.releases[0].version != ver:
                self.badge.set_text(f"{_('status_update_available')} (v{ver} → v{self.releases[0].version})")
                ctx.add_class("badge-update")
            else:
                self.badge.set_text(f"{_('status_installed')}: v{ver}" if ver else _("status_installed"))
                ctx.add_class("badge-installed")
        else:
            self.badge.set_text(_("status_not_installed"))
            ctx.add_class("badge-none")

    def _populate_versions(self):
        if not self.meta.supports_versions:
            return

        model = Gtk.StringList()
        if self.releases:
            for idx, r in enumerate(self.releases):
                tag = f" ({_('latest_badge')})" if idx == 0 else ""
                model.append(f"v{r.version}{tag}")
        else:
            model.append("v2.8.1 (Latest)")

        self.version_dropdown.set_model(model)
        self.version_dropdown.set_selected(0)

    def get_selected_version(self) -> Optional[ReleaseInfo]:
        if not self.meta.supports_versions or not self.releases:
            return None
        idx = self.version_dropdown.get_selected()
        if 0 <= idx < len(self.releases):
            return self.releases[idx]
        return self.releases[0] if self.releases else None

    def is_checked(self) -> bool:
        return self.switch.get_active()

    def set_checked(self, checked: bool):
        self.switch.set_active(checked)

    def update_data(self, installed_state: InstalledState, releases: List[ReleaseInfo]):
        self.installed_state = installed_state
        self.releases = releases
        self._update_badge()
        self._populate_versions()


class ViewComponents(Gtk.Box):
    """View displaying component list, version choices, and operation trigger."""

    def __init__(
        self,
        on_start_operation: Callable[[str, dict], None],
        on_refresh_requested: Callable[[], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_start_operation = on_start_operation
        self.on_refresh_requested = on_refresh_requested
        self.rows: Dict[str, ComponentRow] = {}

        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(20)
        self.set_margin_end(20)

        self._build_ui()

    def _build_ui(self):
        # 0. Non-GNOME Desktop Alert Banner
        self.banner = Adw.Banner()
        self.banner.set_button_label("OK")
        self.banner.connect("button-clicked", lambda b: self.banner.set_revealed(False))
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get("DESKTOP_SESSION", "")
        if desktop and "gnome" not in desktop.lower() and "ubuntu" not in desktop.lower():
            msg = _("non_gnome_alert").replace("{desktop}", desktop)
            self.banner.set_title(msg)
            self.banner.set_revealed(True)
        else:
            self.banner.set_revealed(False)
        self.append(self.banner)

        # 0.1 GitHub Installer Update Banner
        self.update_banner = Adw.Banner()
        self.update_banner.set_button_label(_("btn_download_update"))
        self._update_url = "https://github.com/dmz86/antigravity-installer/releases/latest"
        self._last_update_info = None

        def _on_update_clicked(b):
            try:
                import gi
                gi.require_version("Gtk", "4.0")
                gi.require_version("Gdk", "4.0")
                from gi.repository import Gtk, Gdk
                Gtk.show_uri(self.get_root(), self._update_url, Gdk.CURRENT_TIME)
            except Exception:
                import subprocess
                subprocess.Popen(["xdg-open", self._update_url])

        self.update_banner.connect("button-clicked", _on_update_clicked)
        self.update_banner.set_revealed(False)
        self.append(self.update_banner)

        # 0.5 App Header / Hero Section with Antigravity Logo
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        header_box.set_halign(Gtk.Align.CENTER)
        header_box.set_margin_top(6)
        header_box.set_margin_bottom(16)

        # Logo icon
        self.header_logo = Gtk.Image()
        logo_path = get_icon_path("antigravity") or get_icon_path("google.antigravity.installer")
        if logo_path and logo_path.exists():
            self.header_logo.set_from_file(str(logo_path))
            self.header_logo.set_pixel_size(72)
        else:
            self.header_logo.set_from_icon_name("application-x-executable")
            self.header_logo.set_pixel_size(72)

        header_box.append(self.header_logo)

        # Title
        self.header_title = Gtk.Label(label=_("app_title"))
        self.header_title.add_css_class("title-1")
        header_box.append(self.header_title)

        # Subtitle
        self.header_subtitle = Gtk.Label(label=_("app_subtitle"))
        self.header_subtitle.add_css_class("dim-label")
        header_box.append(self.header_subtitle)

        self.append(header_box)

        # 1. Mode selector card
        mode_group = Adw.PreferencesGroup()
        mode_group.set_title(_("mode_label"))

        self.mode_row = Adw.ComboRow()
        self.mode_row.set_title(_("mode_label"))
        self.mode_row.set_subtitle(_("components_desc"))
        self.mode_row.set_icon_name("system-software-install")

        mode_model = Gtk.StringList()
        mode_model.append(_("action_install_update"))
        mode_model.append(_("action_uninstall"))
        mode_model.append(_("action_repair"))
        self.mode_row.set_model(mode_model)
        self.mode_row.set_selected(0)
        self.mode_row.connect("notify::selected", self._on_mode_changed)

        mode_group.add(self.mode_row)
        self.append(mode_group)

        # 2. Components Group
        self.comp_group = Adw.PreferencesGroup()
        self.comp_group.set_title(_("components_title"))
        self.comp_group.set_description(_("components_desc"))

        # Add initial placeholder rows
        for meta in COMPONENTS:
            row = ComponentRow(
                meta=meta,
                installed_state=InstalledState(installed=False),
                releases=[],
                on_toggle=self._on_component_toggled,
            )
            self.rows[meta.id] = row
            self.comp_group.add(row)

        self.append(self.comp_group)

        # 3. Action bar at bottom
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.action_box.set_margin_top(8)

        # Refresh button
        self.btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.btn_refresh.set_tooltip_text(_("btn_refresh"))
        self.btn_refresh.connect("clicked", lambda b: self.on_refresh_requested())
        self.action_box.append(self.btn_refresh)

        # Status note
        self.lbl_status = Gtk.Label(label=_("checking_versions"))
        self.lbl_status.set_hexpand(True)
        self.lbl_status.set_halign(Gtk.Align.START)
        self.lbl_status.get_style_context().add_class("subtitle-dim")
        self.action_box.append(self.lbl_status)

        # Start primary button
        self.btn_start = Gtk.Button(label=_("btn_start_install"))
        self.btn_start.get_style_context().add_class("suggested-action")
        self.btn_start.get_style_context().add_class("big-btn")
        self.btn_start.connect("clicked", self._on_start_clicked)
        self.action_box.append(self.btn_start)

        self.append(self.action_box)

    def _on_mode_changed(self, combo, gparam):
        idx = combo.get_selected()
        ctx = self.btn_start.get_style_context()
        ctx.remove_class("suggested-action")
        ctx.remove_class("destructive-action")

        if idx == 0:  # Install / Update
            self.btn_start.set_label(_("btn_start_install"))
            ctx.add_class("suggested-action")
        elif idx == 1:  # Uninstall
            self.btn_start.set_label(_("btn_start_uninstall"))
            ctx.add_class("destructive-action")
        else:  # Repair
            self.btn_start.set_label(_("btn_start_repair"))
            ctx.add_class("suggested-action")

    def _on_component_toggled(self, comp_id: str, is_active: bool):
        # Update start button sensitivity based on selection
        has_any = any(r.is_checked() for r in self.rows.values())
        mode_idx = self.mode_row.get_selected()
        self.btn_start.set_sensitive(has_any or mode_idx == 2)

    def _on_start_clicked(self, btn):
        mode_idx = self.mode_row.get_selected()
        if mode_idx == 0:
            # Install / Update
            payload = {"items": {}}
            for comp_id, row in self.rows.items():
                if row.is_checked():
                    rel = row.get_selected_version()
                    if rel:
                        payload["items"][comp_id] = {
                            "version": rel.version,
                            "url": rel.download_url,
                        }
                    else:
                        payload["items"][comp_id] = True
            self.on_start_operation("install", payload)

        elif mode_idx == 1:
            # Uninstall
            selected_comps = [
                comp_id for comp_id, row in self.rows.items() if row.is_checked()
            ]
            self.on_start_operation("uninstall", {"components": selected_comps})

        elif mode_idx == 2:
            # Repair
            self.on_start_operation("repair", {})

    def set_system_data(
        self,
        installed: Dict[str, InstalledState],
        hub_releases: List[ReleaseInfo],
        ide_releases: List[ReleaseInfo],
    ):
        """Updates UI rows with detected installed state and releases."""
        if "hub" in self.rows:
            self.rows["hub"].update_data(
                installed.get("hub", InstalledState(False)), hub_releases
            )
        if "ide" in self.rows:
            self.rows["ide"].update_data(
                installed.get("ide", InstalledState(False)), ide_releases
            )
        if "cli" in self.rows:
            self.rows["cli"].update_data(
                installed.get("cli", InstalledState(False)), []
            )

        self.lbl_status.set_text(_("versions_loaded"))

    def set_installer_update(self, update_info: Optional[dict]):
        """Reveals banner if a newer version of the installer is available on GitHub."""
        self._last_update_info = update_info
        if update_info:
            self._update_url = update_info.get("url", "https://github.com/dmz86/antigravity-installer/releases/latest")
            msg = _("installer_update_available").replace("{version}", update_info.get("version", ""))
            self.update_banner.set_title(msg)
            self.update_banner.set_button_label(_("btn_download_update"))
            self.update_banner.set_revealed(True)
        else:
            self.update_banner.set_revealed(False)

    def refresh_translations(self):
        """Updates all strings in view when language changes."""
        self.header_title.set_label(_("app_title"))
        self.header_subtitle.set_label(_("app_subtitle"))

        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "") or os.environ.get("DESKTOP_SESSION", "")
        if desktop and "gnome" not in desktop.lower() and "ubuntu" not in desktop.lower():
            msg = _("non_gnome_alert").replace("{desktop}", desktop)
            self.banner.set_title(msg)

        if self._last_update_info:
            msg = _("installer_update_available").replace("{version}", self._last_update_info.get("version", ""))
            self.update_banner.set_title(msg)
            self.update_banner.set_button_label(_("btn_download_update"))

        self.comp_group.set_title(_("components_title"))
        self.comp_group.set_description(_("components_desc"))
        self.mode_row.set_title(_("mode_label"))
        self.mode_row.set_subtitle(_("components_desc"))

        mode_model = Gtk.StringList()
        mode_model.append(_("action_install_update"))
        mode_model.append(_("action_uninstall"))
        mode_model.append(_("action_repair"))
        curr_idx = self.mode_row.get_selected()
        self.mode_row.set_model(mode_model)
        self.mode_row.set_selected(curr_idx)

        for comp_id, row in self.rows.items():
            row.set_title(_(row.meta.name_key))
            row.set_subtitle(_(row.meta.desc_key))
            row._update_badge()
            row._populate_versions()

        self._on_mode_changed(self.mode_row, None)
