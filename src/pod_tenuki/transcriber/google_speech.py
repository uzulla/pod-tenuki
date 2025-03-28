"""
Google Cloud Speech-to-Text client for audio transcription.

This module provides functionality to transcribe audio files using
Google Cloud Speech-to-Text API, with support for long audio files.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from google.cloud import speech
from google.cloud import storage
from google.cloud.speech import RecognitionConfig, RecognitionAudio
from google.api_core.exceptions import GoogleAPIError

from pod_tenuki.utils.config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT, GOOGLE_STORAGE_BUCKET
from pod_tenuki.utils.cost_tracker import cost_tracker

# Set up logging
logger = logging.getLogger(__name__)

class GoogleSpeechClient:
    """Client for interacting with Google Cloud Speech-to-Text API."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        Initialize the Google Cloud Speech-to-Text client.

        Args:
            credentials_path: Path to the Google Cloud credentials JSON file.
                If not provided, it will be loaded from environment variables.
            project_id: Google Cloud project ID.
                If not provided, it will be loaded from environment variables.
        """
        self.credentials_path = credentials_path or GOOGLE_APPLICATION_CREDENTIALS
        self.project_id = project_id or GOOGLE_CLOUD_PROJECT
        
        if not self.credentials_path:
            raise ValueError("Google Cloud credentials path is required")
        
        if not Path(self.credentials_path).exists():
            raise FileNotFoundError(f"Google Cloud credentials file not found: {self.credentials_path}")
        
        if not self.project_id:
            raise ValueError("Google Cloud project ID is required")
        
        # Set environment variable for credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        
        # Initialize clients
        self.speech_client = speech.SpeechClient()
        self.storage_client = storage.Client()
    
    def create_bucket_if_not_exists(self, bucket_name: str) -> storage.Bucket:
        """
        Create a Google Cloud Storage bucket if it doesn't exist.

        Args:
            bucket_name: Name of the bucket to create.

        Returns:
            Bucket object.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            logger.info(f"Bucket {bucket_name} already exists")
        except Exception:
            bucket = self.storage_client.create_bucket(bucket_name)
            logger.info(f"Bucket {bucket_name} created")
        
        return bucket
    
    def upload_to_gcs(self, bucket_name: str, source_file_path: str, destination_blob_name: Optional[str] = None) -> str:
        """
        Upload a file to Google Cloud Storage.

        Args:
            bucket_name: Name of the bucket to upload to.
            source_file_path: Path to the file to upload.
            destination_blob_name: Name to give the uploaded file in GCS.
                If not provided, the basename of the source file will be used.

        Returns:
            GCS URI of the uploaded file (gs://bucket-name/blob-name).
        """
        if not destination_blob_name:
            destination_blob_name = Path(source_file_path).name
        
        bucket = self.create_bucket_if_not_exists(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        logger.info(f"Uploading {source_file_path} to gs://{bucket_name}/{destination_blob_name}")
        blob.upload_from_filename(source_file_path)
        
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
        logger.info(f"File uploaded to {gcs_uri}")
        
        return gcs_uri
    
    def transcribe_short_audio(
        self,
        audio_file: str,
        language_code: str = "en-US",
        sample_rate_hertz: int = 16000,
        encoding: speech.RecognitionConfig.AudioEncoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
    ) -> str:
        """
        Transcribe a short audio file (less than 60 seconds).

        Args:
            audio_file: Path to the audio file.
            language_code: Language code for transcription.
            sample_rate_hertz: Sample rate of the audio.
            encoding: Audio encoding type.

        Returns:
            Transcribed text.
        """
        with open(audio_file, "rb") as audio_file_obj:
            content = audio_file_obj.read()
        
        audio = RecognitionAudio(content=content)
        config = RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )
        
        logger.info(f"Transcribing short audio file: {audio_file}")
        response = self.speech_client.recognize(config=config, audio=audio)
        
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        return transcript
    
    def transcribe_long_audio(
        self,
        audio_file: str,
        bucket_name: str,
        language_code: str = "en-US",
        sample_rate_hertz: int = 16000,
        encoding: speech.RecognitionConfig.AudioEncoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
        timeout: int = 1800,  # デフォルトの待機時間を30分に延長（長い音声対応）
    ) -> str:
        """
        Transcribe a long audio file (more than 60 seconds) using asynchronous recognition.

        Args:
            audio_file: Path to the audio file.
            bucket_name: Name of the GCS bucket to use for temporary storage.
            language_code: Language code for transcription.
            sample_rate_hertz: Sample rate of the audio.
            encoding: Audio encoding type.
            timeout: Timeout in seconds for the operation.

        Returns:
            Transcribed text.
        """
        # Upload the audio file to GCS
        gcs_uri = self.upload_to_gcs(bucket_name, audio_file)
        
        # Configure the request
        audio = RecognitionAudio(uri=gcs_uri)
        config = RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            # 長時間の音声に対する追加設定
            enable_speaker_diarization=True,  # 話者の分離
            diarization_speaker_count=2,      # 最小の話者数（調整可能）
            use_enhanced=True,                # 強化音声モデルを使用
            model="video",                    # ポッドキャスト/ビデオ向けモデル
            max_alternatives=1,               # 必要に応じて複数の代替文字起こしを取得可能
        )
        
        # Start the long-running operation
        logger.info(f"Starting long-running transcription for {audio_file}")
        operation = self.speech_client.long_running_recognize(config=config, audio=audio)
        
        # Wait for the operation to complete
        logger.info("Waiting for transcription to complete...")
        response = operation.result(timeout=timeout)
        
        # Combine the transcripts with speaker tags (if available)
        transcript = ""
        word_time_data = []
        
        for i, result in enumerate(response.results):
            if result.alternatives:
                alt = result.alternatives[0]
                
                # Check if this result has speaker_tag information
                if hasattr(result, 'alternatives') and hasattr(alt, 'words') and len(alt.words) > 0 and hasattr(alt.words[0], 'speaker_tag'):
                    # Group words by speaker
                    current_speaker = None
                    current_text = ""
                    
                    for word_info in alt.words:
                        if current_speaker is None:
                            current_speaker = word_info.speaker_tag
                        
                        if word_info.speaker_tag != current_speaker:
                            # Speaker changed, add the completed utterance to the transcript
                            transcript += f"\n\nSpeaker {current_speaker}: {current_text.strip()}"
                            current_text = ""
                            current_speaker = word_info.speaker_tag
                        
                        current_text += f" {word_info.word}"
                        
                        # Save word timing information
                        if hasattr(word_info, 'start_time') and hasattr(word_info, 'end_time'):
                            start_seconds = word_info.start_time.total_seconds()
                            end_seconds = word_info.end_time.total_seconds()
                            word_time_data.append({
                                'word': word_info.word,
                                'start_time': start_seconds,
                                'end_time': end_seconds,
                                'speaker': word_info.speaker_tag
                            })
                    
                    # Add the last utterance
                    if current_text:
                        transcript += f"\n\nSpeaker {current_speaker}: {current_text.strip()}"
                
                else:
                    # No speaker information, just add the transcript
                    transcript += alt.transcript + " "
                    
                    # Try to get word timing if available
                    if hasattr(alt, 'words'):
                        for word_info in alt.words:
                            if hasattr(word_info, 'start_time') and hasattr(word_info, 'end_time'):
                                start_seconds = word_info.start_time.total_seconds()
                                end_seconds = word_info.end_time.total_seconds()
                                word_time_data.append({
                                    'word': word_info.word,
                                    'start_time': start_seconds,
                                    'end_time': end_seconds
                                })
        
        # Get audio duration for cost tracking
        try:
            audio_duration_seconds = self._get_audio_duration(audio_file)
            audio_duration_minutes = audio_duration_seconds / 60
            
            # Track the cost (standard model)
            cost_tracker.track_google_speech(audio_duration_minutes)
            
            logger.info(f"Audio duration: {audio_duration_minutes:.2f} minutes")
        except Exception as e:
            logger.warning(f"Could not track cost: {e}")
        
        return transcript.strip()
    
    def transcribe_audio(
        self,
        audio_file: str,
        bucket_name: Optional[str] = None,
        language_code: str = "en-US",
        sample_rate_hertz: int = 16000,
        encoding: Optional[speech.RecognitionConfig.AudioEncoding] = None,
        timeout: int = 600,
    ) -> str:
        """
        Transcribe an audio file, automatically choosing between short and long audio methods.

        Args:
            audio_file: Path to the audio file.
            bucket_name: Name of the GCS bucket to use for temporary storage.
                Required for long audio files.
            language_code: Language code for transcription.
            sample_rate_hertz: Sample rate of the audio.
            encoding: Audio encoding type. If not provided, it will be determined from the file extension.
            timeout: Timeout in seconds for long-running operations.

        Returns:
            Transcribed text.
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Determine file size - すべてのオーディオを非同期（long_audio）として処理
        file_size = os.path.getsize(audio_file)
        logger.info(f"Audio file size: {file_size / (1024 * 1024):.2f} MB")
        # ポッドキャスト用途では常に非同期APIを使用するため、常にTrueに設定
        is_long_audio = True  # すべての音声ファイルを長時間音声として処理
        
        # Determine encoding if not provided
        if not encoding:
            file_ext = Path(audio_file).suffix.lower()
            if file_ext in ['.wav', '.wave']:
                encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            elif file_ext in ['.mp3']:
                encoding = speech.RecognitionConfig.AudioEncoding.MP3
            elif file_ext in ['.flac']:
                encoding = speech.RecognitionConfig.AudioEncoding.FLAC
            else:
                # Default to MP3 for other formats
                encoding = speech.RecognitionConfig.AudioEncoding.MP3
        
        if is_long_audio:
            if not bucket_name:
                bucket_name = f"{self.project_id}-speech-to-text"
            
            return self.transcribe_long_audio(
                audio_file=audio_file,
                bucket_name=bucket_name,
                language_code=language_code,
                sample_rate_hertz=sample_rate_hertz,
                encoding=encoding,
                timeout=timeout,
            )
        else:
            return self.transcribe_short_audio(
                audio_file=audio_file,
                language_code=language_code,
                sample_rate_hertz=sample_rate_hertz,
                encoding=encoding,
            )
    
    def save_transcript(self, transcript: str, output_file: str) -> str:
        """
        Save a transcript to a file.

        Args:
            transcript: Transcribed text.
            output_file: Path to save the transcript.

        Returns:
            Path to the saved transcript file.
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        logger.info(f"Transcript saved to {output_file}")
        
        return output_file

