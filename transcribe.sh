#!/bin/bash
set -e

# Pod-Tenuki Transcription Script
# This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki-transcribe tool

# Display usage information
function show_usage {
    echo "Usage: $0 <audio_file> [options]"
    echo ""
    echo "This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki-transcribe tool"
    echo ""
    echo "Options:"
    echo "  --output-file FILE    Path to save the transcription"
    echo "  --language CODE       Language code for transcription (default: ja-JP)"
    echo "  --verbose, -v         Enable verbose logging"
    echo ""
    echo "Example:"
    echo "  $0 podcast.mp3 --verbose"
    exit 1
}

# Check if an audio file was provided
if [ $# -eq 0 ] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
fi

AUDIO_FILE="$1"
shift

# Check if the audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    exit 1
fi

# Set up virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Always reinstall dependencies with pip3
echo "Installing pod-tenuki and dependencies..."
pip3 install -e .

# Install additional audio processing dependencies
echo "Installing audio processing dependencies..."
pip3 install pydub ffmpeg-python simpleaudio pyaudio

# Run the pod-tenuki-transcribe tool with the provided arguments
echo "Running pod-tenuki-transcribe with $AUDIO_FILE..."
pod-tenuki-transcribe "$AUDIO_FILE" "$@"

# Deactivate virtual environment
deactivate

echo "Done!"
