# Debian Packaging Documentation

## Overview

This document describes the Debian packaging system for Voice Training Data Creator, including the build process, installation paths, and storage mechanisms.

## Package Structure

### Files and Directories

```
voice-training-data-creator_1.0.0_all.deb
├── DEBIAN/
│   ├── control              # Package metadata and dependencies
│   ├── postinst             # Post-installation script
│   ├── prerm                # Pre-removal script
│   └── postrm               # Post-removal script
├── usr/
│   ├── bin/
│   │   └── voice-training-data-creator  # Launch script
│   ├── lib/
│   │   └── voice-training-data-creator/
│   │       ├── src/         # Application source code
│   │       ├── requirements.txt
│   │       ├── README.md
│   │       └── venv/        # Created during installation
│   └── share/
│       ├── applications/
│       │   └── voice-training-data-creator.desktop
│       ├── icons/
│       │   └── hicolor/256x256/apps/
│       │       └── voice-training-data-creator.png
│       └── doc/
│           └── voice-training-data-creator/
│               ├── copyright
│               └── README.gz
```

## Installation Paths

### System Installation

The package installs to system directories:

| Component | Path | Purpose |
|-----------|------|---------|
| Application code | `/usr/lib/voice-training-data-creator/` | Main application files |
| Virtual environment | `/usr/lib/voice-training-data-creator/venv/` | Isolated Python dependencies |
| Executable | `/usr/bin/voice-training-data-creator` | Launch script in PATH |
| Desktop entry | `/usr/share/applications/` | Menu integration |
| Icon | `/usr/share/icons/hicolor/256x256/apps/` | Application icon |
| Documentation | `/usr/share/doc/voice-training-data-creator/` | Copyright and README |

### User Data Storage

User-specific data is stored in the home directory, **not** in system paths:

| Data Type | Path | Persistence |
|-----------|------|-------------|
| Configuration | `~/.config/VoiceTrainingDataCreator/config.json` | Survives updates/reinstalls |
| API Keys | System Keyring (KDE Wallet/GNOME Keyring) | Secure storage |
| Voice Samples | User-configured path (e.g., `~/voice-samples/`) | Never deleted |

## Storage Mechanism Validation

### Configuration Storage

The application uses `ConfigManager` which stores settings in:
```
~/.config/VoiceTrainingDataCreator/config.json
```

This path is constructed using Python's `Path.home()`, ensuring it works for any user:

```python
CONFIG_FILE = Path.home() / ".config" / APP_NAME / "config.json"
```

**Benefits:**
- ✅ Works for all users (multi-user system support)
- ✅ Persists across package updates
- ✅ Persists across package reinstalls
- ✅ Not removed during package uninstall (only on purge)
- ✅ Standard XDG Base Directory compliance

### API Key Storage

API keys are stored using the `keyring` library:

```python
keyring.set_password("VoiceTrainingDataCreator", "openai_api_key", api_key)
```

**Storage location by desktop environment:**
- **KDE Plasma**: KDE Wallet
- **GNOME**: GNOME Keyring
- **Other**: Secret Service API-compatible keyring

**Benefits:**
- ✅ Encrypted storage
- ✅ OS-level security
- ✅ Not stored in plain text
- ✅ Survives package updates
- ✅ Separate per user

### Voice Sample Storage

Voice samples are stored in a user-specified directory, configured through the Settings dialog:

**Default suggestion**: `~/voice_samples/` or `~/ai/training/voice/`

**Benefits:**
- ✅ User controls location
- ✅ Never touched by package manager
- ✅ Can be on external drive or NAS
- ✅ Easy to backup separately
- ✅ Not deleted on uninstall

## Build Process

### Building the Package

```bash
./build-deb.sh
```

The build script:
1. Cleans previous builds
2. Creates debian package structure
3. Copies application files (excluding `.git`, `.venv`, etc.)
4. Sets correct permissions
5. Builds the .deb package using `dpkg-deb`

### Build Dependencies

- `dpkg-dev` - Debian package building tools
- `rsync` - For efficient file copying
- `ImageMagick` (convert) - For icon conversion

## Installation Process

### What Happens During Installation

1. **Package extraction**: Files copied to system directories
2. **postinst script runs**:
   - Creates virtual environment at `/usr/lib/voice-training-data-creator/venv/`
   - Installs Python dependencies from `requirements.txt`
   - Updates desktop database
   - Updates icon cache

### Dependencies

**System packages** (automatically installed):
- python3 (>= 3.10)
- python3-pip
- python3-venv
- python3-pyqt6
- python3-numpy
- libportaudio2

**Python packages** (installed in venv):
- PyQt6 >= 6.6.0
- sounddevice >= 0.4.6
- soundfile >= 0.12.1
- numpy >= 1.24.0
- openai >= 1.12.0
- keyring >= 24.3.0

## Uninstallation Process

### Remove Package

```bash
sudo apt-get remove voice-training-data-creator
```

**What gets removed:**
- Application files in `/usr/lib/voice-training-data-creator/`
- Virtual environment
- Executable in `/usr/bin/`
- Desktop entry
- Icon

**What stays:**
- User configuration in `~/.config/VoiceTrainingDataCreator/`
- API keys in system keyring
- Voice samples (always)

### Purge Package

```bash
sudo apt-get purge voice-training-data-creator
```

**Additionally removes:**
- Virtual environment (if not already removed)
- Updates desktop/icon caches

**Still preserved:**
- User configuration (manually delete if desired)
- API keys (manually delete if desired)
- Voice samples (always preserved)

## Validation

After installation, run the validation script:

```bash
./validate-package.sh
```

This checks:
- Package installation status
- Executable and permissions
- Application files and structure
- Virtual environment setup
- Python dependencies
- Desktop integration
- Documentation
- User configuration paths
- System dependencies
- PATH configuration

## Multi-User Support

The package supports multiple users on the same system:

- Each user gets their own:
  - Configuration in `~/.config/VoiceTrainingDataCreator/`
  - API key in their keyring
  - Voice sample directory

- Shared components:
  - Application code in `/usr/lib/voice-training-data-creator/`
  - Virtual environment (read-only for users)

## Updates and Upgrades

When a new version is installed:

1. Old application files are replaced
2. Virtual environment is recreated with new dependencies
3. User configuration is **preserved**
4. API keys remain in keyring
5. Voice samples are unaffected

## Troubleshooting

### Virtual environment issues

Recreate the virtual environment:
```bash
sudo dpkg-reconfigure voice-training-data-creator
```

### API key not persisting

Check keyring status:
```bash
# Check if keyring is unlocked
keyring get VoiceTrainingDataCreator openai_api_key

# On KDE, ensure KDE Wallet is running:
ps aux | grep kwalletd
```

### Permission issues

Application runs with user permissions, storing data in user's home directory. No special permissions needed.

## Future Enhancements

Potential improvements for future versions:

1. **AppImage packaging** - For broader Linux distribution support
2. **Flatpak/Snap** - Alternative distribution methods
3. **Auto-updates** - Built-in update checking
4. **Release signing** - GPG-signed packages
5. **PPA repository** - For easier installation and updates

## License

See [copyright](debian/usr/share/doc/voice-training-data-creator/copyright) file for licensing information.
