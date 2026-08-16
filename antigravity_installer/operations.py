"""
Execution engine for Antigravity Suite operations:
Download, Install, Update, Uninstall, Repair, and Sandbox Permission setups.
"""

import os
import shutil
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional

from antigravity_installer.config import (
    APPLICATIONS_DIR,
    BIN_DIR,
    DESKTOP_ENTRY_CLI,
    DESKTOP_ENTRY_HUB,
    DESKTOP_ENTRY_HUB_URL,
    DESKTOP_ENTRY_IDE,
    HICOLOR_ICONS_DIR,
    INSTALL_DIR_HUB,
    INSTALL_DIR_IDE,
    PIXMAPS_DIR,
    TMP_DOWNLOAD_DIR,
    append_to_logfile,
)
from antigravity_installer.i18n import _
from antigravity_installer.icons import (
    get_cli_icon_source,
    get_hub_icon_source,
    get_ide_icon_source,
    register_icon_scales,
    remove_icon,
    update_icon_cache,
)


def get_real_user() -> str:
    """Resolves the real username when running under pkexec or sudo."""
    pkexec_uid = os.environ.get("PKEXEC_UID")
    if pkexec_uid:
        try:
            import pwd
            return pwd.getpwuid(int(pkexec_uid)).pw_name
        except Exception:
            pass
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"


class OperationContext:
    def __init__(
        self,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_progress: Optional[Callable[[float, str], None]] = None,
    ):
        self._on_log = on_log
        self._on_progress = on_progress
        self.is_cancelled = False

    def log(self, level: str, message: str):
        append_to_logfile(level, message)
        if self._on_log:
            self._on_log(level, message)
        else:
            print(f"[{level}] {message}")

    def progress(self, pct: float, message: str):
        if self._on_progress:
            self._on_progress(pct, message)


