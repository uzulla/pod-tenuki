"""
Gemini API client for audio transcription.

This module provides functionality to transcribe audio files using Google's Gemini API.
It supports long audio files (up to 9.5 hours) and various audio formats.
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import wave
import contextlib

import google.generativeai as genai
from google.generativeai import types
from pydub import AudioSegment

from pod_tenuki.utils.config import GEMINI_API_KEY
from pod_tenuki.utils.cost_tracker import cost_tracker

# Set up logging
logger = logging.getLogger(__name__)

class GeminiTranscriber:
    """Client for interacting with Gemini API for audio transcription."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini API client.

        Args:
            api_key: Gemini API key. If not provided, it will be loaded from environment variables.
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure the Gemini API client
        genai.configure(api_key=self.api_key)
        
        # Default model for transcription
        self.model_name = "gemini-1.5-flash"
    
    def transcribe_audio(
        self,
        audio_file: str,
        output_file: Optional[str] = None,
        language_code: str = "ja-JP",
    ) -> str:
        """
        Transcribe an audio file using Gemini API.

        Args:
            audio_file: Path to the audio file to transcribe.
            output_file: Path to save the transcription. If not provided, it will be saved
                in the same directory as the audio file with a .txt extension.
            language_code: Language code for transcription.

        Returns:
            Path to the saved transcription file.
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Create default output file if not provided
        if not output_file:
            audio_path = Path(audio_file)
            output_file = str(audio_path.with_suffix(".txt"))
        
        # Get the MIME type based on the file extension
        mime_type = self._get_mime_type(audio_file)
        
        try:
            logger.info(f"Transcribing audio file: {audio_file}")
            
            # Check file size to determine upload method
            file_size = os.path.getsize(audio_file)
            
            # For all files, use inline data
            logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")
            with open(audio_file, "rb") as f:
                audio_bytes = f.read()
            
            # Create prompt for transcription
            prompt = f"Please provide a complete and accurate transcript of this audio file. The language is {language_code.split('-')[0]}."
            
            # Generate content with the audio bytes
            response = genai.generate_content(
                model=self.model_name,
                contents=[
                    prompt,
                    {"mime_type": mime_type, "data": audio_bytes}
                ]
            )
            
            # Extract the transcription from the response
            transcription = response.text
            
            # Save the transcription to the output file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(transcription)
            
            # Track API usage cost
            audio_duration = self._get_audio_duration(audio_file)
            cost_tracker.track_gemini_audio(audio_duration)
            
            logger.info(f"Transcription saved to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get the MIME type based on the file extension.

        Args:
            file_path: Path to the file.

        Returns:
            MIME type string.
        """
        extension = Path(file_path).suffix.lower()
        
        mime_types = {
            ".wav": "audio/wav",
            ".mp3": "audio/mp3",
            ".aiff": "audio/aiff",
            ".aif": "audio/aiff",
            ".aac": "audio/aac",
            ".ogg": "audio/ogg",
            ".oga": "audio/ogg",
            ".flac": "audio/flac",
            ".m4a": "audio/mp4",
            ".mp4": "audio/mp4",
        }
        
        return mime_types.get(extension, "audio/mp3")  # Default to mp3 if unknown
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            audio_file: Path to the audio file.
            
        Returns:
            Duration of the audio in seconds.
        """
        try:
            extension = Path(audio_file).suffix.lower()
            
            # Use wave module for WAV files
            if extension == ".wav":
                with contextlib.closing(wave.open(audio_file, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    duration = frames / float(rate)
                    return duration
            
            # Use pydub for other formats
            else:
                audio = AudioSegment.from_file(audio_file)
                return len(audio) / 1000.0  # pydub duration is in milliseconds
                
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            # Return a default duration estimate based on file size
            # Assuming ~10MB per hour of audio at medium quality
            file_size_bytes = os.path.getsize(audio_file)
            file_size_mb = file_size_bytes / (1024 * 1024)
            estimated_duration_seconds = file_size_mb * 360  # 1 MB ≈ 6 minutes
            logger.warning(f"Using estimated duration based on file size: {estimated_duration_seconds:.2f} seconds")
            return estimated_duration_seconds

def transcribe_audio_file(
    audio_file: str,
    output_file: Optional[str] = None,
    language_code: str = "ja-JP",
    api_key: Optional[str] = None,
) -> str:
    """
    Transcribe an audio file using Gemini API.

    Args:
        audio_file: Path to the audio file to transcribe.
        output_file: Path to save the transcription. If not provided, it will be saved
            in the same directory as the audio file with a .txt extension.
        language_code: Language code for transcription.
        api_key: Gemini API key. If not provided, it will be loaded from environment variables.

    Returns:
        Path to the saved transcription file.
    """
    transcriber = GeminiTranscriber(api_key)
    return transcriber.transcribe_audio(
        audio_file=audio_file,
        output_file=output_file,
        language_code=language_code,
    )
