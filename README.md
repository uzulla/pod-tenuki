# Pod-Tenuki

Pod-Tenuki is a command-line tool for processing podcast audio files. It provides the following features:

1. **Audio Conversion**: Convert audio files (MP3, MP4, m4a, etc.) using the Auphonic API with specified presets
2. **Transcription**: Transcribe audio files to text using Google Cloud Speech-to-Text API
3. **Summarization**: Generate podcast titles and descriptions from transcriptions using OpenAI API

## Installation

### Prerequisites

- Python 3.8 or higher
- Auphonic API key
- Google Cloud API credentials
- OpenAI API key

### Setup

1. Clone the repository:

```bash
git clone https://github.com/uzulla/pod-tenuki.git
cd pod-tenuki
```

2. Install the package:

```bash
pip install -e .
```

3. Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Basic Usage

```bash
pod-tenuki /path/to/your/audio_file.mp3
```

This will:
1. Convert the audio file using the default Auphonic preset
2. Transcribe the converted audio using Google Cloud Speech-to-Text
3. Generate a podcast title and description from the transcription

### Command-line Options

```
usage: pod-tenuki [-h] [--preset-uuid PRESET_UUID] [--preset-name PRESET_NAME]
                  [--output-dir OUTPUT_DIR] [--language LANGUAGE]
                  [--skip-conversion] [--skip-transcription]
                  [--skip-summarization] [--verbose]
                  audio_file

Process podcast audio files with Auphonic, transcribe, and summarize.

positional arguments:
  audio_file            Path to the audio file to process (MP3, MP4, m4a, etc.)

optional arguments:
  -h, --help            show this help message and exit
  --preset-uuid PRESET_UUID
                        UUID of the Auphonic preset to use (default: xbyREqwaKxENW2n5V2y3mg)
  --preset-name PRESET_NAME
                        Name of the Auphonic preset to use (alternative to --preset-uuid)
  --output-dir OUTPUT_DIR
                        Directory to save output files (default: same directory as input file)
  --language LANGUAGE   Language code for transcription (default: ja-JP)
  --skip-conversion     Skip audio conversion with Auphonic
  --skip-transcription  Skip audio transcription
  --skip-summarization  Skip transcript summarization
  --verbose, -v         Enable verbose logging
```

### Examples

#### Convert audio only:

```bash
pod-tenuki --skip-transcription --skip-summarization audio_file.mp3
```

#### Transcribe audio only (skip conversion):

```bash
pod-tenuki --skip-conversion --skip-summarization audio_file.mp3
```

#### Summarize an existing transcript:

```bash
pod-tenuki --skip-conversion --skip-transcription audio_file.mp3
# Note: This assumes audio_file.txt exists
```

#### Specify output directory:

```bash
pod-tenuki --output-dir /path/to/output audio_file.mp3
```

#### Use a different Auphonic preset:

```bash
pod-tenuki --preset-uuid YOUR_PRESET_UUID audio_file.mp3
```

#### Specify language for transcription:

```bash
pod-tenuki --language en-US audio_file.mp3
```

## API Keys

### Auphonic API

1. Sign up for an Auphonic account at [auphonic.com](https://auphonic.com/)
2. Get your API key from the [Account Settings page](https://auphonic.com/engine/account/)
3. Add the API key to your `.env` file:

```
AUPHONIC_API_KEY=your_auphonic_api_key
```

### Google Cloud API

1. Create a Google Cloud project
2. Enable the Speech-to-Text API
3. Create a service account and download the JSON key file
4. Add the path to the key file and project ID to your `.env` file:

```
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials_json_file
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
```

### OpenAI API

1. Sign up for an OpenAI account at [openai.com](https://openai.com/)
2. Create an API key in the [API keys section](https://platform.openai.com/api-keys)
3. Add the API key to your `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
```

## Output Files

For an input file `podcast.mp3`, the following files will be created:

- Converted audio file(s): Depends on the Auphonic preset settings
- Transcript: `podcast.txt`
- Summary: `podcast.summary.md`

## License

MIT
