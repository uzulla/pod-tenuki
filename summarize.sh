#!/bin/bash
set -e

# Pod-Tenuki Summarization Script
# This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki-summarize tool

# Display usage information
function show_usage {
    echo "Usage: $0 <transcript_file> [options]"
    echo ""
    echo "This script sets up a virtual environment, installs dependencies, and runs the pod-tenuki-summarize tool"
    echo ""
    echo "Options:"
    echo "  --output-file FILE    Path to save the summary"
    echo "  --verbose, -v         Enable verbose logging"
    echo ""
    echo "Example:"
    echo "  $0 podcast.txt --verbose"
    exit 1
}

# Check if a transcript file was provided
if [ $# -eq 0 ] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
fi

TRANSCRIPT_FILE="$1"
shift

# Check if the transcript file exists
if [ ! -f "$TRANSCRIPT_FILE" ]; then
    echo "Error: Transcript file '$TRANSCRIPT_FILE' not found"
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

# Install dependencies if needed
if ! pip show pod-tenuki &> /dev/null; then
    echo "Installing pod-tenuki and dependencies..."
    pip install -e .
fi

# Run the pod-tenuki-summarize tool with the provided arguments
echo "Running pod-tenuki-summarize with $TRANSCRIPT_FILE..."
pod-tenuki-summarize "$TRANSCRIPT_FILE" "$@"

# Deactivate virtual environment
deactivate

echo "Done!"
