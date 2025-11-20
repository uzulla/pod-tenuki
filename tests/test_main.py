"""Tests for main CLI functionality."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from argparse import Namespace

from pod_tenuki.main import parse_arguments


@pytest.mark.unit
class TestParseArguments:
    """Test command-line argument parsing."""

    def test_parse_arguments_single_file(self):
        """Test parsing single audio file."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3']):
            args = parse_arguments()

        assert args.audio_files == ['audio.mp3']
        assert args.skip_conversion is False
        assert args.skip_transcription is False
        assert args.skip_summarization is False

    def test_parse_arguments_multiple_files(self):
        """Test parsing multiple audio files."""
        with patch('sys.argv', ['pod-tenuki', 'file1.wav', 'file2.wav', 'file3.wav']):
            args = parse_arguments()

        assert args.audio_files == ['file1.wav', 'file2.wav', 'file3.wav']

    def test_parse_arguments_skip_conversion(self):
        """Test parsing with skip conversion flag."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--skip-conversion']):
            args = parse_arguments()

        assert args.skip_conversion is True

    def test_parse_arguments_skip_transcription(self):
        """Test parsing with skip transcription flag."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--skip-transcription']):
            args = parse_arguments()

        assert args.skip_transcription is True

    def test_parse_arguments_skip_summarization(self):
        """Test parsing with skip summarization flag."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--skip-summarization']):
            args = parse_arguments()

        assert args.skip_summarization is True

    def test_parse_arguments_output_dir(self):
        """Test parsing with output directory."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--output-dir', '/path/to/output']):
            args = parse_arguments()

        assert args.output_dir == '/path/to/output'

    def test_parse_arguments_output_name(self):
        """Test parsing with output name."""
        with patch('sys.argv', ['pod-tenuki', 'file1.wav', 'file2.wav', '--output-name', 'combined.mp3']):
            args = parse_arguments()

        assert args.output_name == 'combined.mp3'

    def test_parse_arguments_language(self):
        """Test parsing with custom language."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--language', 'en-US']):
            args = parse_arguments()

        assert args.language == 'en-US'

    def test_parse_arguments_default_language(self):
        """Test default language is ja-JP."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3']):
            args = parse_arguments()

        assert args.language == 'ja-JP'

    def test_parse_arguments_preset_uuid(self):
        """Test parsing with preset UUID."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--preset-uuid', 'custom-uuid']):
            args = parse_arguments()

        assert args.preset_uuid == 'custom-uuid'

    def test_parse_arguments_preset_name(self):
        """Test parsing with preset name."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--preset-name', 'My Preset']):
            args = parse_arguments()

        assert args.preset_name == 'My Preset'

    def test_parse_arguments_verbose(self):
        """Test parsing with verbose flag."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '--verbose']):
            args = parse_arguments()

        assert args.verbose is True

    def test_parse_arguments_verbose_short(self):
        """Test parsing with verbose short flag."""
        with patch('sys.argv', ['pod-tenuki', 'audio.mp3', '-v']):
            args = parse_arguments()

        assert args.verbose is True

    def test_parse_arguments_all_skip_flags(self):
        """Test parsing with all skip flags."""
        with patch('sys.argv', [
            'pod-tenuki', 'audio.mp3',
            '--skip-conversion',
            '--skip-transcription',
            '--skip-summarization'
        ]):
            args = parse_arguments()

        assert args.skip_conversion is True
        assert args.skip_transcription is True
        assert args.skip_summarization is True


@pytest.mark.integration
class TestMainIntegration:
    """Test main CLI integration."""

    @patch('pod_tenuki.main.validate_config')
    @patch('pod_tenuki.main.process_audio_file')
    @patch('pod_tenuki.main.transcribe_audio_file')
    @patch('pod_tenuki.main.summarize_transcript')
    @patch('pod_tenuki.main.cost_tracker')
    def test_main_full_pipeline(
        self,
        mock_cost_tracker,
        mock_summarize,
        mock_transcribe,
        mock_process_audio,
        mock_validate,
        sample_audio_file,
        tmp_path
    ):
        """Test running the full pipeline."""
        from pod_tenuki import main as main_module

        # Mock outputs
        mock_process_audio.return_value = [str(tmp_path / "converted.mp3")]
        mock_transcribe.return_value = str(tmp_path / "transcript.txt")
        mock_summarize.return_value = (
            "タイトル",
            "説明文",
            ["トピック1"],
            str(tmp_path / "summary.md")
        )

        # Mock arguments
        args = Namespace(
            audio_files=[sample_audio_file],
            preset_uuid="test-uuid",
            preset_name=None,
            output_dir=str(tmp_path),
            output_name=None,
            language="ja-JP",
            skip_conversion=False,
            skip_transcription=False,
            skip_summarization=False,
            verbose=False
        )

        with patch('pod_tenuki.main.parse_arguments', return_value=args):
            # Run main
            result = main_module.main()

        # Verify all steps were called
        mock_validate.assert_called_once()
        mock_process_audio.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_summarize.assert_called_once()

    @patch('pod_tenuki.main.validate_config')
    @patch('pod_tenuki.main.concatenate_wav_files')
    @patch('pod_tenuki.main.transcribe_audio_file')
    @patch('pod_tenuki.main.summarize_transcript')
    @patch('pod_tenuki.main.cost_tracker')
    def test_main_multiple_wav_files(
        self,
        mock_cost_tracker,
        mock_summarize,
        mock_transcribe,
        mock_concat,
        mock_validate,
        sample_wav_files,
        tmp_path
    ):
        """Test processing multiple WAV files."""
        from pod_tenuki import main as main_module

        # Mock outputs
        mock_concat.return_value = str(tmp_path / "concatenated.mp3")
        mock_transcribe.return_value = str(tmp_path / "transcript.txt")
        mock_summarize.return_value = (
            "タイトル",
            "説明文",
            ["トピック1"],
            str(tmp_path / "summary.md")
        )

        # Mock arguments
        args = Namespace(
            audio_files=sample_wav_files,
            preset_uuid="test-uuid",
            preset_name=None,
            output_dir=str(tmp_path),
            output_name=None,
            language="ja-JP",
            skip_conversion=True,
            skip_transcription=False,
            skip_summarization=False,
            verbose=False
        )

        with patch('pod_tenuki.main.parse_arguments', return_value=args):
            # Run main
            result = main_module.main()

        # Verify concatenation was called
        mock_concat.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_summarize.assert_called_once()

    @patch('pod_tenuki.main.validate_config')
    @patch('pod_tenuki.main.process_audio_file')
    @patch('pod_tenuki.main.cost_tracker')
    def test_main_skip_all(
        self,
        mock_cost_tracker,
        mock_process_audio,
        mock_validate,
        sample_audio_file
    ):
        """Test skipping all processing steps."""
        from pod_tenuki import main as main_module

        # Mock arguments
        args = Namespace(
            audio_files=[sample_audio_file],
            preset_uuid="test-uuid",
            preset_name=None,
            output_dir=None,
            output_name=None,
            language="ja-JP",
            skip_conversion=True,
            skip_transcription=True,
            skip_summarization=True,
            verbose=False
        )

        with patch('pod_tenuki.main.parse_arguments', return_value=args):
            # Run main
            result = main_module.main()

        # Verify nothing was processed
        mock_process_audio.assert_not_called()

    @patch('pod_tenuki.main.validate_config')
    def test_main_validation_error(self, mock_validate):
        """Test handling of configuration validation errors."""
        from pod_tenuki import main as main_module

        # Mock validation error
        mock_validate.side_effect = ValueError("Missing config")

        # Mock arguments
        args = Namespace(
            audio_files=["audio.mp3"],
            preset_uuid="test-uuid",
            preset_name=None,
            output_dir=None,
            output_name=None,
            language="ja-JP",
            skip_conversion=False,
            skip_transcription=False,
            skip_summarization=False,
            verbose=False
        )

        with patch('pod_tenuki.main.parse_arguments', return_value=args):
            # Should exit with error
            with pytest.raises(SystemExit):
                main_module.main()
