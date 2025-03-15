#!/usr/bin/env python3
"""
CLI tool for summarizing transcripts using OpenAI API.

This script provides a command-line interface for summarizing transcripts
to generate podcast titles and descriptions using the OpenAI API.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to allow importing from pod_tenuki
sys.path.insert(0, str(Path(__file__).parents[3]))

from pod_tenuki.utils.logger import setup_logger
from pod_tenuki.utils.config import validate_config
from pod_tenuki.utils.cost_tracker import cost_tracker
from pod_tenuki.summarizer import summarize_transcript

# Set up logger
logger = setup_logger("pod_tenuki.cli.summarize", logging.INFO)

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Summarize transcripts using OpenAI API."
    )
    
    parser.add_argument(
        "transcript_file",
        help="Path to the transcript file to summarize"
    )
    
    parser.add_argument(
        "--output-file",
        help="Path to save the summary (default: same name as input file with .summary.md extension)"
    )
    
    parser.add_argument(
        "--max-title-length",
        type=int,
        default=100,
        help="Maximum length of the generated title (default: 100)"
    )
    
    parser.add_argument(
        "--max-description-length",
        type=int,
        default=500,
        help="Maximum length of the generated description (default: 500)"
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
        transcript_file = args.transcript_file
        if not os.path.exists(transcript_file):
            logger.error(f"Transcript file not found: {transcript_file}")
            return 1
        
        # Create output file path if not provided
        output_file = args.output_file
        if not output_file:
            output_file = str(Path(transcript_file).with_suffix(".summary.md"))
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Summarize the transcript
        logger.info(f"Summarizing transcript: {transcript_file}")
        
        try:
            title, description, summary_path = summarize_transcript(
                transcript_file=transcript_file,
                output_file=output_file,
                max_title_length=args.max_title_length,
                max_description_length=args.max_description_length,
            )
            
            logger.info(f"Summarization complete. Title: {title}")
            logger.info(f"Summary saved to: {summary_path}")
            
            # Print summary of results
            logger.info("\n" + "=" * 50)
            logger.info("SUMMARIZATION COMPLETE")
            logger.info("=" * 50)
            logger.info(f"Podcast title: {title}")
            logger.info(f"Summary file: {summary_path}")
            
            # Print API usage costs
            logger.info("\n" + "=" * 50)
            logger.info(cost_tracker.format_cost_summary())
            logger.info("=" * 50)
            
            return 0
        
        except Exception as e:
            logger.error(f"Error summarizing transcript: {e}")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
