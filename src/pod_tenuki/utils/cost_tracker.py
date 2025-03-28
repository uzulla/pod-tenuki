"""
Cost tracking utilities for pod-tenuki.

This module provides functionality to track and calculate API usage costs
for OpenAI, Gemini, and Google Cloud Speech-to-Text API calls.
"""
import logging
from typing import Dict, Any, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

class CostTracker:
    """Track API usage costs for various services."""
    
    # Approximate cost per 1000 tokens for OpenAI models (in USD)
    OPENAI_COSTS = {
        "gpt-4o": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    }
    
    # Approximate cost per minute for Gemini audio transcription (in USD)
    GEMINI_AUDIO_COST_PER_MINUTE = 0.0025
    
    # Approximate cost per minute for Google Cloud Speech-to-Text (in USD)
    # Standard model: $0.024/分（$0.006/15秒）
    GOOGLE_SPEECH_COST_PER_MINUTE = 0.024
    
    def __init__(self):
        """Initialize the cost tracker."""
        self.reset()
    
    def reset(self):
        """Reset all tracked costs."""
        self.openai_costs = {model: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0} 
                            for model in self.OPENAI_COSTS}
        self.gemini_audio_minutes = 0
        self.gemini_audio_cost = 0.0
        self.google_speech_minutes = 0
        self.google_speech_cost = 0.0
        self.total_cost = 0.0
    
    def track_openai_usage(self, response: Any, model: str = "gpt-4o"):
        """
        Track OpenAI API usage from a response.
        
        Args:
            response: OpenAI API response object
            model: OpenAI model name
        """
        if model not in self.OPENAI_COSTS:
            logger.warning(f"Unknown OpenAI model: {model}, using gpt-4o pricing")
            model = "gpt-4o"
        
        try:
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # Calculate cost
            input_cost = (input_tokens / 1000) * self.OPENAI_COSTS[model]["input"]
            output_cost = (output_tokens / 1000) * self.OPENAI_COSTS[model]["output"]
            total_cost = input_cost + output_cost
            
            # Update tracking
            self.openai_costs[model]["input_tokens"] += input_tokens
            self.openai_costs[model]["output_tokens"] += output_tokens
            self.openai_costs[model]["cost"] += total_cost
            self.total_cost += total_cost
            
            logger.debug(f"OpenAI API usage: {input_tokens} input tokens, {output_tokens} output tokens")
            logger.debug(f"OpenAI API cost: ${total_cost:.4f}")
            
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not track OpenAI usage: {e}")
    
    def track_gemini_audio(self, audio_duration_minutes: float):
        """
        Track Gemini API usage for audio transcription.
        
        Args:
            audio_duration_minutes: Duration of the audio in minutes
        """
        try:
            cost = audio_duration_minutes * self.GEMINI_AUDIO_COST_PER_MINUTE
            
            # Update tracking
            self.gemini_audio_minutes += audio_duration_minutes
            self.gemini_audio_cost += cost
            self.total_cost += cost
            
            logger.debug(f"Gemini API audio usage: {audio_duration_minutes:.2f} minutes")
            logger.debug(f"Gemini API audio cost: ${cost:.4f}")
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not track Gemini audio usage: {e}")
    
    def track_google_speech(self, audio_duration_minutes: float):
        """
        Track Google Cloud Speech-to-Text API usage.
        
        Args:
            audio_duration_minutes: Duration of the audio in minutes
        """
        try:
            cost = audio_duration_minutes * self.GOOGLE_SPEECH_COST_PER_MINUTE
            
            # Update tracking
            self.google_speech_minutes += audio_duration_minutes
            self.google_speech_cost += cost
            self.total_cost += cost
            
            logger.debug(f"Google Speech API usage: {audio_duration_minutes:.2f} minutes")
            logger.debug(f"Google Speech API cost: ${cost:.4f}")
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not track Google Speech usage: {e}")
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tracked costs.
        
        Returns:
            Dictionary with cost summary
        """
        summary = {
            "openai": {
                model: {
                    "input_tokens": self.openai_costs[model]["input_tokens"],
                    "output_tokens": self.openai_costs[model]["output_tokens"],
                    "cost": self.openai_costs[model]["cost"]
                }
                for model in self.OPENAI_COSTS
                if self.openai_costs[model]["input_tokens"] > 0
            },
            "gemini": {
                "audio_minutes": self.gemini_audio_minutes,
                "cost": self.gemini_audio_cost
            },
            "google_speech": {
                "audio_minutes": self.google_speech_minutes,
                "cost": self.google_speech_cost
            },
            "total_cost": self.total_cost
        }
        
        return summary
    
    def format_cost_summary(self) -> str:
        """
        Format the cost summary as a human-readable string.
        
        Returns:
            Formatted cost summary string
        """
        summary = self.get_cost_summary()
        lines = ["API USAGE COSTS:"]
        
        # OpenAI costs
        openai_models = [model for model in summary["openai"] if summary["openai"][model]["input_tokens"] > 0]
        if openai_models:
            lines.append("OpenAI API:")
            for model in openai_models:
                model_data = summary["openai"][model]
                lines.append(f"  - {model}: {model_data['input_tokens']} input tokens, "
                            f"{model_data['output_tokens']} output tokens, "
                            f"${model_data['cost']:.4f}")
        
        # Gemini costs
        if summary["gemini"]["audio_minutes"] > 0:
            lines.append("Gemini API:")
            lines.append(f"  - Audio transcription: {summary['gemini']['audio_minutes']:.2f} minutes, "
                        f"${summary['gemini']['cost']:.4f}")
        
        # Google Speech costs
        if summary["google_speech"]["audio_minutes"] > 0:
            lines.append("Google Cloud Speech-to-Text API:")
            lines.append(f"  - Audio transcription: {summary['google_speech']['audio_minutes']:.2f} minutes, "
                        f"${summary['google_speech']['cost']:.4f}")
        
        # Total cost
        lines.append(f"Total cost: ${summary['total_cost']:.4f}")
        
        return "\n".join(lines)

# Global instance for convenience
cost_tracker = CostTracker()
