"""Tests for cost tracking utilities."""
import pytest
from unittest.mock import Mock
from pod_tenuki.utils.cost_tracker import CostTracker


@pytest.mark.unit
class TestCostTracker:
    """Test cost tracking functionality."""

    def test_initialization(self):
        """Test CostTracker initialization."""
        tracker = CostTracker()
        assert tracker.total_cost == 0.0
        assert tracker.gemini_audio_minutes == 0
        assert tracker.google_speech_minutes == 0
        assert all(
            tracker.openai_costs[model]["input_tokens"] == 0
            for model in tracker.OPENAI_COSTS
        )

    def test_reset(self):
        """Test resetting the cost tracker."""
        tracker = CostTracker()

        # Add some costs
        tracker.total_cost = 10.0
        tracker.gemini_audio_minutes = 5.0
        tracker.google_speech_minutes = 3.0

        # Reset
        tracker.reset()

        # Verify reset
        assert tracker.total_cost == 0.0
        assert tracker.gemini_audio_minutes == 0
        assert tracker.google_speech_minutes == 0

    def test_track_openai_usage_gpt4o(self):
        """Test tracking OpenAI API usage for GPT-4o."""
        tracker = CostTracker()

        # Mock response
        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 1000
        response.usage.completion_tokens = 500

        # Track usage
        tracker.track_openai_usage(response, model="gpt-4o")

        # Verify tracking
        assert tracker.openai_costs["gpt-4o"]["input_tokens"] == 1000
        assert tracker.openai_costs["gpt-4o"]["output_tokens"] == 500

        # Calculate expected cost
        input_cost = (1000 / 1000) * 0.01  # $0.01
        output_cost = (500 / 1000) * 0.03  # $0.015
        expected_cost = input_cost + output_cost  # $0.025

        assert abs(tracker.openai_costs["gpt-4o"]["cost"] - expected_cost) < 0.0001
        assert abs(tracker.total_cost - expected_cost) < 0.0001

    def test_track_openai_usage_unknown_model(self):
        """Test tracking OpenAI API usage with unknown model defaults to gpt-4o."""
        tracker = CostTracker()

        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 50

        # Track usage with unknown model
        tracker.track_openai_usage(response, model="unknown-model")

        # Should default to gpt-4o pricing
        assert tracker.openai_costs["gpt-4o"]["input_tokens"] == 100
        assert tracker.openai_costs["gpt-4o"]["output_tokens"] == 50

    def test_track_openai_usage_invalid_response(self):
        """Test tracking OpenAI usage with invalid response doesn't crash."""
        tracker = CostTracker()

        # Mock invalid response
        response = Mock()
        response.usage = None

        # Should not raise exception
        tracker.track_openai_usage(response, model="gpt-4o")

        # Should not have tracked anything
        assert tracker.total_cost == 0.0

    def test_track_gemini_audio(self):
        """Test tracking Gemini API audio usage."""
        tracker = CostTracker()

        # Track 10 minutes of audio
        tracker.track_gemini_audio(10.0)

        # Verify tracking
        assert tracker.gemini_audio_minutes == 10.0
        expected_cost = 10.0 * tracker.GEMINI_AUDIO_COST_PER_MINUTE
        assert abs(tracker.gemini_audio_cost - expected_cost) < 0.0001
        assert abs(tracker.total_cost - expected_cost) < 0.0001

    def test_track_google_speech(self):
        """Test tracking Google Speech API usage."""
        tracker = CostTracker()

        # Track 5 minutes of audio
        tracker.track_google_speech(5.0)

        # Verify tracking
        assert tracker.google_speech_minutes == 5.0
        expected_cost = 5.0 * tracker.GOOGLE_SPEECH_COST_PER_MINUTE
        assert abs(tracker.google_speech_cost - expected_cost) < 0.0001
        assert abs(tracker.total_cost - expected_cost) < 0.0001

    def test_multiple_api_tracking(self):
        """Test tracking multiple API usages."""
        tracker = CostTracker()

        # Track OpenAI
        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 1000
        response.usage.completion_tokens = 500
        tracker.track_openai_usage(response, model="gpt-4o")

        # Track Gemini
        tracker.track_gemini_audio(10.0)

        # Track Google Speech
        tracker.track_google_speech(5.0)

        # Calculate expected total cost
        openai_cost = (1000 / 1000) * 0.01 + (500 / 1000) * 0.03
        gemini_cost = 10.0 * tracker.GEMINI_AUDIO_COST_PER_MINUTE
        google_cost = 5.0 * tracker.GOOGLE_SPEECH_COST_PER_MINUTE
        expected_total = openai_cost + gemini_cost + google_cost

        assert abs(tracker.total_cost - expected_total) < 0.0001

    def test_get_cost_summary(self):
        """Test getting cost summary."""
        tracker = CostTracker()

        # Add some usage
        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 1000
        response.usage.completion_tokens = 500
        tracker.track_openai_usage(response, model="gpt-4o")
        tracker.track_google_speech(5.0)

        # Get summary
        summary = tracker.get_cost_summary()

        # Verify summary structure
        assert "openai" in summary
        assert "gemini" in summary
        assert "google_speech" in summary
        assert "total_cost" in summary

        # Verify OpenAI data
        assert "gpt-4o" in summary["openai"]
        assert summary["openai"]["gpt-4o"]["input_tokens"] == 1000
        assert summary["openai"]["gpt-4o"]["output_tokens"] == 500

        # Verify Google Speech data
        assert summary["google_speech"]["audio_minutes"] == 5.0

    def test_format_cost_summary(self):
        """Test formatting cost summary as string."""
        tracker = CostTracker()

        # Add some usage
        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 1000
        response.usage.completion_tokens = 500
        tracker.track_openai_usage(response, model="gpt-4o")
        tracker.track_google_speech(5.0)

        # Format summary
        summary_str = tracker.format_cost_summary()

        # Verify formatted string contains expected elements
        assert "API USAGE COSTS:" in summary_str
        assert "OpenAI API:" in summary_str
        assert "gpt-4o" in summary_str
        assert "1000 input tokens" in summary_str
        assert "500 output tokens" in summary_str
        assert "Google Cloud Speech-to-Text API:" in summary_str
        assert "Total cost:" in summary_str

    def test_format_cost_summary_empty(self):
        """Test formatting cost summary when no usage tracked."""
        tracker = CostTracker()

        # Format summary
        summary_str = tracker.format_cost_summary()

        # Should contain header and total
        assert "API USAGE COSTS:" in summary_str
        assert "Total cost: $0.0000" in summary_str
