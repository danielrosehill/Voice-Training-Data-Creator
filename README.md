# Voice Training Data Creator

![alt text](screenshots/1.png)

A desktop GUI application for creating voice training datasets with AI-powered synthetic text generation. Supports voice cloning, TTS model training, and STT fine-tuning workflows.

## Screenshots

![alt text](screenshots/2.png)

![alt text](screenshots/4.png)

![alt text](screenshots/5.png)

## Dataset System

Each sample is saved as a numbered folder (starting from 001) with:

- Recording (as .wav) 
- Text as .txt, incorporating user edits to scrub AI messages from source of truth 
- JSON for metadata

![alt text](screenshots/3.png)

## Features

### Audio Recording
- High-quality WAV recording (44.1kHz/48kHz, 16-bit)
- Microphone selection and testing
- Real-time audio level monitoring
- Pause/resume functionality
- Clipping and silence detection

### Text Generation
- Synthetic text generation using OpenAI GPT models
- Multiple style options:
  - General Purpose
  - Colloquial
  - Voice Note
  - Technical
  - Prose
- Custom vocabulary dictionary support
- Configurable duration and speaking rate (WPM)
- Post-generation text editing

### Sample Management
- Organized directory structure
- Automatic sample numbering
- Metadata tracking (generation parameters, timestamps)
- Session statistics
- Total duration estimation

### Configuration and Settings
- Secure API key storage (system keyring)
- Configurable audio quality settings
- Multiple OpenAI model support
- Persistent base path configuration

### Quality Assurance
- Audio validation (silence, clipping detection)
- Text validation
- Disk space checking
- Real-time quality warnings

## Installation

### Option 1: Install .deb Package (Recommended)

Standard installation method for Ubuntu/Debian systems:

1. **Download or build the package**:
   ```bash
   # Option A: Build from source
   git clone https://github.com/danielrosehill/Voice-Training-Data-Creator.git
   cd Voice-Training-Data-Creator
   ./build-deb.sh

   # Option B: Download release (when available)
   # Download voice-training-data-creator_1.0.0_all.deb from releases
   ```

2. **Install the package**:
   ```bash
   sudo dpkg -i voice-training-data-creator_1.0.0_all.deb
   sudo apt-get install -f  # Install dependencies
   ```

3. **Validate installation** (optional):
   ```bash
   ./validate-package.sh
   ```

4. **Launch the application**:
   - From application menu: Search for "Voice Training Data Creator"
   - From terminal: `voice-training-data-creator`

See [INSTALL.md](INSTALL.md) for detailed installation instructions and troubleshooting.

### Option 2: Run from Source

For development or if you prefer not to install system-wide:

#### Prerequisites

- Python 3.10 or higher
- Ubuntu Desktop (tested on Ubuntu 25.04 with KDE)
- System packages: `libportaudio2`
- OpenAI API key (for text generation)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Voice-Training-Data-Creator.git
cd Voice-Training-Data-Creator
```

2. The application uses `uv` for virtual environment management. If you don't have it installed:
```bash
pip install uv
```

3. Create and activate virtual environment, then install dependencies:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Usage

### Running the Application

Use the provided launcher script:
```bash
./run.sh
```

Or manually:
```bash
source .venv/bin/activate
python src/main.py
```

### First-Time Setup

1. **Configure Base Path**: On first launch, you'll be prompted to set a base directory for storing samples
2. **Add API Key**: Go to Settings → API Configuration and enter your OpenAI API key
3. **Test Connection**: Click "Test Connection" to verify your API key works

### Creating Samples

1. **Select Microphone**: Choose your input device from the dropdown
2. **Test Microphone** (optional): Click "Test Mic" to verify audio input
3. **Generate Text**:
   - Set target duration (minutes)
   - Choose words per minute (WPM)
   - Select a style
   - Optionally add custom vocabulary
   - Click "Generate Text"
4. **Record Audio**:
   - Click "Record" to start
   - Monitor audio levels (avoid red/clipping)
   - Use "Pause" if needed
   - Click "Stop" when finished
5. **Review**: Edit the generated text if needed
6. **Save**: Click "Save Sample" (Ctrl+Enter)

### Keyboard Shortcuts

- `Ctrl+Return`: Save sample
- `Ctrl+G`: Generate text
- `Ctrl+,`: Open settings
- `Ctrl+Q`: Quit application

## Directory Structure

Samples are organized as follows:

```
{base_path}/
└── samples/
    ├── 001/
    │   ├── 1.wav              # Audio recording
    │   ├── 1.txt              # Source text
    │   └── 1_metadata.json    # Generation parameters
    ├── 002/
    │   ├── 2.wav
    │   ├── 2.txt
    │   └── 2_metadata.json
    └── ...
```

## Configuration

Configuration is stored in `~/.config/VoiceTrainingDataCreator/config.json`

API keys are stored securely in the system keyring.

## Troubleshooting

### No Audio Devices Found
- Ensure your microphone is connected
- Check system audio settings
- Verify permissions for microphone access

### API Connection Fails
- Verify your API key is correct
- Check internet connectivity
- Ensure you have sufficient OpenAI credits

### Audio Clipping Warning
- Reduce microphone input volume in system settings
- Move further from the microphone
- Adjust microphone gain if available

### Long Silence Detected
- Re-record the sample
- Check microphone is not muted
- Verify microphone is selected correctly

## Development

### Project Structure

```
Voice-Training-Data-Creator/
├── src/
│   ├── main.py              # Application entry point
│   ├── audio/               # Audio recording modules
│   │   ├── recorder.py
│   │   └── device_manager.py
│   ├── llm/                 # LLM integration
│   │   ├── generator.py
│   │   └── prompt_builder.py
│   ├── storage/             # Configuration and data storage
│   │   ├── config.py
│   │   └── sample_manager.py
│   ├── main.py              # Flet UI (single-file architecture)
│   └── utils/               # Validation utilities
│       └── validators.py
├── requirements.txt
├── run.sh                   # Launcher script
└── README.md
```

### Dependencies

- **Flet**: Modern GUI framework (Flutter-based)
- **sounddevice**: Audio recording
- **soundfile**: WAV file handling
- **numpy**: Audio processing
- **openai**: LLM text generation
- **keyring**: Secure credential storage

### UI Framework Migration Note

This application was recently migrated from PyQt6 to Flet for improved layout reliability and modern UI patterns. Flet provides:
- Flutter-based rendering with predictable layouts
- Declarative UI architecture
- Better cross-platform support
- Material Design by default

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

Built with:
- Flet (Flutter) for the GUI
- OpenAI GPT for text generation
- sounddevice for audio recording
