# 🚀 Release Notes - v1.0.0

## Google Antigravity Suite Installer & Manager (Linux x64)

We are proud to announce the first official stable release (**v1.0.0**) of **Antigravity Suite Installer**, the modern, open-source graphical installer and system manager for the **Google Antigravity** suite on Linux x86_64 (developed and optimized for **Ubuntu 26.04 LTS**, **24.04 LTS**, **22.04 LTS**, and derivatives).

---

## ✨ What's New & Key Highlights

### 📦 Complete Suite Management
- **Antigravity 2.0 (Hub)**: Full lifecycle management (install, update, repair, uninstall) with automatic `.desktop` launcher and URL protocol handlers (`antigravity://`).
- **Antigravity IDE**: Automated extraction and setup of the native AI-first IDE environment based on Electron/VSCode with global binary symlinks.
- **Antigravity CLI (`agy`)**: Official curl bootstrap integration, global `/usr/local/bin/agy` symlinking, and a dedicated `antigravity-cli.desktop` terminal launcher.

### 🎨 Modern Libadwaita / GTK4 Interface
- Built adhering strictly to the **GNOME Human Interface Guidelines (HIG)**.
- **Hero Section**: Beautiful Antigravity vector logo with localized title and subtitle.
- **Live Terminal Log Viewer**: Real-time streaming log output for all privileged operations.
- **Dark / Light Theme**: Automatic synchronization with system appearance preferences with manual toggle.

### 🎨 Official Vector Squircle Icons
- High-definition squircle icons extracted directly from official Google Antigravity vector assets (`antigravity.google`).
- **Hub**: Clean white squircle with subtle border.
- **IDE**: Dark squircle (`#202124`).
- **CLI**: Seamless dark squircle with rainbow arch pixel artwork.
- Automatically scaled and registered across all 7 standard Freedesktop resolutions (`512x512`, `256x256`, `128x128`, `64x64`, `48x48`, `32x32`, `16x16`) with proper `index.theme` cache initialization.

### 🛡️ Secure Polkit Privilege Separation
- The graphical interface executes entirely as an unprivileged user process.
- Privileged operations (`/usr/share/`, `/usr/bin/`, SUID sandbox setups) are safely delegated through **Polkit (`pkexec`)** to an isolated worker process.
- Built-in AppImage FUSE permissions bridging: automatically stages worker scripts into world-readable temporary paths so `pkexec` never fails due to FUSE mountpoint restrictions.

### 🔧 SUID Sandbox & System Permission Repair Engine
- One-click **"Repair Permissions and Icons"** mode.
- Automatically audits and configures `chmod 4755 root:root` on `chrome-sandbox` binaries to prevent Electron startup failures.
- Verifies global symlinks in `/usr/bin/` and desktop registry caches.

### 📦 Universal Standalone AppImage & Smart Launcher
- **Single Portable File**: `Antigravity-Installer-x86_64.AppImage` (1.2 MB) bundles all assets, ASAR extractor, and locales.
- **FUSE Automation**: Native fallback to `--appimage-extract-and-run` on fresh Ubuntu 24.04/26.04 installations where legacy `libfuse2` is absent, plus automatic system package installation (`libfuse2t64`) during setup.
- **Bootstrap Launcher**: [`install.sh`](install.sh) provides a universal, zero-friction launch wrapper.

### 🌍 Multi-Language Support (i18n)
- Fully translated into **5 languages**:
  - 🇬🇧 English
  - 🇮🇹 Italian (Italiano)
  - 🇪🇸 Spanish (Español)
  - 🇫🇷 French (Français)
  - 🇩🇪 German (Deutsch)
- Automatic system locale detection with instant live switching from the interface.

### ⚠️ Desktop Environment Detection
- Automatically detects the active desktop session (`XDG_CURRENT_DESKTOP`).
- Shows a non-intrusive `Adw.Banner` alert on non-GNOME environments (KDE Plasma, XFCE, Cinnamon, MATE, LXQt) explaining potential dock integration variances.

### 💻 Non-Interactive CLI Automation Mode
- Fully headless execution via `--non-interactive` / `-y` for developer provisioning, Docker containers, and CI/CD pipelines.

---

## 💻 Supported Operating Systems

- **Ubuntu 26.04 LTS** (Primary Development & Target Platform)
- **Ubuntu 24.04 LTS** (Noble Numbat)
- **Ubuntu 22.04 LTS** (Jammy Jellyfish)
- **Ubuntu 25.04 / 25.10 / 24.10 / 23.10**
- **Debian 12 (Bookworm) / Debian 13 (Trixie) / Testing**
- **Fedora 39+ / Arch Linux / Pop!_OS / Linux Mint**
- **Headless Servers / Docker / WSL2** (via CLI mode)

---

## 🚀 Getting Started

### Download & Run

```bash
# 1. Download the standalone AppImage
chmod +x Antigravity-Installer-x86_64.AppImage

# 2. Run the GUI installer
./Antigravity-Installer-x86_64.AppImage
```

### Or use the Smart Bootstrap Launcher

```bash
./install.sh
```

### Headless CLI Installation (All Components)

```bash
./Antigravity-Installer-x86_64.AppImage -y
```

---

## 📦 Release Assets

| File | Type | Description |
| :--- | :--- | :--- |
| `Antigravity-Installer-x86_64.AppImage` | Binary | Standalone portable executable for Linux x86_64 (1.2 MB) |
| `install.sh` | Shell Script | Universal bootstrap launcher with FUSE autodetection |
| `Source code (zip / tar.gz)` | Source Archive | Complete project source code |

---

## 🔗 Project Links

- **Repository**: [https://github.com/dmz86/antigravity-installer](https://github.com/dmz86/antigravity-installer)
- **Issue Tracker**: [https://github.com/dmz86/antigravity-installer/issues](https://github.com/dmz86/antigravity-installer/issues)
- **Official Google Antigravity Platform**: [https://antigravity.google](https://antigravity.google)
