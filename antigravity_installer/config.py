"""
Configuration, constants, API URLs, and desktop entry templates for Antigravity Suite Installer.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import datetime

# Base directories
INSTALL_DIR_HUB = Path("/usr/share/antigravity")
INSTALL_DIR_IDE = Path("/usr/share/antigravity-ide")
BIN_DIR = Path("/usr/bin")
LOCAL_BIN_DIR = Path.home() / ".local" / "bin"
APPLICATIONS_DIR = Path("/usr/share/applications")
PIXMAPS_DIR = Path("/usr/share/pixmaps")
HICOLOR_ICONS_DIR = Path("/usr/share/icons/hicolor")
TMP_DOWNLOAD_DIR = Path("/tmp/antigravity-installer")
LOG_DIR = Path.home() / ".local" / "state" / "antigravity-installer"
LOG_FILE = LOG_DIR / "installer.log"
FALLBACK_LOG_FILE = Path("/tmp/antigravity-installer.log")


def append_to_logfile(level: str, text: str):
    """Appends timestamped log message to persistent log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {text}\n"
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        try:
            with open(FALLBACK_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

# Assets directory
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BUNDLED_ICONS_DIR = ASSETS_DIR / "icons"

# API Endpoints
API_HUB_RELEASES = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"
API_IDE_RELEASES = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"
CLI_INSTALL_SCRIPT_URL = "https://antigravity.google/cli/install.sh"

# Download URL Templates
URL_HUB_DOWNLOAD_TEMPLATE = (
    "https://storage.googleapis.com/antigravity-public/antigravity-hub/"
    "{version}-{execution_id}/linux-x64/Antigravity.tar.gz"
)
URL_IDE_DOWNLOAD_TEMPLATE = (
    "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/"
    "{version}-{execution_id}/linux-x64/Antigravity%20IDE.tar.gz"
)

# Standard icon sizes for hicolor theme
HICOLOR_SIZES = [512, 256, 128, 64, 48, 32]


@dataclass
class ReleaseInfo:
    version: str
    execution_id: str
    download_url: str
    is_latest: bool = False
    release_date: Optional[str] = None


@dataclass
class ComponentMeta:
    id: str
    name_key: str
    desc_key: str
    icon_name: str
    default_enabled: bool = True
    supports_versions: bool = True


COMPONENTS: List[ComponentMeta] = [
    ComponentMeta(
        id="hub",
        name_key="component_hub_name",
        desc_key="component_hub_desc",
        icon_name="antigravity",
        default_enabled=True,
        supports_versions=True,
    ),
    ComponentMeta(
        id="ide",
        name_key="component_ide_name",
        desc_key="component_ide_desc",
        icon_name="antigravity-ide",
        default_enabled=True,
        supports_versions=True,
    ),
    ComponentMeta(
        id="cli",
        name_key="component_cli_name",
        desc_key="component_cli_desc",
        icon_name="antigravity-cli",
        default_enabled=True,
        supports_versions=False,
    ),
]


def get_icon_path(icon_name: str) -> Optional[Path]:
    """Returns absolute path to bundled high-res icon if available."""
    png_path = BUNDLED_ICONS_DIR / f"{icon_name}.png"
    if png_path.exists():
        return png_path
    return None

# Desktop files definitions
DESKTOP_ENTRY_HUB = """[Desktop Entry]
Name=Antigravity
Name[it]=Antigravity
Comment=Experience liftoff - AI-First Multi-Agent Orchestrator
Comment[it]=Piattaforma e orchestratore multi-agente AI-First
GenericName=Text Editor
GenericName[it]=Editor di Testo
Exec=/usr/share/antigravity/antigravity %F
Icon=antigravity
Type=Application
StartupNotify=false
StartupWMClass=Antigravity
Categories=TextEditor;Development;IDE;
MimeType=application/x-antigravity-workspace;
Actions=new-empty-window;
Keywords=vscode;antigravity;ai;agent;

[Desktop Action new-empty-window]
Name=New Empty Window
Name[it]=Nuova finestra vuota
Name[es]=Nueva ventana vacía
Name[fr]=Nouvelle fenêtre vide
Name[de]=Neues leeres Fenster
Exec=/usr/share/antigravity/antigravity --new-window %F
Icon=antigravity
"""

DESKTOP_ENTRY_HUB_URL = """[Desktop Entry]
Name=Antigravity - URL Handler
Comment=Experience liftoff URL Handler
GenericName=Text Editor
Exec=/usr/share/antigravity/antigravity --open-url %U
Icon=antigravity
Type=Application
NoDisplay=true
StartupNotify=false
Categories=Utility;TextEditor;Development;IDE;
MimeType=x-scheme-handler/antigravity;
Keywords=vscode;antigravity;
"""

DESKTOP_ENTRY_IDE = """[Desktop Entry]
Name=Antigravity IDE
Name[it]=Antigravity IDE
Comment=Advanced Development Environment for Antigravity
Comment[it]=Ambiente di Sviluppo Avanzato per Antigravity
GenericName=Integrated Development Environment
GenericName[it]=Ambiente di Sviluppo Integrato (IDE)
Exec=/usr/share/antigravity-ide/antigravity-ide %F
Icon=antigravity-ide
Type=Application
StartupNotify=false
StartupWMClass=Antigravity IDE
Categories=Development;IDE;TextEditor;
MimeType=application/x-antigravity-workspace;
Keywords=vscode;antigravity;ide;ai;agent;
"""
