# 🚀 Google Antigravity Suite Installer & Manager (Linux x64)

[![Platform](https://img.shields.io/badge/Platform-Linux%20x86__64-blue.svg)](https://antigravity.google)
[![UI](https://img.shields.io/badge/UI-GTK4%20%7C%20Libadwaita-4a90e2.svg)](https://gitlab.gnome.org/GNOME/libadwaita)
[![Package](https://img.shields.io/badge/Packaging-AppImage%20Standalone-orange.svg)](https://appimage.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Antigravity Suite Installer** is an open-source graphical installer and system manager for the **Google Antigravity** suite on Linux x86_64 distributions (developed and optimized on **Ubuntu 26.04 LTS**, with full support for **Ubuntu 24.04 LTS**, **22.04 LTS**, and derivatives).

Built with a native **GTK 4 / Libadwaita** interface and integrated with Polkit (`pkexec`), it securely handles the entire software lifecycle: downloading official releases from Google CDN, installation, updates, uninstallation, and **automatic repair of system permissions, global symlinks, and sandbox SUID setups**.

---

## 📑 Table of Contents

- [Managed Components](#-managed-components)
- [Key Features](#-key-features)
- [System Requirements](#-system-requirements)
- [Quick Start & Launching](#-quick-start--launching)
- [CLI & Automation Guide](#-cli--automation-guide)
- [Permission & Sandbox Repair Engine](#-permission--sandbox-repair-engine)
- [Project Architecture](#-project-architecture)
- [Building the AppImage](#-building-the-appimage)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Author & License](#-author--license)

---

## 📦 Managed Components

The installer manages all three official components of the Antigravity suite:

| Component | Type | Description | Desktop Entry |
| :--- | :--- | :--- | :--- |
| 🚀 **Antigravity 2.0 (Hub)** | Desktop App | Primary AI-first desktop orchestrator, multi-agent platform, and auxiliary canvas. | `antigravity.desktop` |
| 💻 **Antigravity IDE** | Desktop IDE | Native AI-first development environment based on Electron/VSCode with inline code lens and contextual chat. | `antigravity-ide.desktop` |
| ⚡ **Antigravity CLI (`agy`)** | Terminal CLI | Ultra-fast terminal interface for interacting with and executing agent workflows directly from the shell. | `antigravity-cli.desktop` |

---

## ✨ Key Features

- 🎨 **Native GNOME / Libadwaita Design**: Follows GNOME Human Interface Guidelines (HIG) with smooth animations, status pages, responsive controls, and contextual banners.
- 🎨 **Official Vector Squircle Icons**: High-definition icons (Hub on white squircle, IDE on dark squircle, CLI with pixel-art rainbow arch) rendered with smooth rounded corners and generated across all 7 standard Freedesktop resolutions (512x512 down to 16x16).
- 🛡️ **Privilege Separation via Polkit**: The graphical user interface runs as an unprivileged user process; only system-level filesystem writes (`/usr/share/`, `/usr/bin/`) are delegated to a dedicated worker through `pkexec` with live streaming logs.
- 🔧 **SUID Sandbox Permission Repair**: Automatically configures and audits `chmod 4755 root:root` on `chrome-sandbox` binaries, resolving startup crashes common to Electron applications on Linux.
- 🌐 **Real-time API Manifest Discovery**: Queries Google Cloud Storage and Google DL release endpoints to offer the latest stable builds or allow rolling back to specific versions.
- 📦 **Pure Python ASAR Extractor**: Built-in reader/extractor for Electron `.asar` archives with zero external Node.js dependencies.
- 🌍 **Internationalization (i18n)**: Fully translated into **5 languages** (English, Italian, Spanish, French, German) with automatic system locale detection and live runtime language switching.
- 🌗 **Dark / Light Theme Support**: Automatically tracks GNOME system color scheme preferences with a manual toggle in the header bar.
- ⚠️ **Desktop Environment Detection**: Automatic warning banner when running on non-GNOME environments (KDE Plasma, XFCE, Cinnamon, etc.) to inform users of potential dock integration variances.
- 🛡️ **FUSE & `libfuse2t64` Automation**: 100% out-of-the-box compatibility with Ubuntu 26.04 & 24.04 LTS (where `libfuse2` is absent by default) through automatic `--appimage-extract-and-run` fallback and system-wide package auto-installation.

---

## 💻 System Requirements

- **Architecture**: Linux x86_64 (AMD64 / Intel 64-bit)
- **Supported Distributions**:
  - **Ubuntu 26.04 LTS** (Primary Development & Target Platform)
  - **Ubuntu 24.04 LTS** (Noble Numbat)
  - **Ubuntu 22.04 LTS** (Jammy Jellyfish)
  - **Ubuntu 25.04 / 25.10 / 24.10 / 23.10**
  - **Debian 12 (Bookworm) / Debian 13 (Trixie) / Testing**
  - **Fedora 39+ / Arch Linux / Pop!_OS / Linux Mint**
- **Headless / Server Mode**: CLI mode works on **any Linux x64 environment**, including headless servers, Docker containers, and WSL instances with no monitor or graphical server attached.

---

## 🚀 Quick Start & Launching

### Option 1: Standalone AppImage (Recommended)

Download `Antigravity-Installer-x86_64.AppImage` from the `dist/` directory or from [GitHub Releases](https://github.com/dmz86/antigravity-installer/releases):

```bash
# 1. Make the AppImage executable
chmod +x dist/Antigravity-Installer-x86_64.AppImage

# 2. Launch the graphical installer
./dist/Antigravity-Installer-x86_64.AppImage
```

### Option 2: Smart Bootstrap Launcher (`install.sh`)

The universal launcher automatically validates system dependencies and handles FUSE compatibility:

```bash
./install.sh
```

### Option 3: From Source (Development)

To run the application directly from the source code repository:

```bash
# Install development dependencies:
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cairo

# Run the installer
./run.sh
```

---

## ⌨️ CLI & Automation Guide

The installer can be executed headlessly from the terminal to automate machine provisioning, developer onboarding, or CI/CD pipelines.

### General Syntax

```bash
./Antigravity-Installer-x86_64.AppImage [OPTIONS]
```

### Parameters Reference

| Flag | Description | Accepted Values | Default |
| :--- | :--- | :--- | :--- |
| `-h`, `--help` | Show help screen and exit | — | — |
| `-v`, `--version` | Display installer version and exit | — | — |
| `-y`, `--non-interactive` | Run in non-interactive batch mode (headless, no GUI) | — | Disabled |
| `--action` | Action to execute in non-interactive mode | `install`, `uninstall`, `repair` | `install` |
| `--hub-version` | Specific Antigravity Hub version to install | E.g. `2.8.1` | Latest release |
| `--ide-version` | Specific Antigravity IDE version to install | E.g. `2.5.5` | Latest release |
| `--lang` | Force interface and log language | `en`, `it`, `es`, `fr`, `de` | System locale |

---

### 💡 Practical CLI Examples

#### 1. Full Automated Installation (All Components)
Downloads and installs the latest versions of Hub, IDE, and CLI without opening a graphical window:
```bash
./Antigravity-Installer-x86_64.AppImage -y
```

#### 2. System Permissions & Icons Repair
Audits sandbox SUID permissions, restores global symlinks, and regenerates `.desktop` entries:
```bash
./Antigravity-Installer-x86_64.AppImage -y --action repair
```

#### 3. Complete Suite Uninstallation
Removes all binaries, `/usr/share/antigravity*` directories, `.desktop` launchers, and icon assets:
```bash
./Antigravity-Installer-x86_64.AppImage -y --action uninstall
```

#### 4. Installing Specific Pinned Versions
```bash
./Antigravity-Installer-x86_64.AppImage -y --hub-version 2.8.1 --ide-version 2.5.5
```

#### 5. Running with Forced Language
```bash
./Antigravity-Installer-x86_64.AppImage --lang it
```

---

## 🛠️ Permission & Sandbox Repair Engine

Chromium and Electron-based applications (such as Antigravity Hub and Antigravity IDE) require a specialized security sandbox on Linux. When permissions or system AppArmor profiles become mismatched, these applications fail to launch.

The **"Repair Permissions and Icons"** action automatically executes:
1. **SUID Sandbox Audit**: Sets `chmod 4755 root:root` on:
   - `/usr/share/antigravity/chrome-sandbox`
   - `/usr/share/antigravity-ide/chrome-sandbox`
2. **Global Symlinks**: Restores executable links in `/usr/bin/` and `/usr/local/bin/`:
   - `/usr/bin/antigravity` → `/usr/share/antigravity/antigravity`
   - `/usr/bin/antigravity-ide` → `/usr/share/antigravity-ide/antigravity-ide`
   - `/usr/local/bin/agy` → `~/.local/bin/agy`
3. **Desktop Integration**: Recreates compliant `.desktop` entries with `StartupWMClass` matching Wayland and GNOME Shell requirements.
4. **Icon Theme Cache**: Rebuilds system and user icon theme caches (`gtk-update-icon-cache`) and desktop application registries (`update-desktop-database`).
5. **FUSE System Support**: Checks for `libfuse2t64` on Ubuntu 24.04+ and installs it via `apt-get` if missing.

---

## 🏗️ Project Architecture

```
antigravity-installer/
├── antigravity_installer/          # Python source package
│   ├── __init__.py                 # Application version (1.0.0)
│   ├── api.py                      # Google Storage & DL release API client
│   ├── asar.py                     # Native Python Electron ASAR extractor
│   ├── config.py                   # System constants, paths, and desktop entries
│   ├── detector.py                 # System-installed components detector
│   ├── i18n.py                     # Internationalization & locale engine
│   ├── icons.py                    # Hicolor & Pixmaps icon scaling manager
│   ├── main.py                     # Main entry point (GUI/CLI dispatcher)
│   ├── operations.py               # Core operations (download, unpack, repair)
│   ├── polkit.py                   # Privileged worker launcher via pkexec
│   ├── polkit_worker.py            # Root-privileged task worker
│   ├── locales/                    # Translation JSON dictionaries (it, en, es, fr, de)
│   └── ui/                         # GTK4 / Libadwaita graphical interface
│       ├── window.py               # Main Adw.ApplicationWindow
│       ├── view_components.py      # Component selection and hero view
│       ├── view_progress.py        # Progress view and live log terminal
│       └── view_finish.py          # Completion view with app quick-launch
├── assets/                         # Graphic assets
│   └── icons/                      # Official squircle vector icons (512x512 PNG)
├── dist/                           # Built distribution packages
│   ├── Antigravity-Installer-x86_64.AppImage
│   └── install.sh                  # Bootstrap launcher
├── build_appimage.sh               # Standalone AppImage packaging script
├── install.sh                      # Universal launcher
├── run.sh                          # Local development runner
├── pyproject.toml                  # Python package configuration
└── README.md                       # This documentation
```

---

## 🔨 Building the AppImage

To build the standalone AppImage from source:

```bash
chmod +x build_appimage.sh
./build_appimage.sh
```

The script automatically:
1. Downloads the latest continuous build of `appimagetool`.
2. Packages the Python application, desktop entries, and assets into the `AppDir` tree.
3. Generates all 7 standard hicolor icon resolutions.
4. Compresses the payload into a standalone SquashFS/zstd AppImage binary at `dist/Antigravity-Installer-x86_64.AppImage`.

---

## ❓ Troubleshooting & FAQ

### 1. Where are log files saved?
Full operational logs with timestamps and log levels are saved automatically to:
```bash
cat ~/.local/state/antigravity-installer/installer.log
```

### 2. Dock icon shows a generic terminal icon (`>_`)
If the dock icon does not associate immediately on the first run, execute the repair routine once:
```bash
./dist/Antigravity-Installer-x86_64.AppImage -y --action repair
```
This registers the full multi-resolution hicolor icon set and `index.theme` in `~/.local/share/icons/hicolor/`.

### 3. Error `dlopen(): error loading libfuse.so.2` on fresh Ubuntu 26.04 / 24.04
Ubuntu 26.04 and 24.04 LTS removed `libfuse2` by default. You can launch the installer using `./install.sh` (which automatically uses `--appimage-extract-and-run` with zero dependencies) or install system FUSE support with:
```bash
sudo apt install libfuse2t64
```

---

## 👤 Author & References

- **Developed by**: [dmz86](https://github.com/dmz86)
- **Project Repository**: [https://github.com/dmz86/antigravity-installer](https://github.com/dmz86/antigravity-installer)
- **Issue Tracker**: [GitHub Issues](https://github.com/dmz86/antigravity-installer/issues)
- **Official Google Antigravity Website**: [https://antigravity.google](https://antigravity.google)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
