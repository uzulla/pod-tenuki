"""Tests for WAV file concatenation."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import ffmpeg

from pod_tenuki.audio_converter.wav_concat import concatenate_wav_files


@pytest.mark.unit
class TestWavConcat:
    """Test WAV file concatenation functionality."""

    def test_concatenate_wav_files_no_files(self):
        """Test concatenating with no files raises ValueError."""
        with pytest.raises(ValueError, match="No WAV files provided"):
            concatenate_wav_files([])

    def test_concatenate_wav_files_nonexistent_file(self):
        """Test concatenating with nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="WAV file not found"):
            concatenate_wav_files(["/nonexistent/file.wav"])

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_single_file(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test concatenating a single WAV file."""
        output_dir = str(temp_dir / "output")

        # Mock ffmpeg chain
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.return_value = None

        # Concatenate
        result = concatenate_wav_files(
            [sample_wav_files[0]],
            output_dir=output_dir
        )

        # Verify result path
        assert result.endswith('.mp3')
        assert output_dir in result

        # Verify ffmpeg was called
        mock_ffmpeg.input.assert_called_once_with(sample_wav_files[0])
        mock_ffmpeg.output.assert_called_once()
        mock_ffmpeg.run.assert_called_once()

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_multiple_files(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test concatenating multiple WAV files."""
        output_dir = str(temp_dir / "output")

        # Mock ffmpeg chain
        mock_input = MagicMock()
        mock_concat = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.concat.return_value = mock_concat
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.return_value = None

        # Concatenate
        result = concatenate_wav_files(
            sample_wav_files,
            output_dir=output_dir
        )

        # Verify result path
        assert result.endswith('.mp3')
        assert output_dir in result
        assert 'concatenated' in result

        # Verify ffmpeg was called multiple times
        assert mock_ffmpeg.input.call_count == len(sample_wav_files)
        assert mock_ffmpeg.concat.call_count == len(sample_wav_files) - 1

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_custom_output_name(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test concatenating with custom output name."""
        output_dir = str(temp_dir / "output")
        output_name = "custom_output.mp3"

        # Mock ffmpeg
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.return_value = None

        # Concatenate
        result = concatenate_wav_files(
            [sample_wav_files[0]],
            output_dir=output_dir,
            output_name=output_name
        )

        # Verify result path contains custom name
        assert output_name in result
        assert output_dir in result

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_default_output_dir(self, mock_ffmpeg, sample_wav_files):
        """Test concatenating with default output directory."""
        # Mock ffmpeg
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.return_value = None

        # Concatenate
        result = concatenate_wav_files([sample_wav_files[0]])

        # Verify result path contains default output directory
        assert 'output' in result

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_ffmpeg_error(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test handling of FFmpeg errors."""
        output_dir = str(temp_dir / "output")

        # Mock ffmpeg to raise error
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output

        # Create a mock FFmpeg error
        error = ffmpeg.Error('ffmpeg', '', b'Mock error')
        mock_ffmpeg.run.side_effect = error
        mock_ffmpeg.Error = ffmpeg.Error

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="FFmpeg error"):
            concatenate_wav_files(
                [sample_wav_files[0]],
                output_dir=output_dir
            )

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_wav_files_general_error(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test handling of general errors."""
        output_dir = str(temp_dir / "output")

        # Mock ffmpeg to raise error
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.side_effect = Exception("General error")

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Error concatenating WAV files"):
            concatenate_wav_files(
                [sample_wav_files[0]],
                output_dir=output_dir
            )

    @patch('pod_tenuki.audio_converter.wav_concat.ffmpeg')
    def test_concatenate_creates_output_directory(self, mock_ffmpeg, sample_wav_files, temp_dir):
        """Test that concatenate_wav_files creates output directory if it doesn't exist."""
        output_dir = str(temp_dir / "new_output_dir")

        # Mock ffmpeg
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_ffmpeg.output.return_value = mock_output
        mock_ffmpeg.run.return_value = None

        # Concatenate
        result = concatenate_wav_files(
            [sample_wav_files[0]],
            output_dir=output_dir
        )

        # Verify output directory was created
        assert os.path.exists(output_dir)
