#!/bin/bash
set -e

# Pod-Tenuki Conversion Script
# This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki tool

# Display usage information
function show_usage {
    echo "Usage: $0 <audio_file> [options]"
    echo ""
    echo "This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki tool"
    echo ""
    echo "Options:"
    echo "  --preset-uuid UUID    UUID of the Auphonic preset to use"
    echo "  --preset-name NAME    Name of the Auphonic preset to use"
    echo "  --output-dir DIR      Directory to save output files"
    echo "  --language CODE       Language code for transcription (default: ja-JP)"
    echo "  --skip-conversion     Skip audio conversion with Auphonic"
    echo "  --skip-transcription  Skip audio transcription"
    echo "  --skip-summarization  Skip transcript summarization"
    echo "  --verbose, -v         Enable verbose logging"
    echo ""
    echo "Example:"
    echo "  $0 podcast.mp3 --skip-conversion --verbose"
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
    python -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
if ! pip show pod-tenuki &> /dev/null; then
    echo "Installing pod-tenuki and dependencies..."
    pip install -e .
fi

# Run the pod-tenuki tool with the provided arguments
echo "Running pod-tenuki with $AUDIO_FILE..."
pod-tenuki "$AUDIO_FILE" "$@"

# Deactivate virtual environment
deactivate

echo "Done!"
