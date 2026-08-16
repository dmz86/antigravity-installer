"""
Polkit / pkexec helper for privileged system operations.
Supports running backend actions directly if already root, or via pkexec with streaming logs.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional

from antigravity_installer.config import append_to_logfile


def is_root() -> bool:
    """Returns True if the current process is running as root (EUID 0)."""
    return os.geteuid() == 0


def _prepare_worker_for_pkexec() -> tuple:
    """
    When running from an AppImage, the FUSE mountpoint is only accessible to
    the mounting user.  pkexec runs the worker as root, which cannot read files
    inside /tmp/.mount_*.  We solve this by copying the entire installer
    package tree to a world-readable temp directory and pointing pkexec at the
    copy.

    Returns (worker_script_path, temp_dir_or_None).
    temp_dir_or_None is set when a copy was made and must be cleaned up later.
    """
    pkg_dir = Path(__file__).resolve().parent          # antigravity_installer/
    project_root = pkg_dir.parent                      # project root or AppDir tree
    worker_script = pkg_dir / "polkit_worker.py"

    # Check if we are running inside an AppImage FUSE mount
    appimage_env = os.environ.get("APPIMAGE")
    appdir_env = os.environ.get("APPDIR")
    inside_fuse = (
        appimage_env
        or appdir_env
        or str(project_root).startswith("/tmp/.mount_")
    )

    if not inside_fuse:
        # Normal dev / system-wide install — no copy needed
        return str(worker_script), None

    # Copy the package tree to a world-readable tempdir
    tmp_root = tempfile.mkdtemp(prefix="antigravity_pkexec_")
    os.chmod(tmp_root, 0o755)

    # Copy the antigravity_installer package
    dst_pkg = Path(tmp_root) / "antigravity_installer"
    shutil.copytree(str(pkg_dir), str(dst_pkg))

    # Copy assets if they exist (needed for icons during repair)
    assets_src = project_root / "assets"
    if assets_src.exists():
        shutil.copytree(str(assets_src), str(Path(tmp_root) / "assets"))

    # Make everything world-readable
    for root_dir, dirs, files in os.walk(tmp_root):
        os.chmod(root_dir, 0o755)
        for f in files:
            os.chmod(os.path.join(root_dir, f), 0o644)

    # Make .py files executable
    for py_file in Path(tmp_root).rglob("*.py"):
        os.chmod(str(py_file), 0o755)

    return str(dst_pkg / "polkit_worker.py"), tmp_root


def run_privileged_worker(
    action_type: str,
    payload: dict,
    on_log: Optional[Callable[[str, str], None]] = None,
    on_progress: Optional[Callable[[float, str], None]] = None,
) -> bool:
    """
    Executes a privileged worker task.
    If root, runs in-process or via direct subprocess.
    If non-root, invokes pkexec with the python runner.
    """
    tmp_dir = None
    try:
        if is_root():
            worker_script = str(Path(__file__).resolve().parent / "polkit_worker.py")
        else:
            worker_script, tmp_dir = _prepare_worker_for_pkexec()

        cmd = [
            sys.executable,
            worker_script,
            "--action",
            action_type,
            "--payload",
            json.dumps(payload),
        ]

        if not is_root():
            cmd = ["pkexec"] + cmd

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        for line in iter(proc.stdout.readline, ""):
            line_str = line.strip()
            if not line_str:
                continue

            # Check for JSON progress messages from worker
            if line_str.startswith("__PROGRESS__:"):
                try:
                    data = json.loads(line_str[len("__PROGRESS__:"):])
                    pct = float(data.get("pct", 0.0))
                    msg = data.get("msg", "")
                    if on_progress:
                        on_progress(pct, msg)
                    continue
                except Exception:
                    pass

            if line_str.startswith("__LOG__:"):
                try:
                    data = json.loads(line_str[len("__LOG__:"):])
                    level = data.get("level", "INFO")
                    text = data.get("text", "")
                    append_to_logfile(level, text)
                    if on_log:
                        on_log(level, text)
                    continue
                except Exception:
                    pass

            # Standard raw log
            append_to_logfile("INFO", line_str)
            if on_log:
                on_log("INFO", line_str)

        proc.stdout.close()
        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        if on_log:
            on_log("ERROR", f"Failed to execute privileged worker: {e}")
        return False
    finally:
        # Clean up temporary copy
        if tmp_dir:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass
