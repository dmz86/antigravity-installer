# 🚀 Release Notes - v1.1.0

## Google Antigravity Suite Installer & Manager (Linux x64)

We are pleased to release **v1.1.0** of **Antigravity Suite Installer**, introducing system-wide installation to `/opt`, automated GitHub release update notifications, and desktop launcher deduplication.

---

## ✨ What's New in v1.1.0

### 📦 1. Permanent System Installation to `/opt`
- **First-Run Interactive Setup**: When launched from temporary or portable locations (e.g. `~/Downloads` or `/tmp`), the installer now presents an intuitive Libadwaita prompt asking if you'd like to install it permanently.
- **System Integration**:
  - Installs the standalone AppImage into `/opt/antigravity-installer/Antigravity-Installer-x86_64.AppImage`.
  - Creates a global CLI shortcut at `/usr/bin/antigravity-installer`.
  - Configures the desktop entry in `/usr/share/applications/google.antigravity.installer.desktop`.
- **Smart NoDisplay Fallback**: If temporary execution is preferred, the installer configures `NoDisplay=true` on user-level entries, keeping the application menu clean while retaining active dock icon matching during runtime.

### 🌐 2. Automated GitHub Releases Update Checker
- Background version checker querying `https://api.github.com/repos/dmz86/antigravity-installer/releases/latest`.
- Non-intrusive `Adw.Banner` alert at the top of the interface notifying users whenever a newer version is published.
- Direct **"Download"** action opening the release assets page in the default web browser.

### 🧹 3. Desktop Launcher Deduplication & Clean-up
- Cleaned up redundant `.desktop` entries in user directories (`~/.local/share/applications/`), ensuring a strict 1-to-1 mapping for all suite components:
  - **Antigravity 2.0 (Hub)** (`antigravity.desktop`)
  - **Antigravity IDE** (`antigravity-ide.desktop`)
  - **Antigravity CLI** (`antigravity-cli.desktop`)
  - **Antigravity Suite Installer** (`google.antigravity.installer.desktop`)

### 🐧 4. Platform Optimization
- Explicit support and optimization for **Ubuntu 26.04 LTS**, **Ubuntu 24.04 LTS**, and modern GNOME / Wayland environments.

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

### Or use the Universal Launcher

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
