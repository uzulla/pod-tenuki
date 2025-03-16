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
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check and install system dependencies
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Checking system dependencies for macOS..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
        echo "Then run this script again."
        exit 1
    fi
    
    # Check for ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo "Installing ffmpeg..."
        brew install ffmpeg
    fi
    
    # Install portaudio for pyaudio
    if ! brew list portaudio &> /dev/null; then
        echo "Installing portaudio..."
        brew install portaudio
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Checking system dependencies for Linux..."
    if command -v apt-get &> /dev/null; then
        echo "Installing system dependencies..."
        sudo apt-get update
        sudo apt-get install -y ffmpeg python3-dev python3-pyaudio
    elif command -v yum &> /dev/null; then
        echo "Installing system dependencies..."
        sudo yum install -y ffmpeg python3-devel python3-pyaudio
    else
        echo "Warning: Unsupported Linux distribution. Please install ffmpeg and python3-pyaudio manually."
    fi
fi

# Install dependencies if needed
if ! pip show pod-tenuki &> /dev/null; then
    echo "Installing pod-tenuki and dependencies..."
    pip install -e .
    
    # Install additional Python dependencies
    echo "Installing additional audio processing dependencies..."
    pip install pyaudio
fi

# Run the pod-tenuki tool with the provided arguments
echo "Running pod-tenuki with $AUDIO_FILE..."
pod-tenuki "$AUDIO_FILE" "$@"

# Deactivate virtual environment
deactivate

echo "Done!"
