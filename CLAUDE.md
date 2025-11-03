# Voice Training Data Creator

The objective of this repository is to create a desktop application for aggregating voice samples for training custom TTS models and/or STT fine-tuning.

A detailed spec is provided; the Claude Spec should be preferred over the user draft.

## UI Framework

**Current**: Flet (Flutter-based)
**Previous**: PyQt6 (migrated due to persistent layout issues)

The application was migrated from PyQt6 to Flet for:
- Improved layout reliability (no resize bugs)
- Modern Flutter-based rendering
- Declarative UI patterns
- Better cross-platform support
- Material Design by default

## Application Structure

### Three-Tab Interface

1. **Record & Generate Tab**
   - Text generation with OpenAI GPT models
   - Audio recording with pause/resume
   - New Sample button (clears state and starts fresh)
   - Retake button (discard and restart recording in one click)
   - Save sample workflow

2. **Dataset Tab**
   - Total sample count and duration statistics
   - Personalized goal progress tracking
   - Quick access to dataset folder
   - Training data completion percentage

3. **Settings Tab**
   - Base path configuration
   - OpenAI API key and model selection with test button
   - Preferred microphone selection (auto-selected on recording)
   - Sample rate configuration
   - Training goal duration (personalizes progress tracking)
   - Auto-generate next sample preference

## Architecture

- **Main UI**: Single-file Flet application (`src/main.py`)
- **Audio**: Recording and device management modules (`audio/`)
- **Storage**: Configuration and sample management (`storage/`)
- **LLM**: OpenAI-based text generation (`llm/`)
- **Utils**: Validation utilities (`utils/`)

## Key Features

### Workflow Improvements
- **New Sample**: Clears both text and audio, starts completely fresh
- **Retake**: During recording, instantly discard and restart (no need for stop → delete → record)
- **Preferred Microphone**: Set once in Settings, auto-selected every time
- **Goal Tracking**: Personalized progress based on your target duration

### Configuration
- Settings stored in `~/.config/VoiceTrainingDataCreator/config.json`
- API keys stored securely in system keyring
- Persistent preferences (microphone, sample rate, goal duration)

## Development Notes

- Virtual environment managed with `uv`
- Run with `./run.sh`
- UI is declarative - modify `src/main.py` for interface changes
- Core audio/LLM logic remains modular and testable