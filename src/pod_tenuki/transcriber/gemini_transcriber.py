"""
Gemini API client for audio transcription.

This module provides functionality to transcribe audio files using Google's Gemini API.
It supports long audio files (up to 9.5 hours) and various audio formats.
"""
import os
import logging
import tempfile
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import wave
import contextlib

from google import genai

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

        # Initialize the Gemini API client with the new SDK
        self.client = genai.Client(api_key=self.api_key)

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

            # Generate content with the audio bytes using the new SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"text": prompt},
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
            error_message = f"Error transcribing audio: {e}"
            
            # 詳細なエラー情報を出力（特にGoogle APIからのエラーの場合）
            if hasattr(e, 'status_code'):
                error_message += f"\nStatus code: {e.status_code}"
            
            if hasattr(e, 'details'):
                error_message += f"\nDetails: {e.details}"
                
            if hasattr(e, 'message'):
                error_message += f"\nMessage: {e.message}"
                
            # APIレスポンスの生データがあれば出力
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_message += f"\nResponse text: {e.response.text[:1000]}"  # 長すぎる場合は切り詰める
                
            # HTTPヘッダーも取得（認証や制限に関する問題の特定に役立つ）
            if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                error_message += f"\nResponse headers: {dict(e.response.headers)}"

            logger.error(error_message)
            
            # 詳細なエラー情報を含めて例外を再発生
            raise Exception(error_message) from e
    
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
            
            # Use ffprobe for other formats
            else:
                try:
                    # Use ffprobe to get duration
                    cmd = [
                        "ffprobe", 
                        "-v", "error", 
                        "-show_entries", "format=duration", 
                        "-of", "json", 
                        audio_file
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    data = json.loads(result.stdout)
                    duration = float(data["format"]["duration"])
                    return duration
                except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error using ffprobe to get duration: {e}")
                    raise
                
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