def transcribe_audio_file(
    audio_file: str,
    output_file: Optional[str] = None,
    bucket_name: Optional[str] = None,
    language_code: str = "ja-JP",  # デフォルトを日本語に変更
    credentials_path: Optional[str] = None,
    project_id: Optional[str] = None,
    timeout: int = 1800,  # デフォルトタイムアウトを30分に延長
) -> str:
    """
    Transcribe an audio file using Google Cloud Speech-to-Text.

    Args:
        audio_file: Path to the audio file.
        output_file: Path to save the transcript. If not provided, it will be saved
            in the same directory as the audio file with a .txt extension.
        bucket_name: Name of the GCS bucket to use for temporary storage.
            Required for long audio files.
        language_code: Language code for transcription.
        credentials_path: Path to the Google Cloud credentials JSON file.
            If not provided, it will be loaded from environment variables.
        project_id: Google Cloud project ID.
            If not provided, it will be loaded from environment variables.
        timeout: Timeout in seconds for long-running operations.

    Returns:
        Path to the saved transcript file.
    """
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    # Create default output file if not provided
    if not output_file:
        audio_path = Path(audio_file)
        output_file = str(audio_path.with_suffix(".txt"))
    
    # Initialize client
    client = GoogleSpeechClient(credentials_path, project_id)
    
    try:
        # Transcribe the audio
        transcript = client.transcribe_audio(
            audio_file=audio_file,
            bucket_name=bucket_name,
            language_code=language_code,
            timeout=timeout,
        )
        
        # Save the transcript
        return client.save_transcript(transcript, output_file)
    
    except GoogleAPIError as e:
        logger.error(f"Google API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise
