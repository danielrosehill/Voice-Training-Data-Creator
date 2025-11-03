Your task in this repository is to create a GUI for me to use with my voice cloning project - although this could also be helpful for STT fine-tuning.

Here's what I would like:

For voice training two things are needed, at scale: voice samples, source of truth texts. LLMs are a great fit for the latter as they can generate synthetic text on demand and can also provide synethetic text to match a certain style or with specific dictionary words.

I'd like to design this interface to incorporate all of these requirements. Deployment target = my desktop which is Ubuntu.

## Recording Panel

Record, pause, stop controls. 

Default to default system mic but have a toggle to be able to select a different one. 

"Test mic" functionality: record 3 second loop verify that there is an audio feed. 

## Base path definition

This app will require persistent storage on the local filesystem. 

On first run, user will be prompted for a save path. On subsequent runs, that will be set but the user can change it. 

## Synthetic Text Panel

In panel 2, create synthetic text. 

User parameters guide the synthetic text generation. By default: generate general purpose text sufficient to generate about 3 mins of audio.

But there should be a "style" button in which users can ask for one of these: Colloquial, Voice Note (simluated a dictated voice note), Technical, Prose 

Target length: generate enough text for X minutes. By default use a ballpark average WPM but the user can provide their own and if they do that gets added to the text gen prompt. 

Finally: use dictionary. Here, users can define a list of words to include in the generation. User should separate words with commas. Prompt will ask LLM to include these if they are provided. Otherwise that section of the constructed prompt is skipped.

## API Keys

OpenAI API with key persistence and the ability to change the key in settings.

## Saving Logic 
 
The app expects both an LLM generated text and a voice sample and validates for both when the user hits Save Sample

When the user does that:

- Program looks for {basepath}/samples
   If it's empty it creates it

Samples are notated with three digitas. First folder should be 001 

Within 001 app will save: 1.wav (voice recording), 1.txt (source of truth text - LLM generated)

NOTE:

The LLM generated text should be user-editable post generation. This is so that the user can remove non narrated text like "Here's your text:" although the AI should be instructed to not include any user messages like that. 

After success message: both fields reset (record and text) supporting an iterative workflow. On the next save 002 and files will be created. 