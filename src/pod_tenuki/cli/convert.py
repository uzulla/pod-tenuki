#!/usr/bin/env python3
"""
CLI tool for converting audio files using Auphonic API.

This script provides a command-line interface for converting audio files
using the Auphonic API with specified presets.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

# Add parent directory to path to allow importing from pod_tenuki
sys.path.insert(0, str(Path(__file__).parents[3]))

from pod_tenuki.utils.logger import setup_logger
from pod_tenuki.utils.config import validate_config
from pod_tenuki.audio_converter import process_audio_file

# Set up logger
logger = setup_logger("pod_tenuki.cli.convert", logging.INFO)

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert audio files using Auphonic API."
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to the audio file to process (MP3, MP4, m4a, etc.)"
    )
    
    parser.add_argument(
        "--preset-uuid",
        default="xbyREqwaKxENW2n5V2y3mg",
        help="UUID of the Auphonic preset to use (default: xbyREqwaKxENW2n5V2y3mg)"
    )
    
    parser.add_argument(
        "--preset-name",
        help="Name of the Auphonic preset to use (alternative to --preset-uuid)"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Directory to save output files (default: same directory as input file)"
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
        
        # Validate input file
        audio_file = args.audio_file
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return 1
        
        # Create output directory if specified
        output_dir = args.output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Process audio with Auphonic
        logger.info(f"Processing audio file: {audio_file}")
        
        try:
            processed_files, production_info = process_audio_file(
                audio_file=audio_file,
                preset_uuid=args.preset_uuid,
                preset_name=args.preset_name,
                output_dir=output_dir,
            )
            
            if not processed_files:
                logger.warning("No processed files were returned")
                return 1
            
            logger.info(f"Audio processing complete. Files: {', '.join(processed_files)}")
            
            # Print summary of results
            logger.info("\n" + "=" * 50)
            logger.info("PROCESSING COMPLETE")
            logger.info("=" * 50)
            logger.info(f"Processed audio files: {', '.join(processed_files)}")
            
            if production_info:
                logger.info(f"Production UUID: {production_info.get('uuid', 'N/A')}")
                logger.info(f"Production status: {production_info.get('status', 'N/A')}")
            
            return 0
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
