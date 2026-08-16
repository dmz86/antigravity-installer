"""
Live operation progress and log console view for Antigravity Installer.
"""

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk, Pango

from antigravity_installer.config import FALLBACK_LOG_FILE, LOG_FILE
from antigravity_installer.i18n import _


class ViewProgress(Gtk.Box):
    """View displaying animated progress bar, status metrics, and live log console."""

    def __init__(self, on_cancel_requested: Optional[Callable[[], None]] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_cancel_requested = on_cancel_requested

        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build_ui()

    def _build_ui(self):
        # 1. Header status card
        header_card = Adw.Bin()
        header_card.get_style_context().add_class("card")
        header_card.get_style_context().add_class("card-hero")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Spinner & Title Row
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.spinner = Gtk.Spinner()
        self.spinner.start()
        title_box.append(self.spinner)

        self.lbl_title = Gtk.Label(label=_("progress_title"))
        self.lbl_title.get_style_context().add_class("title-large")
        self.lbl_title.set_halign(Gtk.Align.START)
        title_box.append(self.lbl_title)
        vbox.append(title_box)

        # Status text
        self.lbl_status = Gtk.Label(label=_("progress_preparing"))
        self.lbl_status.set_halign(Gtk.Align.START)
        self.lbl_status.set_wrap(True)
        vbox.append(self.lbl_status)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("0%")
        vbox.append(self.progress_bar)

        header_card.set_child(vbox)
        self.append(header_card)

        # 2. Live Console Logs Expander
        self.expander = Adw.ExpanderRow()
        self.expander.set_title(_("show_logs"))
        self.expander.set_subtitle("Live operations output")
        self.expander.set_icon_name("utilities-terminal-symbolic")
        self.expander.set_expanded(True)

        # Scrolled Text View
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_min_content_height(200)
        self.scrolled.set_vexpand(True)
        self.scrolled.get_style_context().add_class("log-scroller")

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_monospace(True)
        self.text_view.get_style_context().add_class("log-view")

        self.buffer = self.text_view.get_buffer()
        self._setup_tags()

        self.scrolled.set_child(self.text_view)

        # Container for scrolled in expander
        expander_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        expander_box.set_margin_top(8)
        expander_box.set_margin_bottom(8)
        expander_box.set_margin_start(8)
        expander_box.set_margin_end(8)
        expander_box.append(self.scrolled)

        # Log path bar and Open button
        log_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.lbl_log_path = Gtk.Label(label=f"📄 {LOG_FILE}")
        self.lbl_log_path.get_style_context().add_class("subtitle-dim")
        self.lbl_log_path.set_halign(Gtk.Align.START)
        self.lbl_log_path.set_hexpand(True)
        log_bar.append(self.lbl_log_path)

        self.btn_open_log = Gtk.Button.new_from_icon_name("document-open-symbolic")
        self.btn_open_log.set_tooltip_text("Open log file")
        self.btn_open_log.connect("clicked", lambda b: self._open_log_file())
        log_bar.append(self.btn_open_log)

        expander_box.append(log_bar)

        self.expander.add_row(expander_box)
        self.append(self.expander)

    def _open_log_file(self):
        import subprocess
        target = LOG_FILE if LOG_FILE.exists() else FALLBACK_LOG_FILE
        if target.exists():
            try:
                subprocess.Popen(["xdg-open", str(target)])
            except Exception:
                pass

    def _setup_tags(self):
        """Sets up color tags for log levels."""
        table = self.buffer.get_tag_table()

        tag_info = Gtk.TextTag.new("INFO")
        tag_info.set_property("foreground", "#58a6ff")
        table.add(tag_info)

        tag_success = Gtk.TextTag.new("SUCCESS")
        tag_success.set_property("foreground", "#3fb950")
        tag_success.set_property("weight", Pango.Weight.BOLD)
        table.add(tag_success)

        tag_warning = Gtk.TextTag.new("WARNING")
        tag_warning.set_property("foreground", "#d29922")
        table.add(tag_warning)

        tag_error = Gtk.TextTag.new("ERROR")
        tag_error.set_property("foreground", "#f85149")
        tag_error.set_property("weight", Pango.Weight.BOLD)
        table.add(tag_error)

        tag_bold = Gtk.TextTag.new("BOLD")
        tag_bold.set_property("weight", Pango.Weight.BOLD)
        table.add(tag_bold)

    def reset(self, title: Optional[str] = None):
        """Resets progress bar and log buffer for a new run."""
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0%")
        self.spinner.start()
        self.lbl_title.set_text(title or _("progress_title"))
        self.lbl_status.set_text(_("progress_preparing"))
        self.buffer.set_text("")

    def update_progress(self, fraction: float, status_msg: str):
        """Updates progress bar and text smoothly."""
        pct = max(0.0, min(1.0, fraction))
        self.progress_bar.set_fraction(pct)
        self.progress_bar.set_text(f"{int(pct * 100)}%")
        if status_msg:
            self.lbl_status.set_text(status_msg)

    def append_log(self, level: str, text: str):
        """Appends formatted line to the log console and scrolls to bottom."""
        end_iter = self.buffer.get_end_iter()

        prefix = f"[{level}] "
        self.buffer.insert_with_tags_by_name(end_iter, prefix, level)

        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, f"{text}\n")

        # Scroll to bottom
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def finish_state(self, success: bool):
        self.spinner.stop()
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("100%" if success else "Error")
        self.lbl_status.set_text(
            _("progress_complete") if success else _("progress_error")
        )

    def refresh_translations(self):
        self.lbl_title.set_text(_("progress_title"))
        self.expander.set_title(_("show_logs"))
