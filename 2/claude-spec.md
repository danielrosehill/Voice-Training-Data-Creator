# Voice Training Data Creator - Specification

## Overview

This application is a GUI tool designed for voice cloning and speech-to-text (STT) fine-tuning projects. It facilitates the creation of paired voice samples and source-of-truth texts at scale, leveraging LLMs to generate synthetic text that matches specific styles and incorporates custom vocabulary.

**Deployment Target**: Ubuntu Desktop

## Core Features

### 1. Recording Panel

**Audio Recording Controls:**
- Record, pause, and stop buttons
- Visual feedback for recording state (recording/paused/stopped)
- Duration timer display during recording

**Microphone Management:**
- Default: Use system default microphone
- Dropdown/selector to choose from available input devices
- "Test Mic" functionality:
  - Records a 3-second audio loop
  - Plays back the recording to verify audio feed
  - Displays visual waveform or volume meter to confirm signal

**Audio Quality:**
- Record in WAV format (uncompressed, suitable for training)
- Sample rate: 44.1kHz or 48kHz (configurable in settings)
- Bit depth: 16-bit minimum

### 2. Base Path Configuration

**Persistent Storage Management:**

**First Run:**
- Prompt user to select a base directory for storing samples
- Validate write permissions
- Create necessary subdirectories (`/samples`)
- Save configuration for subsequent sessions

**Subsequent Runs:**
- Load saved base path automatically
- Display current base path in settings/UI
- Provide "Change Base Path" option in settings
- Validate new path and migrate if necessary (optional feature)

**Directory Structure:**
```
{base_path}/
└── samples/
    ├── 001/
    │   ├── 1.wav
    │   └── 1.txt
    ├── 002/
    │   ├── 2.wav
    │   └── 2.txt
    └── ...
```

### 3. Synthetic Text Generation Panel

**Text Generation Parameters:**

**Length Control:**
- **Target Duration**: Generate text for X minutes of audio (default: 3 minutes)
- **Words Per Minute (WPM)**:
  - Default: Use ballpark average (e.g., 150 WPM for conversational speech)
  - Custom: Allow user to input their own WPM
  - If custom WPM provided, include in LLM prompt for appropriate text length

**Style Selection:**
- Dropdown or button group with options:
  - **General Purpose** (default): Neutral, varied content
  - **Colloquial**: Casual, everyday speech patterns
  - **Voice Note**: Simulates dictated voice notes with natural pauses and thinking patterns
  - **Technical**: Technical/professional language and terminology
  - **Prose**: Literary, narrative style

**Dictionary Integration:**
- **Use Dictionary** toggle/checkbox
- Text input field for comma-separated words
- When enabled: LLM prompt instructs inclusion of specified words
- When disabled: Skip dictionary section in prompt
- Validation: Show warning if dictionary is very large (e.g., >50 words)

**Text Generation:**
- "Generate Text" button
- Loading indicator during generation
- Display generated text in editable text area
- "Regenerate" button to create new text with same parameters
- Character/word count display

**Post-Generation Editing:**
- Multi-line text editor for generated content
- Allow user to edit/refine text before saving
- Remove any LLM meta-commentary (e.g., "Here's your text:")
- Prompt engineering should minimize need for manual cleanup

### 4. API Configuration

**OpenAI Integration:**
- API key input field (masked/password field)
- "Test API Key" button to validate connectivity
- Persistent storage of API key (encrypted/secure storage)
- Settings panel to change API key
- Model selection dropdown (e.g., gpt-4, gpt-3.5-turbo)
- Error handling for:
  - Invalid API key
  - Rate limits
  - Network connectivity issues
  - Insufficient credits

### 5. Saving Logic

**Validation:**
- Before saving, verify both components exist:
  - Audio recording is not empty
  - Text content is not empty
- Display validation errors if either is missing

**Save Process:**

1. **Directory Management:**
   - Check if `{base_path}/samples` exists; create if not
   - Scan existing folders to determine next numeric folder (001, 002, etc.)
   - Create next numbered folder

2. **File Creation:**
   - Save audio as `{folder_number}.wav` (e.g., `001/1.wav`)
   - Save text as `{folder_number}.txt` (e.g., `001/1.txt`)
   - File naming: use same number as parent folder for consistency

3. **Post-Save Actions:**
   - Display success message with saved location
   - Clear/reset recording (remove audio buffer)
   - Clear/reset text field
   - Increment internal counter for next sample
   - Enable iterative workflow without restarting app

4. **Error Handling:**
   - Insufficient disk space
   - Write permission errors
   - File system errors
   - Display clear error messages to user

### 6. Additional Features & Improvements

**Session Management:**
- Display current session statistics:
  - Number of samples recorded in current session
  - Total samples in base path
  - Estimated total duration of recorded audio

**Metadata Tracking:**
- Optional: Save metadata file with each sample:
  - Recording date/time
  - Generation parameters (style, WPM, dictionary used)
  - Model used for text generation
  - Audio specifications (sample rate, bit depth)

**Export Functionality:**
- Export session summary (CSV/JSON) with all samples and metadata
- Batch export for training dataset preparation

**Quality Assurance:**
- Audio level meter during recording to prevent clipping
- Silence detection warning (if recording contains long silent periods)
- Text-audio length mismatch warning (if text seems too long/short for recording)

**Settings Panel:**
- Audio recording settings (format, sample rate, bit depth)
- API configuration (key, model selection)
- Default text generation parameters
- Base path management
- Theme/appearance options (light/dark mode)

**Keyboard Shortcuts:**
- Record: Space bar or Ctrl+R
- Stop: Escape or Ctrl+S
- Save: Ctrl+Enter
- Generate Text: Ctrl+G

**Undo/Redo:**
- Allow undo of text edits
- Confirm before discarding unsaved recording

## Technical Considerations

**Audio Processing:**
- Use appropriate audio library (e.g., PyAudio, SoundDevice for Python)
- Ensure low-latency recording
- Implement proper buffer management

**LLM Integration:**
- Construct prompts dynamically based on user parameters
- Example prompt structure:
  ```
  Generate {duration}-minute worth of text ({word_count} words) in a {style} style.
  [If dictionary]: Include these words naturally: {comma_separated_words}
  [If custom WPM]: Assume reading pace of {wpm} words per minute.
  Generate only the text content without any meta-commentary or introduction.
  ```

**Data Integrity:**
- Atomic saves to prevent partial file creation
- Verify file writes were successful
- Optional: Calculate and store checksums

**Cross-Platform Considerations:**
- While target is Ubuntu, structure code to be potentially portable
- Use pathlib for path handling
- Handle file system differences gracefully

## UI/UX Guidelines

**Layout:**
- Clear visual separation between recording and text generation sections
- Logical workflow: left-to-right or top-to-bottom
- Save button prominently placed and clearly labeled
- Status indicators for all async operations

**Feedback:**
- Loading spinners for API calls
- Progress indicators for file operations
- Clear success/error messages
- Toast notifications for non-blocking feedback

**Accessibility:**
- Clear labels for all controls
- Keyboard navigation support
- High contrast mode option
- Screen reader compatibility (ARIA labels where applicable)

## Future Enhancements

- Multi-language support for text generation
- Audio effects/normalization options
- Integration with other LLM providers (Anthropic, local models via Ollama)
- Batch processing mode
- Cloud backup integration
- Collaborative features (share samples with team)
- Training pipeline integration (direct export to training tools)
