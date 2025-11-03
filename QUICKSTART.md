# Quick Start Guide

## Installation (5 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd Voice-Training-Data-Creator

# Install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## First Launch

```bash
./run.sh
```

## Initial Setup

### 1. Set Base Path (First Launch)
- You'll be prompted to select a directory
- Choose where you want to store your voice samples
- Example: `~/voice_training_data`

### 2. Configure API Key
1. Go to **File → Settings**
2. Click **API Configuration** tab
3. Enter your OpenAI API key
4. Select model (recommend `gpt-4o-mini` for cost-effectiveness)
5. Click **Test Connection** to verify
6. Click **Save**

## Creating Your First Sample

### Step 1: Generate Text
1. Set **Target Duration**: `3.0` minutes (default)
2. Set **Words Per Minute**: `150` (default)
3. Choose **Style**: Select from dropdown
4. (Optional) Enable **Use Custom Dictionary** and add words
5. Click **Generate Text** (or press `Ctrl+G`)
6. Wait for text to generate (5-15 seconds)
7. Edit the text if needed

### Step 2: Record Audio
1. Select your **Microphone** from dropdown
2. (Optional) Click **Test Mic** to verify it works
3. Click **⏺ Record** button
4. Read the generated text aloud
5. Watch the audio level meter (keep it in the green/yellow range, avoid red)
6. Click **⏹ Stop** when finished

### Step 3: Save Sample
1. Review the audio duration matches roughly the text length
2. Click **💾 Save Sample** (or press `Ctrl+Enter`)
3. Your sample is saved automatically!

## Tips for Best Results

### Audio Quality
- Use a good quality microphone
- Record in a quiet environment
- Keep audio levels moderate (avoid clipping - red levels)
- Position microphone consistently

### Text Generation
- Start with 3-minute samples
- Use custom dictionary for domain-specific vocabulary
- Experiment with different styles for variety
- Edit generated text for naturalness

### Workflow Efficiency
- Use keyboard shortcuts (`Ctrl+G` to generate, `Ctrl+Enter` to save)
- Test microphone once per session
- Generate text while reviewing previous recordings
- Keep sessions focused (15-20 samples)

## Understanding the Output

Your samples are saved in this structure:

```
{base_path}/
└── samples/
    ├── 001/
    │   ├── 1.wav              # Your voice recording
    │   ├── 1.txt              # The text you read
    │   └── 1_metadata.json    # Generation parameters
    ├── 002/
    │   ├── 2.wav
    │   ├── 2.txt
    │   └── 2_metadata.json
    └── ...
```

## Troubleshooting

### "No audio devices found"
- Check microphone is connected
- Restart the application
- Check system audio settings

### "API connection failed"
- Verify API key in Settings
- Check internet connection
- Verify OpenAI account has credits

### Audio sounds clipped/distorted
- Lower microphone gain/volume
- Move further from microphone
- Check the red clipping warning

### Text generation is slow
- Normal for first generation (10-15 seconds)
- Check internet connection
- Consider using `gpt-4o-mini` for faster generation

## Next Steps

1. Create 10-20 samples to get comfortable
2. Listen back to verify quality
3. Experiment with different styles
4. Add custom vocabulary for your use case
5. Monitor session statistics for progress

## Support

See [README.md](README.md) for full documentation.
