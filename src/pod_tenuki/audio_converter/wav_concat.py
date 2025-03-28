"""
Module for concatenating WAV files into a single MP3 file.

This module provides functionality to combine multiple WAV files into a single
MP3 file for further processing.
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional

import ffmpeg

# Set up logger
logger = logging.getLogger(__name__)

def concatenate_wav_files(
    wav_files: List[str],
    output_dir: Optional[str] = None,
    output_name: Optional[str] = None
) -> str:
    """
    Concatenate multiple WAV files into a single MP3 file.
    
    Args:
        wav_files: List of paths to WAV files to concatenate
        output_dir: Directory to save the output file (if None, uses temp directory)
        output_name: Name for the output file (if None, generates a temporary name)
    
    Returns:
        Path to the concatenated MP3 file
    
    Raises:
        ValueError: If no WAV files are provided or if any file doesn't exist
        RuntimeError: If concatenation fails
    """
    if not wav_files:
        raise ValueError("No WAV files provided for concatenation")
    
    # Validate all files exist
    for wav_file in wav_files:
        if not os.path.exists(wav_file):
            raise ValueError(f"WAV file not found: {wav_file}")
    
    # Create output file path
    if output_dir and output_name:
        output_path = Path(output_dir) / output_name
        os.makedirs(output_dir, exist_ok=True)
    elif output_dir:
        # Use first filename as base for output name
        base_name = Path(wav_files[0]).stem
        if len(wav_files) > 1:
            base_name += "_concatenated"
        output_path = Path(output_dir) / f"{base_name}.mp3"
        os.makedirs(output_dir, exist_ok=True)
    elif output_name:
        # Use default output directory with provided name
        default_output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(default_output_dir, exist_ok=True)
        output_path = Path(default_output_dir) / output_name
    else:
        # Use default output directory with generated name
        default_output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(default_output_dir, exist_ok=True)
        base_name = Path(wav_files[0]).stem
        if len(wav_files) > 1:
            base_name += "_concatenated"
        output_path = Path(default_output_dir) / f"{base_name}.mp3"
    
    logger.info(f"Concatenating {len(wav_files)} WAV files into {output_path}")
    
    try:
        # Start with the first file
        input_stream = ffmpeg.input(wav_files[0])
        
        # Add other files
        for wav_file in wav_files[1:]:
            file_stream = ffmpeg.input(wav_file)
            # Concatenate in the audio domain
            input_stream = ffmpeg.concat(input_stream, file_stream, v=0, a=1)
        
        # Output to MP3
        output_stream = ffmpeg.output(input_stream, str(output_path), acodec='libmp3lame', ab='192k')
        
        # Run the FFmpeg command
        ffmpeg.run(output_stream, quiet=True, overwrite_output=True)
        
        logger.info(f"Successfully concatenated files to {output_path}")
        return str(output_path)
    
    except ffmpeg.Error as e:
        error_msg = f"FFmpeg error during concatenation: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error concatenating WAV files: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)