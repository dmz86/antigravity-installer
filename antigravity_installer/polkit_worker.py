"""
Privileged backend worker executed directly or via pkexec.
Emits structured JSON lines for live progress and logging to the frontend GUI.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path even when invoked via pkexec / root
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from antigravity_installer.config import append_to_logfile
from antigravity_installer.operations import (
    OperationContext,
    install_cli,
    install_hub,
    install_ide,
    install_self_to_opt,
    repair_all,
    uninstall_cli,
    uninstall_hub,
    uninstall_ide,
)


def emit_log(level: str, text: str):
    msg = json.dumps({"level": level, "text": text})
    print(f"__LOG__:{msg}", flush=True)


def emit_progress(pct: float, msg: str):
    data = json.dumps({"pct": pct, "msg": msg})
    print(f"__PROGRESS__:{data}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Privileged Worker")
    parser.add_argument("--action", required=True, choices=["install", "uninstall", "repair", "install_self"])
    parser.add_argument("--payload", required=True, help="JSON encoded configuration payload")
    args = parser.parse_args()

    payload = json.loads(args.payload)
    ctx = OperationContext(on_log=emit_log, on_progress=emit_progress)

    success = True
    action = args.action

    if action == "install_self":
        src = payload.get("source_appimage", "")
        success = install_self_to_opt(src, ctx)

    elif action == "repair":
        success = repair_all(ctx)

    elif action == "uninstall":
        selected = payload.get("components", [])
        total = max(len(selected), 1)
        for i, comp_id in enumerate(selected):
            emit_progress(i / total, f"Uninstalling {comp_id}...")
            if comp_id == "hub":
                if not uninstall_hub(ctx):
                    success = False
            elif comp_id == "ide":
                if not uninstall_ide(ctx):
                    success = False
            elif comp_id == "cli":
                if not uninstall_cli(ctx):
                    success = False
        emit_progress(1.0, "Uninstallation completed.")

    elif action == "install":
        items = payload.get("items", {})
        # items format: {"hub": {"version": "2.8.1", "url": "..."}, "ide": {...}, "cli": True}
        total_items = max(len(items), 1)
        step_weight = 1.0 / total_items

        curr_step = 0
        if "hub" in items:
            hub_data = items["hub"]
            ver = hub_data.get("version", "latest")
            url = hub_data.get("url")
            s_pct = curr_step * step_weight
            e_pct = (curr_step + 1) * step_weight
            emit_progress(s_pct, f"Installing Antigravity Hub v{ver}...")
            if not install_hub(ver, url, ctx, start_pct=s_pct, end_pct=e_pct):
                success = False
            curr_step += 1

        if "ide" in items:
            ide_data = items["ide"]
            ver = ide_data.get("version", "latest")
            url = ide_data.get("url")
            s_pct = curr_step * step_weight
            e_pct = (curr_step + 1) * step_weight
            emit_progress(s_pct, f"Installing Antigravity IDE v{ver}...")
            if not install_ide(ver, url, ctx, start_pct=s_pct, end_pct=e_pct):
                success = False
            curr_step += 1

        if "cli" in items:
            emit_progress(curr_step * step_weight, "Installing Antigravity CLI...")
            if not install_cli(ctx):
                success = False
            curr_step += 1

        emit_progress(1.0, "Installation completed.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
