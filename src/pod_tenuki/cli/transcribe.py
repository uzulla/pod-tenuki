#!/usr/bin/env python3
"""
CLI tool for transcribing audio files using Gemini API.

This script provides a command-line interface for transcribing audio files
using the Gemini API.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow importing from pod_tenuki
sys.path.insert(0, str(Path(__file__).parents[3]))

from pod_tenuki.utils.logger import setup_logger
from pod_tenuki.utils.config import validate_config
from pod_tenuki.utils.cost_tracker import cost_tracker
from pod_tenuki.transcriber import transcribe_audio_file
from pod_tenuki.audio_converter import concatenate_wav_files

# Set up logger
logger = setup_logger("pod_tenuki.cli.transcribe", logging.INFO)

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Gemini API."
    )
    
    parser.add_argument(
        "audio_files",
        nargs='+',
        help="Path(s) to the audio file(s) to transcribe (MP3, MP4, m4a, WAV, etc.). Multiple WAV files will be concatenated."
    )
    
    parser.add_argument(
        "--output-name",
        help="Name for the output file when concatenating multiple files"
    )
    
    parser.add_argument(
        "--output-file",
        help="Path to save the transcription (default: same name as input file with .txt extension)"
    )
    
    parser.add_argument(
        "--language",
        default="ja-JP",
        help="Language code for transcription (default: ja-JP)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main() -> int:
    """Main entry point for the application."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Set log level
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return 1
        
        # Validate input files
        audio_files = args.audio_files
        for audio_file in audio_files:
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return 1
        
        # Check if we need to concatenate multiple WAV files
        input_audio_file = audio_files[0]
        if len(audio_files) > 1 and all(Path(f).suffix.lower() == '.wav' for f in audio_files):
            logger.info(f"Detected multiple WAV files, concatenating {len(audio_files)} files...")
            try:
                # Use specified output directory or default to ./output
                output_dir = os.path.dirname(args.output_file) if args.output_file else os.path.join(os.getcwd(), "output")
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Using output directory: {output_dir}")
                
                input_audio_file = concatenate_wav_files(
                    wav_files=audio_files,
                    output_dir=output_dir,
                    output_name=args.output_name
                )
                logger.info(f"Successfully concatenated files to: {input_audio_file}")
            except Exception as e:
                logger.error(f"Failed to concatenate WAV files: {e}")
                return 1
        elif len(audio_files) > 1:
            logger.warning("Multiple input files provided but not all are WAV files. Using only the first file.")
        
        # Create output file path if not provided
        output_file = args.output_file
        if not output_file:
            output_file = str(Path(input_audio_file).with_suffix(".txt"))
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Transcribe the audio
        logger.info(f"Transcribing audio file: {input_audio_file}")
        
        try:
            transcript_path = transcribe_audio_file(
                audio_file=input_audio_file,
                output_file=output_file,
                language_code=args.language,
            )
            
            logger.info(f"Transcription complete. Saved to: {transcript_path}")
            
            # Print summary of results
            logger.info("\n" + "=" * 50)
            logger.info("TRANSCRIPTION COMPLETE")
            logger.info("=" * 50)
            logger.info(f"Transcript file: {transcript_path}")
            
            # Print API usage costs
            logger.info("\n" + "=" * 50)
            logger.info(cost_tracker.format_cost_summary())
            logger.info("=" * 50)
            
            return 0
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
