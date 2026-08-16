"""
Polkit / pkexec helper for privileged system operations.
Supports running backend actions directly if already root, or via pkexec with streaming logs.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from antigravity_installer.config import append_to_logfile


def is_root() -> bool:
    """Returns True if the current process is running as root (EUID 0)."""
    return os.geteuid() == 0


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
    worker_script = str(Path(__file__).resolve().parent / "polkit_worker.py")
    cmd = [
        sys.executable,
        worker_script,
        "--action",
        action_type,
        "--payload",
        json.dumps(payload),
    ]

    if not is_root():
        # Prepend pkexec
        cmd = ["pkexec"] + cmd

    try:
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
                    data = json.loads(line_str[len("__PROGRESS__:") :])
                    pct = float(data.get("pct", 0.0))
                    msg = data.get("msg", "")
                    if on_progress:
                        on_progress(pct, msg)
                    continue
                except Exception:
                    pass

            if line_str.startswith("__LOG__:"):
                try:
                    data = json.loads(line_str[len("__LOG__:") :])
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
