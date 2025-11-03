# Installation Guide

## Building from Source

### Prerequisites

- Ubuntu 24.04+ or Debian-based system
- Python 3.10 or higher
- Development tools: `build-essential`, `dpkg-dev`
- ImageMagick (for icon conversion)

### Build the .deb Package

1. Clone the repository:
```bash
git clone https://github.com/danielrosehill/Voice-Training-Data-Creator.git
cd Voice-Training-Data-Creator
```

2. Run the build script:
```bash
./build-deb.sh
```

This will create `voice-training-data-creator_1.0.0_all.deb`.

### Install the Package

```bash
sudo dpkg -i voice-training-data-creator_1.0.0_all.deb
sudo apt-get install -f  # Install any missing dependencies
```

### System Installation Details

When installed as a .deb package, the application is installed to:

- **Application files**: `/usr/lib/voice-training-data-creator/`
- **Executable**: `/usr/bin/voice-training-data-creator`
- **Desktop entry**: `/usr/share/applications/voice-training-data-creator.desktop`
- **Icon**: `/usr/share/icons/hicolor/256x256/apps/voice-training-data-creator.png`

### User Data Storage

User data is stored in your home directory:

- **Configuration**: `~/.config/VoiceTrainingDataCreator/config.json`
- **API Key**: Stored securely in your system keyring (KDE Wallet on KDE Plasma)
- **Voice samples**: User-specified location (configured in Settings)

This means:
- ✅ Your settings persist across application updates
- ✅ Your API key is stored securely
- ✅ Multiple users can use the application with separate settings
- ✅ Uninstalling the package won't delete your voice samples

### First Run

After installation:

1. Launch from the application menu or run:
```bash
voice-training-data-creator
```

2. Configure the application:
   - Set your base path for storing voice samples
   - Enter your OpenAI API key (stored securely in keyring)
   - Adjust audio settings if needed

3. Start creating voice training data!

### Uninstallation

To remove the application:

```bash
sudo apt-get remove voice-training-data-creator
```

To remove including all configuration (purge):

```bash
sudo apt-get purge voice-training-data-creator
```

**Note**: Your voice samples are NOT deleted during uninstallation. Only the application configuration in `~/.config/VoiceTrainingDataCreator/` is removed on purge.

### Dependencies

The package automatically handles Python dependencies by creating a virtual environment at `/usr/lib/voice-training-data-creator/venv/` during installation.

Required system packages:
- python3 (>= 3.10)
- python3-pip
- python3-venv
- python3-pyqt6
- python3-numpy
- libportaudio2

Python packages (installed automatically in venv):
- PyQt6 >= 6.6.0
- sounddevice >= 0.4.6
- soundfile >= 0.12.1
- numpy >= 1.24.0
- openai >= 1.12.0
- keyring >= 24.3.0

### Troubleshooting

**Virtual environment not found**:
```bash
sudo dpkg-reconfigure voice-training-data-creator
```

**Permission issues**:
The application runs with your user permissions and stores data in your home directory, so no special permissions are needed.

**API key not persisting**:
Ensure your system keyring (KDE Wallet, GNOME Keyring, etc.) is properly configured and unlocked.

### Development Installation

For development, use the included `run.sh` script instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```
