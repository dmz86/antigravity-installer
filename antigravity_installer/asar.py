"""
Pure-Python Electron ASAR archive parser and asset extractor.
Enables reading metadata and extracting icons without requiring Node.js or external tools.
"""

import json
import os
import struct
from pathlib import Path
from typing import Dict, List, Optional


class AsarArchive:
    """Read-only reader for Electron ASAR archive files."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.header: Dict = {}
        self.base_offset = 0
        if self.file_path.exists():
            self._parse_header()

    def _parse_header(self):
        with open(self.file_path, "rb") as f:
            f.seek(0)
            _magic = struct.unpack("<I", f.read(4))[0]
            header_size = struct.unpack("<I", f.read(4))[0]
            _header_json_size = struct.unpack("<I", f.read(4))[0]
            header_len = struct.unpack("<I", f.read(4))[0]

            header_raw = f.read(header_len)
            self.header = json.loads(header_raw.decode("utf-8"))
            self.base_offset = 8 + header_size

    def list_files(self) -> List[str]:
        """Lists all files in the ASAR archive."""
        results: List[str] = []

        def _walk(node: dict, path: str):
            if "files" in node:
                for name, info in node["files"].items():
                    sub = f"{path}/{name}" if path else name
                    if "files" in info:
                        _walk(info, sub)
                    else:
                        results.append(sub)

        _walk(self.header, "")
        return results

    def read_file(self, rel_path: str) -> Optional[bytes]:
        """Reads file bytes from ASAR archive."""
        if not self.file_path.exists():
            return None

        clean_path = rel_path.strip("/")
        parts = clean_path.split("/")

        curr = self.header
        for part in parts:
            if "files" in curr and part in curr["files"]:
                curr = curr["files"][part]
            else:
                return None

        if "size" not in curr or "offset" not in curr:
            # File might be unpacked in <archive>.unpacked/
            unpacked_path = (
                self.file_path.parent
                / f"{self.file_path.name}.unpacked"
                / clean_path
            )
            if unpacked_path.exists():
                return unpacked_path.read_bytes()
            return None

        offset = int(curr["offset"])
        size = int(curr["size"])

        with open(self.file_path, "rb") as f:
            f.seek(self.base_offset + offset)
            return f.read(size)

    def extract_file(self, rel_path: str, dest_path: str | Path) -> bool:
        """Extracts a file to local destination path."""
        data = self.read_file(rel_path)
        if data is None:
            return False

        try:
            dest = Path(dest_path)
            if dest.exists():
                try:
                    dest.unlink()
                except Exception:
                    pass
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return True
        except Exception as e:
            print(f"[ASAR] Could not write {dest_path}: {e}")
            return False


def get_asar_package_json(asar_path: str | Path) -> Optional[dict]:
    """Reads and parses package.json from an ASAR file."""
    try:
        archive = AsarArchive(asar_path)
        content = archive.read_file("package.json")
        if content:
            return json.loads(content.decode("utf-8"))
    except Exception as e:
        print(f"[ASAR] Error reading package.json: {e}")
    return None
