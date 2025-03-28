#!/usr/bin/env python3
"""
Pod-Tenuki: A tool for processing podcast audio files.

This script provides a command-line interface for:
1. Converting audio files using Auphonic API
2. Transcribing audio using Google Cloud Speech-to-Text
3. Summarizing transcriptions to generate podcast titles and descriptions
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from pod_tenuki.utils.logger import setup_logger
from pod_tenuki.utils.config import validate_config
from pod_tenuki.utils.cost_tracker import cost_tracker
from pod_tenuki.audio_converter import process_audio_file, concatenate_wav_files
from pod_tenuki.transcriber import transcribe_audio_file
from pod_tenuki.summarizer import summarize_transcript

# Set up logger
logger = setup_logger("pod_tenuki", logging.INFO)

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process podcast audio files with Auphonic, transcribe, and summarize."
    )
    
    parser.add_argument(
        "audio_files",
        nargs='+',
        help="Path(s) to the audio file(s) to process (MP3, MP4, m4a, WAV, etc.). Multiple WAV files will be concatenated."
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
        "--output-name",
        help="Name for the output file when concatenating multiple files"
    )
    
    parser.add_argument(
        "--language",
        default="ja-JP",
        help="Language code for transcription (default: ja-JP)"
    )
    
    parser.add_argument(
        "--skip-conversion",
        action="store_true",
        help="Skip audio conversion with Auphonic"
    )
    
    parser.add_argument(
        "--skip-transcription",
        action="store_true",
        help="Skip audio transcription"
    )
    
    parser.add_argument(
        "--skip-summarization",
        action="store_true",
        help="Skip transcript summarization"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def process_audio(
    audio_file: str,
    preset_uuid: Optional[str] = None,
    preset_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    skip_conversion: bool = False,
) -> List[str]:
    """
    Process an audio file using Auphonic API.
    
    Args:
        audio_file: Path to the audio file.
        preset_uuid: UUID of the preset to use.
        preset_name: Name of the preset to use.
        output_dir: Directory to save the processed files.
        skip_conversion: Whether to skip audio conversion.
    
    Returns:
        List of paths to processed audio files.
    """
    if skip_conversion:
        logger.info("Skipping audio conversion")
        return [audio_file]
    
    logger.info(f"Processing audio file: {audio_file}")
    
    try:
        processed_files, _ = process_audio_file(
            audio_file=audio_file,
            preset_uuid=preset_uuid,
            preset_name=preset_name,
            output_dir=output_dir,
        )
        
        if not processed_files:
            logger.warning("No processed files were returned")
            return [audio_file]
        
        logger.info(f"Audio processing complete. Files: {', '.join(processed_files)}")
        return processed_files
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        logger.warning("Using original audio file for next steps")
        return [audio_file]

def transcribe_audio(
    audio_file: str,
    language_code: str = "ja-JP",
    output_dir: Optional[str] = None,
    skip_transcription: bool = False,
) -> Optional[str]:
    """
    Transcribe an audio file using Gemini API.
    
    Args:
        audio_file: Path to the audio file.
        language_code: Language code for transcription.
        output_dir: Directory to save the transcript.
        skip_transcription: Whether to skip transcription.
    
    Returns:
        Path to the transcript file, or None if transcription was skipped or failed.
    """
    if skip_transcription:
        logger.info("Skipping audio transcription")
        return None
    
    logger.info(f"Transcribing audio file: {audio_file}")
    
    try:
        # Create output file path
        if output_dir:
            audio_filename = Path(audio_file).name
            base_name = Path(audio_filename).stem
            transcript_file = Path(output_dir) / f"{base_name}.txt"
        else:
            transcript_file = Path(audio_file).with_suffix(".txt")
        
        # Transcribe the audio
        transcript_path = transcribe_audio_file(
            audio_file=audio_file,
            output_file=str(transcript_file),
            language_code=language_code,
        )
        
        logger.info(f"Transcription complete. Saved to: {transcript_path}")
        return transcript_path
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None

def summarize_text(
    transcript_file: str,
    output_dir: Optional[str] = None,
    skip_summarization: bool = False,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Summarize a transcript to generate podcast title and description.
    
    Args:
        transcript_file: Path to the transcript file.
        output_dir: Directory to save the summary.
        skip_summarization: Whether to skip summarization.
    
    Returns:
        Tuple containing the podcast title, description, and path to the summary file,
        or (None, None, None) if summarization was skipped or failed.
    """
    if skip_summarization:
        logger.info("Skipping transcript summarization")
        return None, None, None
    
    if not transcript_file or not os.path.exists(transcript_file):
        logger.error(f"Transcript file not found: {transcript_file}")
        return None, None, None
    
    logger.info(f"Summarizing transcript: {transcript_file}")
    
    try:
        # Create output file path
        if output_dir:
            transcript_filename = Path(transcript_file).name
            base_name = Path(transcript_filename).stem
            summary_file = Path(output_dir) / f"{base_name}.summary.md"
        else:
            summary_file = Path(transcript_file).with_suffix(".summary.md")
        
        # Summarize the transcript
        title, description, summary_path = summarize_transcript(
            transcript_file=transcript_file,
            output_file=str(summary_file),
        )
        
        logger.info(f"Summarization complete. Title: {title}")
        logger.info(f"Summary saved to: {summary_path}")
        
        return title, description, summary_path
    
    except Exception as e:
        logger.error(f"Error summarizing transcript: {e}")
        return None, None, None

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
        
        # Create output directory if specified
        output_dir = args.output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Check if we need to concatenate multiple WAV files
        input_audio_file = audio_files[0]
        if len(audio_files) > 1 and all(Path(f).suffix.lower() == '.wav' for f in audio_files):
            logger.info(f"Detected multiple WAV files, concatenating {len(audio_files)} files...")
            try:
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
        
        # Process audio with Auphonic
        processed_files = process_audio(
            audio_file=input_audio_file,
            preset_uuid=args.preset_uuid,
            preset_name=args.preset_name,
            output_dir=output_dir,
            skip_conversion=args.skip_conversion,
        )
        
        # Use the first processed file for transcription
        audio_for_transcription = processed_files[0] if processed_files else input_audio_file
        
        # Transcribe audio
        transcript_file = transcribe_audio(
            audio_file=audio_for_transcription,
            language_code=args.language,
            output_dir=output_dir,
            skip_transcription=args.skip_transcription,
        )
        
        # Summarize transcript
        title, description, summary_file = summarize_text(
            transcript_file=transcript_file,
            output_dir=output_dir,
            skip_summarization=args.skip_summarization,
        )
        
        # Print summary of results
        logger.info("\n" + "=" * 50)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 50)
        
        if processed_files and not args.skip_conversion:
            logger.info(f"Processed audio files: {', '.join(processed_files)}")
        
        if transcript_file and not args.skip_transcription:
            logger.info(f"Transcript file: {transcript_file}")
        
        if title and description and not args.skip_summarization:
            logger.info(f"Podcast title: {title}")
            logger.info(f"Summary file: {summary_file}")
        
        # Print API usage costs
        logger.info("\n" + "=" * 50)
        logger.info(cost_tracker.format_cost_summary())
        logger.info("=" * 50)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
