"""Tests for OpenAI summarization."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from pod_tenuki.summarizer.openai_summarizer import (
    OpenAISummarizer,
    summarize_transcript
)


@pytest.mark.unit
class TestOpenAISummarizer:
    """Test OpenAI summarizer functionality."""

    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                OpenAISummarizer()

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_initialization_success(self, mock_openai_class):
        """Test successful initialization."""
        summarizer = OpenAISummarizer(api_key="test-api-key")

        assert summarizer.api_key == "test-api-key"
        mock_openai_class.assert_called_once_with(api_key="test-api-key")

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_generate_summary_empty_text(self, mock_openai_class):
        """Test generating summary with empty text raises error."""
        summarizer = OpenAISummarizer(api_key="test-api-key")

        with pytest.raises(ValueError, match="cannot be empty"):
            summarizer.generate_summary("")

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    @patch('pod_tenuki.summarizer.openai_summarizer.cost_tracker')
    def test_generate_summary_success(self, mock_cost_tracker, mock_openai_class, mock_openai_response):
        """Test successful summary generation."""
        # Setup mock client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Generate summary
        title, description, topics = summarizer.generate_summary(
            "これはテストテキストです。"
        )

        # Verify results
        assert isinstance(title, str)
        assert len(title) > 0
        assert isinstance(description, str)
        assert len(description) > 0
        assert isinstance(topics, list)

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()

        # Verify cost tracking
        mock_cost_tracker.track_openai_usage.assert_called_once()

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    @patch('pod_tenuki.summarizer.openai_summarizer.cost_tracker')
    def test_generate_summary_truncates_long_text(self, mock_cost_tracker, mock_openai_class, mock_openai_response):
        """Test that long text is truncated."""
        # Setup mock client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Create very long text
        long_text = "テスト " * 10000

        # Generate summary
        title, description, topics = summarizer.generate_summary(long_text)

        # Should succeed without error
        assert isinstance(title, str)
        assert isinstance(description, str)

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    @patch('pod_tenuki.summarizer.openai_summarizer.cost_tracker')
    def test_generate_summary_custom_model(self, mock_cost_tracker, mock_openai_class, mock_openai_response):
        """Test generating summary with custom model."""
        # Setup mock client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Generate summary with custom model
        title, description, topics = summarizer.generate_summary(
            "テストテキスト",
            model="gpt-4"
        )

        # Verify API was called with correct model
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == "gpt-4"

        # Verify cost tracking with correct model
        mock_cost_tracker.track_openai_usage.assert_called_once()
        track_call_args = mock_cost_tracker.track_openai_usage.call_args
        # model is passed as the second positional argument
        assert track_call_args[0][1] == "gpt-4"

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_generate_summary_api_error(self, mock_openai_class):
        """Test handling of OpenAI API errors."""
        # Setup mock client to raise error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai_class.return_value = mock_client

        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Should raise exception
        with pytest.raises(Exception):
            summarizer.generate_summary("テストテキスト")

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_save_summary(self, mock_openai_class, tmp_path):
        """Test saving summary to file."""
        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Save summary
        output_file = str(tmp_path / "summary.md")
        title = "テストタイトル"
        description = "テスト説明文"
        topics = ["トピック1", "トピック2"]

        result = summarizer.save_summary(
            title,
            description,
            output_file,
            topics
        )

        # Verify file was created
        assert os.path.exists(output_file)
        assert result == output_file

        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert title in content
        assert description in content

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_save_summary_cleans_title(self, mock_openai_class, tmp_path):
        """Test that save_summary cleans markdown from title."""
        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Save summary with title containing markdown
        output_file = str(tmp_path / "summary.md")
        title = "### タイトル: テストタイトル"
        description = "テスト説明文"

        result = summarizer.save_summary(
            title,
            description,
            output_file
        )

        # Verify file was created
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Title should be cleaned
        assert "###" not in content.split('\n')[0]
        assert "タイトル:" not in content.split('\n')[0]
        assert "テストタイトル" in content

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAI')
    def test_save_summary_error(self, mock_openai_class, tmp_path):
        """Test handling of save errors."""
        summarizer = OpenAISummarizer(api_key="test-api-key")

        # Try to save to invalid path
        output_file = "/invalid/path/summary.md"

        with pytest.raises(Exception):
            summarizer.save_summary(
                "タイトル",
                "説明文",
                output_file
            )


@pytest.mark.integration
class TestSummarizeTranscript:
    """Test the summarize_transcript function."""

    def test_summarize_transcript_file_not_found(self):
        """Test summarizing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            summarize_transcript("/nonexistent/file.txt")

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAISummarizer')
    def test_summarize_transcript_default_output(self, mock_summarizer_class, sample_transcript):
        """Test summarizing with default output file."""
        # Mock summarizer
        mock_summarizer = Mock()
        mock_summarizer.generate_summary.return_value = (
            "テストタイトル",
            "テスト説明文",
            ["トピック1"]
        )
        mock_summarizer.save_summary.return_value = "/path/to/summary.md"
        mock_summarizer_class.return_value = mock_summarizer

        # Summarize
        title, description, topics, summary_file = summarize_transcript(sample_transcript)

        # Verify results
        assert title == "テストタイトル"
        assert description == "テスト説明文"
        assert topics == ["トピック1"]
        assert summary_file == "/path/to/summary.md"

        # Verify methods were called
        mock_summarizer.generate_summary.assert_called_once()
        mock_summarizer.save_summary.assert_called_once()

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAISummarizer')
    def test_summarize_transcript_custom_output(self, mock_summarizer_class, sample_transcript, tmp_path):
        """Test summarizing with custom output file."""
        output_file = str(tmp_path / "custom_summary.md")

        # Mock summarizer
        mock_summarizer = Mock()
        mock_summarizer.generate_summary.return_value = (
            "テストタイトル",
            "テスト説明文",
            ["トピック1"]
        )
        mock_summarizer.save_summary.return_value = output_file
        mock_summarizer_class.return_value = mock_summarizer

        # Summarize
        title, description, topics, summary_file = summarize_transcript(
            sample_transcript,
            output_file=output_file
        )

        # Verify output file was used
        assert summary_file == output_file

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAISummarizer')
    def test_summarize_transcript_custom_parameters(self, mock_summarizer_class, sample_transcript):
        """Test summarizing with custom parameters."""
        # Mock summarizer
        mock_summarizer = Mock()
        mock_summarizer.generate_summary.return_value = (
            "テストタイトル",
            "テスト説明文",
            ["トピック1"]
        )
        mock_summarizer.save_summary.return_value = "/path/to/summary.md"
        mock_summarizer_class.return_value = mock_summarizer

        # Summarize with custom parameters
        title, description, topics, summary_file = summarize_transcript(
            sample_transcript,
            api_key="custom-api-key",
            max_title_length=50,
            max_description_length=200
        )

        # Verify summarizer was initialized with custom API key
        mock_summarizer_class.assert_called_once_with("custom-api-key")

        # Verify generate_summary was called with custom parameters
        call_args = mock_summarizer.generate_summary.call_args
        assert call_args.kwargs['max_title_length'] == 50
        assert call_args.kwargs['max_description_length'] == 200

    @patch('pod_tenuki.summarizer.openai_summarizer.OpenAISummarizer')
    def test_summarize_transcript_long_lines(self, mock_summarizer_class, tmp_path):
        """Test summarizing transcript with very long lines."""
        # Create transcript with very long line
        transcript_file = tmp_path / "long_transcript.txt"
        long_text = "テスト " * 500  # Create a very long line
        transcript_file.write_text(long_text)

        # Mock summarizer
        mock_summarizer = Mock()
        mock_summarizer.generate_summary.return_value = (
            "テストタイトル",
            "テスト説明文",
            ["トピック1"]
        )
        mock_summarizer.save_summary.return_value = "/path/to/summary.md"
        mock_summarizer_class.return_value = mock_summarizer

        # Summarize
        title, description, topics, summary_file = summarize_transcript(str(transcript_file))

        # Should succeed
        assert title == "テストタイトル"

        # Verify text was processed (split into multiple lines)
        call_args = mock_summarizer.generate_summary.call_args
        processed_text = call_args[0][0]
        assert '\n' in processed_text
