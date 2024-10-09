
# Real-Time Audio Translation and Playback with OpenAI

This Python script captures live audio input, transcribes it, translates it into Spanish, and plays back the translation as speech. The script is designed for a live event context, focusing on translations aligned with the teachings of the Church of Jesus Christ of Latter-day Saints.

## Features

- **Audio Capture**: Listens to real-time audio from the default microphone.
- **Transcription**: Converts captured audio into text using OpenAI's Whisper model.
- **Translation**: Translates transcribed text to Spanish with contextual adjustments.
- **Text-to-Speech**: Generates audio output of the Spanish translation.
- **Playback**: Streams the translated speech output for real-time playback.

## Prerequisites

- Python 3.x
- [OpenAI API Key](https://platform.openai.com/account/api-keys)
- [FFmpeg](https://ffmpeg.org/download.html) installed and accessible in your PATH.

## Installation

### 1. Clone the Repository
   ```bash
   git clone https://github.com/pvankatwyk/translate.git
   cd translate
   ```

### 2. Install Dependencies with Poetry
   Ensure Poetry is installed on your system. If not, you can install it by following the instructions [here](https://python-poetry.org/docs/#installation).
   ```bash
   poetry install
   ```

### 3. Set up FFmpeg
   - Ensure FFmpeg is installed and available in your PATH.
   - Update `pydub` configuration in the script if needed:
     ```python
     pydub.AudioSegment.ffmpeg = r"C:\ffmpeg\bin"
     AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
     ```

### 4. Set OpenAI API Key
   Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

## Usage

Run the script with Poetry:
```bash
poetry run python translate/translate.py
```

### How It Works

- **Audio Listening**: Captures audio data in chunks and analyzes it for silence. Non-silent audio is queued for transcription.
- **Transcription and Translation**: Transcribes audio and translates it to Spanish, filtering out unwanted phrases.
- **Playback**: Plays back translated text as speech and automatically removes temporary files after playback.

### Customization

- **Silence Threshold**: Adjust `silence_threshold` in the `listen_audio` function to better suit your environment.
- **Unwanted Phrases**: Add phrases to `unwanted_phrases` to filter out common non-essential content.

## Troubleshooting

- **Stream Errors**: If errors occur with audio streams, ensure your microphone is accessible and configured correctly.
- **FFmpeg Issues**: If playback fails, check that FFmpeg is installed correctly and accessible from your PATH.
- **OpenAI Errors**: If API calls fail, ensure the API key is correct and that you have internet access.

## License

This project is licensed under the MIT License.
