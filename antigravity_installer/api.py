"""
API client for querying official Antigravity releases (Hub and IDE).
"""

import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from antigravity_installer.config import (
    API_HUB_RELEASES,
    API_IDE_RELEASES,
    ReleaseInfo,
    URL_HUB_DOWNLOAD_TEMPLATE,
    URL_IDE_DOWNLOAD_TEMPLATE,
)


def _fetch_json(url: str, timeout: int = 8) -> Optional[dict | list]:
    """Fetches and parses JSON from a URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Antigravity-Installer-Linux/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except Exception as e:
        print(f"[API] Error fetching {url}: {e}")
        return None


def fetch_hub_releases() -> List[ReleaseInfo]:
    """Fetches Antigravity Hub releases from Cloud Run API."""
    data = _fetch_json(API_HUB_RELEASES)
    results: List[ReleaseInfo] = []

    if isinstance(data, list) and data:
        for idx, item in enumerate(data):
            ver = str(item.get("version", "")).strip()
            exec_id = str(item.get("execution_id", "")).strip().rstrip("/")
            if ver and exec_id:
                url = URL_HUB_DOWNLOAD_TEMPLATE.format(
                    version=ver, execution_id=exec_id
                )
                results.append(
                    ReleaseInfo(
                        version=ver,
                        execution_id=exec_id,
                        download_url=url,
                        is_latest=(idx == 0),
                    )
                )

    if not results:
        # Fallback offline release
        results.append(
            ReleaseInfo(
                version="2.8.1",
                execution_id="6512087774658560",
                download_url=URL_HUB_DOWNLOAD_TEMPLATE.format(
                    version="2.8.1", execution_id="6512087774658560"
                ),
                is_latest=True,
            )
        )

    return results


def fetch_ide_releases() -> List[ReleaseInfo]:
    """Fetches Antigravity IDE releases from Cloud Run API."""
    data = _fetch_json(API_IDE_RELEASES)
    results: List[ReleaseInfo] = []

    if isinstance(data, list) and data:
        for idx, item in enumerate(data):
            ver = str(item.get("version", "")).strip()
            exec_id = str(item.get("execution_id", "")).strip().rstrip("/")
            if ver and exec_id:
                url = URL_IDE_DOWNLOAD_TEMPLATE.format(
                    version=ver, execution_id=exec_id
                )
                results.append(
                    ReleaseInfo(
                        version=ver,
                        execution_id=exec_id,
                        download_url=url,
                        is_latest=(idx == 0),
                    )
                )

    if not results:
        # Fallback offline release
        results.append(
            ReleaseInfo(
                version="2.5.5",
                execution_id="4923483625488384",
                download_url=URL_IDE_DOWNLOAD_TEMPLATE.format(
                    version="2.5.5", execution_id="4923483625488384"
                ),
                is_latest=True,
            )
        )

    return results


def fetch_all_releases() -> Tuple[List[ReleaseInfo], List[ReleaseInfo]]:
    """Fetches Hub and IDE releases."""
    hub = fetch_hub_releases()
    ide = fetch_ide_releases()
    return hub, ide


def check_installer_github_update(current_version: str = "1.0.0") -> Optional[dict]:
    """Checks GitHub releases for an updated installer version."""
    url = "https://api.github.com/repos/dmz86/antigravity-installer/releases/latest"
    data = _fetch_json(url, timeout=5)
    if isinstance(data, dict):
        tag = str(data.get("tag_name", "")).strip().lstrip("v")
        if tag:
            try:
                def parse_v(v_str):
                    return tuple(int(x) for x in v_str.split(".") if x.isdigit())

                if parse_v(tag) > parse_v(current_version):
                    return {
                        "version": tag,
                        "url": data.get("html_url", "https://github.com/dmz86/antigravity-installer/releases/latest"),
                        "name": data.get("name", f"Release v{tag}"),
                        "body": data.get("body", ""),
                    }
            except Exception:
                pass
    return None

