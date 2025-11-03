# Voice Training Data Creator

The objective of this repository is to create a desktop application for the user's use in aggregating voice samples for the purpose of training a custom TTS model and/or a STT fine-tune.

A detailed spec is provided; the Claude Spec should be preferred over the user draft.

## UI Framework

**Current**: Flet (Flutter-based)
**Previous**: PyQt6 (migrated due to persistent layout issues)

The application was recently migrated from PyQt6 to Flet for:
- Improved layout reliability (no resize bugs)
- Modern Flutter-based rendering
- Declarative UI patterns
- Better cross-platform support
- Material Design by default

## Architecture

- **Main UI**: Single-file Flet application (`src/main.py`)
- **Audio**: Recording and device management modules
- **Storage**: Configuration and sample management
- **LLM**: OpenAI-based text generation
- **Utils**: Validation utilities

## Development Notes

- Virtual environment managed with `uv`
- Run with `./run.sh`
- UI is declarative - modify `src/main.py` for interface changes
- Core logic remains unchanged from PyQt version