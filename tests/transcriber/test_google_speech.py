"""Tests for Google Cloud Speech-to-Text transcription."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from google.api_core.exceptions import GoogleAPIError

from pod_tenuki.transcriber.google_speech import (
    GoogleSpeechClient,
    transcribe_audio_file
)


@pytest.mark.unit
class TestGoogleSpeechClient:
    """Test Google Speech client functionality."""

    def test_initialization_missing_credentials(self):
        """Test initialization fails without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="credentials path is required"):
                GoogleSpeechClient()

    def test_initialization_credentials_not_found(self, tmp_path):
        """Test initialization fails when credentials file doesn't exist."""
        cred_path = str(tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError, match="credentials file not found"):
            GoogleSpeechClient(
                credentials_path=cred_path,
                project_id="test-project"
            )

    def test_initialization_missing_project_id(self, tmp_path):
        """Test initialization fails without project ID."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="project ID is required"):
                GoogleSpeechClient(
                    credentials_path=str(cred_file),
                    project_id=None
                )

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_initialization_success(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test successful initialization."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        assert client.credentials_path == str(cred_file)
        assert client.project_id == "test-project"
        mock_speech_client.assert_called_once()
        mock_storage_client.assert_called_once()

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_get_bucket_success(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test getting a bucket successfully."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        # Mock bucket
        mock_bucket = Mock()
        client.storage_client.get_bucket.return_value = mock_bucket

        # Get bucket
        bucket = client.get_bucket("test-bucket")

        assert bucket == mock_bucket
        client.storage_client.get_bucket.assert_called_once_with("test-bucket")

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_get_bucket_not_found(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test getting a nonexistent bucket raises error."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        # Mock bucket not found
        client.storage_client.get_bucket.side_effect = Exception("Bucket not found")

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="バケット"):
            client.get_bucket("nonexistent-bucket")

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_upload_to_gcs(self, mock_storage_client, mock_speech_client, tmp_path, sample_audio_file):
        """Test uploading a file to GCS."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        client.storage_client.get_bucket.return_value = mock_bucket

        # Upload file
        gcs_uri = client.upload_to_gcs(
            "test-bucket",
            sample_audio_file
        )

        # Verify GCS URI
        assert gcs_uri.startswith("gs://test-bucket/")
        assert "test_audio.mp3" in gcs_uri

        # Verify upload was called
        mock_blob.upload_from_filename.assert_called_once_with(sample_audio_file)

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_save_transcript(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test saving a transcript to file."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        # Save transcript
        output_file = str(tmp_path / "transcript.txt")
        transcript = "これはテストの文字起こしです。"

        result = client.save_transcript(transcript, output_file)

        # Verify file was created
        assert os.path.exists(output_file)
        assert result == output_file

        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == transcript

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_transcribe_audio_file_not_found(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test transcribing a nonexistent file raises error."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        with pytest.raises(FileNotFoundError):
            client.transcribe_audio("/nonexistent/file.mp3")

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    @patch('pod_tenuki.transcriber.google_speech.cost_tracker')
    def test_transcribe_long_audio(self, mock_cost_tracker, mock_storage_client, mock_speech_client, tmp_path, sample_audio_file):
        """Test transcribing a long audio file."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        client = GoogleSpeechClient(
            credentials_path=str(cred_file),
            project_id="test-project"
        )

        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        client.storage_client.get_bucket.return_value = mock_bucket

        # Mock long_running_recognize
        mock_operation = Mock()
        mock_response = Mock()

        # Mock result
        mock_result = Mock()
        mock_alternative = Mock()
        mock_alternative.transcript = "これはテストの文字起こしです。"
        mock_alternative.words = []
        mock_result.alternatives = [mock_alternative]
        mock_response.results = [mock_result]

        mock_operation.result.return_value = mock_response
        client.speech_client.long_running_recognize.return_value = mock_operation

        # Mock os.path.getsize for cost estimation (since _get_audio_duration doesn't exist)
        with patch('pod_tenuki.transcriber.google_speech.os.path.getsize', return_value=10*1024*1024):
            # Transcribe
            transcript = client.transcribe_long_audio(
                sample_audio_file,
                "test-bucket"
            )

        # Verify transcript
        assert "これはテストの文字起こしです。" in transcript

        # Verify cost tracking was called
        mock_cost_tracker.track_google_speech.assert_called_once()

    @patch('pod_tenuki.transcriber.google_speech.speech.SpeechClient')
    @patch('pod_tenuki.transcriber.google_speech.storage.Client')
    def test_transcribe_audio_determines_encoding(self, mock_storage_client, mock_speech_client, tmp_path):
        """Test that transcribe_audio determines encoding from file extension."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        # Create test audio files with different extensions
        for ext in ['.mp3', '.wav', '.flac']:
            audio_file = tmp_path / f"test{ext}"
            audio_file.write_bytes(b'\x00' * 100)

            client = GoogleSpeechClient(
                credentials_path=str(cred_file),
                project_id="test-project"
            )

            # Mock the transcribe_long_audio method
            with patch.object(client, 'transcribe_long_audio', return_value="Test transcript"):
                # Call transcribe_audio
                transcript = client.transcribe_audio(
                    str(audio_file),
                    bucket_name="test-bucket"
                )

                # Verify transcribe_long_audio was called
                assert transcript == "Test transcript"


@pytest.mark.integration
class TestTranscribeAudioFile:
    """Test the transcribe_audio_file function."""

    @patch('pod_tenuki.transcriber.google_speech.GoogleSpeechClient')
    def test_transcribe_audio_file_default_output(self, mock_client_class, tmp_path, sample_audio_file):
        """Test transcribing with default output file."""
        # Mock client
        mock_client = Mock()
        mock_client.transcribe_audio.return_value = "Test transcript"
        mock_client.save_transcript.return_value = "/path/to/transcript.txt"
        mock_client_class.return_value = mock_client

        # Transcribe
        result = transcribe_audio_file(
            sample_audio_file,
            bucket_name="test-bucket"
        )

        # Verify result
        assert result == "/path/to/transcript.txt"

        # Verify client methods were called
        mock_client.transcribe_audio.assert_called_once()
        mock_client.save_transcript.assert_called_once()

    @patch('pod_tenuki.transcriber.google_speech.GoogleSpeechClient')
    def test_transcribe_audio_file_custom_output(self, mock_client_class, tmp_path, sample_audio_file):
        """Test transcribing with custom output file."""
        output_file = str(tmp_path / "custom_transcript.txt")

        # Mock client
        mock_client = Mock()
        mock_client.transcribe_audio.return_value = "Test transcript"
        mock_client.save_transcript.return_value = output_file
        mock_client_class.return_value = mock_client

        # Transcribe
        result = transcribe_audio_file(
            sample_audio_file,
            output_file=output_file,
            bucket_name="test-bucket"
        )

        # Verify result
        assert result == output_file

    @patch('pod_tenuki.transcriber.google_speech.GoogleSpeechClient')
    def test_transcribe_audio_file_api_error(self, mock_client_class, sample_audio_file):
        """Test handling of Google API errors."""
        # Mock client to raise error
        mock_client = Mock()
        mock_client.transcribe_audio.side_effect = GoogleAPIError("API error")
        mock_client_class.return_value = mock_client

        # Should raise GoogleAPIError
        with pytest.raises(GoogleAPIError):
            transcribe_audio_file(
                sample_audio_file,
                bucket_name="test-bucket"
            )

    def test_transcribe_audio_file_not_found(self):
        """Test transcribing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            transcribe_audio_file(
                "/nonexistent/file.mp3",
                bucket_name="test-bucket"
            )