def download_file(
    url: str,
    dest_path: Path,
    ctx: OperationContext,
    component_name: str = "",
    start_pct: float = 0.0,
    end_pct: float = 1.0,
) -> bool:
    """Downloads a file with chunked streaming, emitting progress and transfer speed."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.log("INFO", f"Downloading {component_name} from {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Antigravity-Installer/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = response.headers.get("content-length")
            total_bytes = int(total_size) if total_size else 0
            downloaded_bytes = 0
            chunk_size = 1024 * 512  # 512 KB

            start_time = time.time()
            last_update = start_time

            with open(dest_path, "wb") as f_out:
                while True:
                    if ctx.is_cancelled:
                        ctx.log("WARNING", "Download cancelled by user.")
                        return False

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f_out.write(chunk)
                    downloaded_bytes += len(chunk)

                    now = time.time()
                    if now - last_update >= 0.2:
                        last_update = now
                        elapsed = now - start_time
                        speed_mb = (downloaded_bytes / (1024 * 1024)) / max(elapsed, 0.001)

                        if total_bytes > 0:
                            ratio = downloaded_bytes / total_bytes
                            current_pct = start_pct + ratio * (end_pct - start_pct)
                            mb_down = downloaded_bytes / (1024 * 1024)
                            mb_tot = total_bytes / (1024 * 1024)
                            msg = f"Downloading {component_name}: {mb_down:.1f}/{mb_tot:.1f} MB ({speed_mb:.2f} MB/s)"
                        else:
                            current_pct = start_pct
                            mb_down = downloaded_bytes / (1024 * 1024)
                            msg = f"Downloading {component_name}: {mb_down:.1f} MB ({speed_mb:.2f} MB/s)"

                        ctx.progress(current_pct, msg)

            ctx.log("SUCCESS", f"Downloaded {component_name} successfully ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
            return True

    except Exception as e:
        ctx.log("ERROR", f"Failed to download {component_name}: {e}")
        return False


def extract_tarball(
    tar_path: Path,
    target_dir: Path,
    ctx: OperationContext,
    component_name: str = "",
) -> bool:
    """Extracts tar.gz with --strip-components=1 to target directory."""
    ctx.log("INFO", f"Extracting {component_name} to {target_dir}")
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Use tar subprocess for maximum speed and exact permissions preservation
        cmd = [
            "tar",
            "-xzf",
            str(tar_path),
            "-C",
            str(target_dir),
            "--strip-components=1",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            ctx.log("ERROR", f"Tar extraction failed: {res.stderr}")
            return False

        ctx.log("SUCCESS", f"Extracted {component_name} successfully to {target_dir}")
        return True
    except Exception as e:
        ctx.log("ERROR", f"Error during tar extraction: {e}")
        return False


def fix_chrome_sandbox(install_dir: Path, ctx: OperationContext) -> bool:
    """Sets root ownership and SUID (4755) permissions on chrome-sandbox."""
    sandbox_path = install_dir / "chrome-sandbox"
    if not sandbox_path.exists():
        return True

    try:
        os.chown(sandbox_path, 0, 0)
        os.chmod(sandbox_path, 0o4755)
        ctx.log("SUCCESS", f"Configured SUID permissions on {sandbox_path} (4755 root:root)")
        return True
    except Exception as e:
        ctx.log("WARNING", f"Could not set SUID on {sandbox_path} (may require root): {e}")
        return False


def update_desktop_database_cache(ctx: OperationContext):
    """Refreshes desktop database and icon theme caches."""
    if shutil.which("update-desktop-database"):
        try:
            subprocess.run(
                ["update-desktop-database", str(APPLICATIONS_DIR)],
                capture_output=True,
                timeout=5,
            )
            ctx.log("INFO", "Updated desktop applications database.")
        except Exception as e:
            ctx.log("WARNING", f"update-desktop-database warning: {e}")

    update_icon_cache()
    ctx.log("INFO", "Updated icon theme cache.")


def install_hub(
    version: str,
    download_url: str,
    ctx: OperationContext,
    start_pct: float = 0.0,
    end_pct: float = 0.5,
) -> bool:
    """Installs Antigravity 2.0 (Hub)."""
    TMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = TMP_DOWNLOAD_DIR / "Antigravity.tar.gz"

    # Step 1: Download
    if not download_file(
        download_url,
        tar_path,
        ctx,
        component_name=f"Antigravity Hub v{version}",
        start_pct=start_pct,
        end_pct=start_pct + (end_pct - start_pct) * 0.7,
    ):
        return False

    # Step 2: Extraction
    ctx.progress(start_pct + (end_pct - start_pct) * 0.75, "Extracting Antigravity Hub...")
    if INSTALL_DIR_HUB.exists():
        shutil.rmtree(INSTALL_DIR_HUB, ignore_errors=True)

    if not extract_tarball(tar_path, INSTALL_DIR_HUB, ctx, "Antigravity Hub"):
        return False

    # Step 3: Symlink binary
    try:
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        bin_link = BIN_DIR / "antigravity"
        if bin_link.exists() or bin_link.is_symlink():
            bin_link.unlink()
        bin_link.symlink_to(INSTALL_DIR_HUB / "antigravity")
        ctx.log("SUCCESS", f"Created symlink {bin_link} -> {INSTALL_DIR_HUB / 'antigravity'}")
    except Exception as e:
        ctx.log("ERROR", f"Failed creating symlink for antigravity: {e}")

    # Step 4: Sandbox SUID
    fix_chrome_sandbox(INSTALL_DIR_HUB, ctx)

    # Step 5: High-Res Icons
    ctx.progress(start_pct + (end_pct - start_pct) * 0.9, "Installing Antigravity Hub icons...")
    hub_icon = get_hub_icon_source()
    if hub_icon:
        register_icon_scales(hub_icon, "antigravity")
        ctx.log("SUCCESS", "Installed Antigravity Hub icons across all standard hicolor resolutions.")
    else:
        ctx.log("WARNING", "Could not locate Antigravity Hub icon source.")

    # Step 6: Desktop entries
    try:
        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        (APPLICATIONS_DIR / "antigravity.desktop").write_text(
            DESKTOP_ENTRY_HUB, encoding="utf-8"
        )
        (APPLICATIONS_DIR / "antigravity-url-handler.desktop").write_text(
            DESKTOP_ENTRY_HUB_URL, encoding="utf-8"
        )
        ctx.log("SUCCESS", "Registered antigravity.desktop and URL handler.")
    except Exception as e:
        ctx.log("ERROR", f"Failed writing desktop entries: {e}")

    update_desktop_database_cache(ctx)
    ctx.progress(end_pct, f"Antigravity Hub v{version} installed.")
    return True


def install_ide(
    version: str,
    download_url: str,
    ctx: OperationContext,
    start_pct: float = 0.5,
    end_pct: float = 1.0,
) -> bool:
    """Installs Antigravity IDE."""
    TMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = TMP_DOWNLOAD_DIR / "Antigravity_IDE.tar.gz"

    # Step 1: Download
    if not download_file(
        download_url,
        tar_path,
        ctx,
        component_name=f"Antigravity IDE v{version}",
        start_pct=start_pct,
        end_pct=start_pct + (end_pct - start_pct) * 0.7,
    ):
        return False

    # Step 2: Extraction
    ctx.progress(start_pct + (end_pct - start_pct) * 0.75, "Extracting Antigravity IDE...")
    if INSTALL_DIR_IDE.exists():
        shutil.rmtree(INSTALL_DIR_IDE, ignore_errors=True)

    if not extract_tarball(tar_path, INSTALL_DIR_IDE, ctx, "Antigravity IDE"):
        return False

    # Step 3: Symlink binary
    try:
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        bin_link = BIN_DIR / "antigravity-ide"
        if bin_link.exists() or bin_link.is_symlink():
            bin_link.unlink()
        bin_link.symlink_to(INSTALL_DIR_IDE / "antigravity-ide")
        ctx.log("SUCCESS", f"Created symlink {bin_link} -> {INSTALL_DIR_IDE / 'antigravity-ide'}")
    except Exception as e:
        ctx.log("ERROR", f"Failed creating symlink for antigravity-ide: {e}")

    # Step 4: Sandbox SUID
    fix_chrome_sandbox(INSTALL_DIR_IDE, ctx)

    # Step 5: High-Res Icons
    ctx.progress(start_pct + (end_pct - start_pct) * 0.9, "Installing Antigravity IDE icons...")
    ide_icon = get_ide_icon_source()
    if ide_icon:
        register_icon_scales(ide_icon, "antigravity-ide")
        ctx.log("SUCCESS", "Installed Antigravity IDE icons across all standard hicolor resolutions.")
    else:
        ctx.log("WARNING", "Could not locate Antigravity IDE icon source.")

    # Step 6: Desktop entries
    try:
        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        (APPLICATIONS_DIR / "antigravity-ide.desktop").write_text(
            DESKTOP_ENTRY_IDE, encoding="utf-8"
        )
        ctx.log("SUCCESS", "Registered antigravity-ide.desktop.")
    except Exception as e:
        ctx.log("ERROR", f"Failed writing IDE desktop entry: {e}")

    update_desktop_database_cache(ctx)
    ctx.progress(end_pct, f"Antigravity IDE v{version} installed.")
    return True


def install_cli(ctx: OperationContext) -> bool:
    """Installs Antigravity CLI via official curl script."""
    ctx.log("INFO", "Running official Antigravity CLI installer...")
    ctx.progress(0.1, "Installing Antigravity CLI (agy)...")

    # Determine real user if running under sudo/pkexec
    real_user = get_real_user()

    cmd = "curl -fsSL https://antigravity.google/cli/install.sh | bash"
    if os.geteuid() == 0 and real_user != "root":
        full_cmd = ["su", "-", real_user, "-c", cmd]
    else:
        full_cmd = ["bash", "-c", cmd]

    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            ctx.log("SUCCESS", "Antigravity CLI installed successfully.")
            # Also create /usr/local/bin/agy or /usr/bin/agy symlink if possible for global discovery
            user_bin = Path(f"/home/{real_user}/.local/bin/agy") if real_user != "root" else Path("/root/.local/bin/agy")
            sys_bin = Path("/usr/local/bin/agy")
            if user_bin.exists() and os.geteuid() == 0:
                try:
                    sys_bin.parent.mkdir(parents=True, exist_ok=True)
                    if sys_bin.exists() or sys_bin.is_symlink():
                        sys_bin.unlink()
                    sys_bin.symlink_to(user_bin)
                    ctx.log("SUCCESS", f"Created global symlink {sys_bin} -> {user_bin}")
                except Exception:
                    pass
            # Register CLI icon
            cli_icon = get_cli_icon_source()
            if cli_icon:
                register_icon_scales(cli_icon, "antigravity-cli")
                ctx.log("SUCCESS", "Installed Antigravity CLI icon.")

            # Register CLI desktop entry
            try:
                APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
                (APPLICATIONS_DIR / "antigravity-cli.desktop").write_text(
                    DESKTOP_ENTRY_CLI, encoding="utf-8"
                )
                ctx.log("SUCCESS", "Registered antigravity-cli.desktop.")
            except Exception as e:
                ctx.log("WARNING", f"Could not write CLI desktop entry: {e}")

            update_desktop_database_cache(ctx)
            return True
        else:
            ctx.log("ERROR", f"CLI installation script returned code {res.returncode}: {res.stderr}")
            return False
    except Exception as e:
        ctx.log("ERROR", f"Failed to execute CLI installer: {e}")
        return False


def uninstall_hub(ctx: OperationContext) -> bool:
    """Uninstalls Antigravity 2.0 (Hub)."""
    ctx.log("INFO", "Uninstalling Antigravity Hub...")
    try:
        if INSTALL_DIR_HUB.exists():
            shutil.rmtree(INSTALL_DIR_HUB, ignore_errors=True)
            ctx.log("SUCCESS", f"Removed {INSTALL_DIR_HUB}")

        bin_link = BIN_DIR / "antigravity"
        if bin_link.exists() or bin_link.is_symlink():
            bin_link.unlink()
            ctx.log("SUCCESS", f"Removed {bin_link}")

        for desktop_file in ("antigravity.desktop", "antigravity-url-handler.desktop"):
            df = APPLICATIONS_DIR / desktop_file
            if df.exists():
                df.unlink()
                ctx.log("SUCCESS", f"Removed {df}")

        remove_icon("antigravity")
        ctx.log("SUCCESS", "Removed Antigravity Hub icons.")
        update_desktop_database_cache(ctx)
        return True
    except Exception as e:
        ctx.log("ERROR", f"Error during Hub uninstallation: {e}")
        return False


def uninstall_ide(ctx: OperationContext) -> bool:
    """Uninstalls Antigravity IDE."""
    ctx.log("INFO", "Uninstalling Antigravity IDE...")
    try:
        if INSTALL_DIR_IDE.exists():
            shutil.rmtree(INSTALL_DIR_IDE, ignore_errors=True)
            ctx.log("SUCCESS", f"Removed {INSTALL_DIR_IDE}")

        bin_link = BIN_DIR / "antigravity-ide"
        if bin_link.exists() or bin_link.is_symlink():
            bin_link.unlink()
            ctx.log("SUCCESS", f"Removed {bin_link}")

        df = APPLICATIONS_DIR / "antigravity-ide.desktop"
        if df.exists():
            df.unlink()
            ctx.log("SUCCESS", f"Removed {df}")

        remove_icon("antigravity-ide")
        ctx.log("SUCCESS", "Removed Antigravity IDE icons.")
        update_desktop_database_cache(ctx)
        return True
    except Exception as e:
        ctx.log("ERROR", f"Error during IDE uninstallation: {e}")
        return False


def uninstall_cli(ctx: OperationContext) -> bool:
    """Uninstalls Antigravity CLI."""
    ctx.log("INFO", "Uninstalling Antigravity CLI...")
    real_user = get_real_user()
    user_home = Path(f"/home/{real_user}") if real_user != "root" else Path("/root")

    paths = [
        user_home / ".local" / "bin" / "agy",
        user_home / ".gemini" / "antigravity-cli",
        Path("/usr/local/bin/agy"),
        Path("/usr/bin/agy"),
        APPLICATIONS_DIR / "antigravity-cli.desktop",
    ]

    for p in paths:
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                ctx.log("SUCCESS", f"Removed directory {p}")
            elif p.exists() or p.is_symlink():
                p.unlink()
                ctx.log("SUCCESS", f"Removed {p}")
        except Exception as e:
            ctx.log("WARNING", f"Could not remove {p}: {e}")

    remove_icon("antigravity-cli")
    update_desktop_database_cache(ctx)
    return True


def install_self_to_opt(source_appimage: str, ctx: OperationContext) -> bool:
    """Installs the AppImage binary into /opt/antigravity-installer/ and configures system shortcut."""
    ctx.log("INFO", "Installing Antigravity Suite Installer to /opt/antigravity-installer/...")
    try:
        opt_dir = Path("/opt/antigravity-installer")
        opt_dir.mkdir(parents=True, exist_ok=True)
        target_appimage = opt_dir / "Antigravity-Installer-x86_64.AppImage"

        src_path = Path(source_appimage)
        if not src_path.exists():
            ctx.log("ERROR", f"Source AppImage not found at {source_appimage}")
            return False

        shutil.copy2(src_path, target_appimage)
        target_appimage.chmod(0o755)
        ctx.log("SUCCESS", f"Installed {target_appimage}")

        # Symlink in /usr/bin/
        bin_link = Path("/usr/bin/antigravity-installer")
        if bin_link.exists() or bin_link.is_symlink():
            bin_link.unlink()
        bin_link.symlink_to(target_appimage)
        ctx.log("SUCCESS", f"Created symlink {bin_link} -> {target_appimage}")

        # Desktop entry in /usr/share/applications/
        desk_file = APPLICATIONS_DIR / "google.antigravity.installer.desktop"
        desk_content = f"""[Desktop Entry]
Name=Antigravity Suite Installer
Comment=Installer, manager and updater for Google Antigravity Suite (Hub, IDE, CLI)
Exec={target_appimage} %u
Icon=google.antigravity.installer
Terminal=false
Type=Application
Categories=Development;Utility;
StartupNotify=true
StartupWMClass=google.antigravity.installer
NoDisplay=false
"""
        desk_file.write_text(desk_content, encoding="utf-8")
        ctx.log("SUCCESS", f"Registered system launcher {desk_file}")

        # Register installer icon to system hicolor
        installer_icon = get_hub_icon_source()
        if installer_icon:
            register_icon_scales(installer_icon, "google.antigravity.installer")

        update_desktop_database_cache(ctx)
        return True
    except Exception as e:
        ctx.log("ERROR", f"Failed to install to /opt: {e}")
        return False


def ensure_system_fuse(ctx: OperationContext):
    """Checks for FUSE2 support and installs libfuse2t64 / libfuse2 if needed on Ubuntu / Debian."""
    try:
        res = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
        if "libfuse.so.2" in res.stdout:
            return

        if shutil.which("apt-get"):
            for pkg in ("libfuse2t64", "libfuse2"):
                check_pkg = subprocess.run(["dpkg", "-s", pkg], capture_output=True, text=True)
                if check_pkg.returncode == 0:
                    return

            ctx.log("INFO", "Installing libfuse2t64 for system-wide AppImage compatibility...")
            for pkg in ("libfuse2t64", "libfuse2"):
                r = subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True, text=True)
                if r.returncode == 0:
                    ctx.log("SUCCESS", f"Installed {pkg} successfully.")
                    return
    except Exception as e:
        ctx.log("WARNING", f"FUSE compatibility check: {e}")


def repair_all(ctx: OperationContext) -> bool:
    """Repairs sandbox permissions, symlinks, desktop shortcuts and icons for installed components."""
    ctx.log("INFO", "Starting system repair and permission audit...")
    ctx.progress(0.1, "Auditing Antigravity Suite...")

    # Ensure system-wide FUSE compatibility for AppImages
    ensure_system_fuse(ctx)

    # Hub Repair
    if INSTALL_DIR_HUB.exists():
        ctx.log("INFO", "Repairing Antigravity Hub...")
        fix_chrome_sandbox(INSTALL_DIR_HUB, ctx)
        hub_icon = get_hub_icon_source()
        if hub_icon:
            register_icon_scales(hub_icon, "antigravity")
        try:
            (APPLICATIONS_DIR / "antigravity.desktop").write_text(
                DESKTOP_ENTRY_HUB, encoding="utf-8"
            )
            (APPLICATIONS_DIR / "antigravity-url-handler.desktop").write_text(
                DESKTOP_ENTRY_HUB_URL, encoding="utf-8"
            )
            bin_link = BIN_DIR / "antigravity"
            if not bin_link.exists() and not bin_link.is_symlink():
                bin_link.symlink_to(INSTALL_DIR_HUB / "antigravity")
            ctx.log("SUCCESS", "Repaired Antigravity Hub shortcuts and symlink.")
        except Exception as e:
            ctx.log("WARNING", f"Could not write Hub shortcuts: {e}")

    # IDE Repair
    if INSTALL_DIR_IDE.exists():
        ctx.log("INFO", "Repairing Antigravity IDE...")
        fix_chrome_sandbox(INSTALL_DIR_IDE, ctx)
        ide_icon = get_ide_icon_source()
        if ide_icon:
            register_icon_scales(ide_icon, "antigravity-ide")
        try:
            (APPLICATIONS_DIR / "antigravity-ide.desktop").write_text(
                DESKTOP_ENTRY_IDE, encoding="utf-8"
            )
            bin_link = BIN_DIR / "antigravity-ide"
            if not bin_link.exists() and not bin_link.is_symlink():
                bin_link.symlink_to(INSTALL_DIR_IDE / "antigravity-ide")
            ctx.log("SUCCESS", "Repaired Antigravity IDE shortcuts and symlink.")
        except Exception as e:
            ctx.log("WARNING", f"Could not write IDE shortcuts: {e}")

    # CLI repair (shortcuts and icons)
    real_user = get_real_user()
    user_bin = Path(f"/home/{real_user}/.local/bin/agy") if real_user != "root" else Path("/root/.local/bin/agy")
    if user_bin.exists() or Path("/usr/local/bin/agy").exists() or Path("/usr/bin/agy").exists():
        ctx.log("INFO", "Repairing Antigravity CLI shortcuts and icons...")
        cli_icon = get_cli_icon_source()
        if cli_icon:
            register_icon_scales(cli_icon, "antigravity-cli")
        try:
            (APPLICATIONS_DIR / "antigravity-cli.desktop").write_text(
                DESKTOP_ENTRY_CLI, encoding="utf-8"
            )
            ctx.log("SUCCESS", "Repaired Antigravity CLI desktop shortcut.")
        except Exception as e:
            ctx.log("WARNING", f"Could not write CLI shortcuts: {e}")

    update_desktop_database_cache(ctx)
    ctx.progress(1.0, "Repair completed.")
    ctx.log("SUCCESS", "System repair completed successfully.")
    return True
