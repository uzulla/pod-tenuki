"""
OpenAI API client for text summarization.

This module provides functionality to summarize transcribed text
and generate podcast titles and descriptions using OpenAI's API.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple

import openai

from pod_tenuki.utils.config import OPENAI_API_KEY
from pod_tenuki.utils.cost_tracker import cost_tracker

# Set up logging
logger = logging.getLogger(__name__)

class OpenAISummarizer:
    """Client for interacting with OpenAI API for text summarization."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI API client.

        Args:
            api_key: OpenAI API key. If not provided, it will be loaded from environment variables.
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Set API key for the client
        openai.api_key = self.api_key
    
    def generate_summary(
        self,
        text: str,
        max_title_length: int = 100,
        max_description_length: int = 500,
        model: str = "gpt-3.5-turbo",
    ) -> Tuple[str, str]:
        """
        Generate a podcast title and description from transcribed text.

        Args:
            text: Transcribed text to summarize.
            max_title_length: Maximum length of the generated title.
            max_description_length: Maximum length of the generated description.
            model: OpenAI model to use for summarization.

        Returns:
            Tuple containing the podcast title and description.
        """
        if not text:
            raise ValueError("Text to summarize cannot be empty")
        
        # Truncate text if it's too long (OpenAI has token limits)
        max_text_length = 15000  # Approximate limit to stay within token limits
        if len(text) > max_text_length:
            logger.warning(f"Text is too long ({len(text)} chars), truncating to {max_text_length} chars")
            text = text[:max_text_length] + "..."
        
        try:
            logger.info("Generating podcast title and description")
            
            # Create the prompt for the API
            prompt = f"""
            You are an expert podcast producer. Your task is to create a compelling title and description for a podcast based on its transcript.
            
            Here is the transcript:
            {text}
            
            Please provide:
            1. A catchy and informative title (maximum {max_title_length} characters)
            2. An engaging description that summarizes the key points (maximum {max_description_length} characters)
            
            Format your response as:
            TITLE: [Your title here]
            DESCRIPTION: [Your description here]
            """
            
            # Call the OpenAI API
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert podcast producer who creates compelling titles and descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.7,
            )
            
            # Track API usage cost
            cost_tracker.track_openai_usage(response, model)
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            
            # Parse the response to extract title and description
            title = ""
            description = ""
            
            for line in response_text.split("\n"):
                line = line.strip()
                if line.startswith("TITLE:"):
                    title = line[6:].strip()
                elif line.startswith("DESCRIPTION:"):
                    description = line[12:].strip()
            
            # Ensure the title and description are within the specified length limits
            if len(title) > max_title_length:
                title = title[:max_title_length - 3] + "..."
            
            if len(description) > max_description_length:
                description = description[:max_description_length - 3] + "..."
            
            logger.info(f"Generated title: {title}")
            logger.debug(f"Generated description: {description[:50]}...")
            
            return title, description
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    def save_summary(
        self,
        title: str,
        description: str,
        output_file: str
    ) -> str:
        """
        Save the generated title and description to a file.

        Args:
            title: Generated podcast title.
            description: Generated podcast description.
            output_file: Path to save the summary.

        Returns:
            Path to the saved summary file.
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{description}")
            
            logger.info(f"Summary saved to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise

def summarize_transcript(
    transcript_file: str,
    output_file: Optional[str] = None,
    api_key: Optional[str] = None,
    max_title_length: int = 100,
    max_description_length: int = 500,
) -> Tuple[str, str, str]:
    """
    Summarize a transcript file and generate a podcast title and description.

    Args:
        transcript_file: Path to the transcript file.
        output_file: Path to save the summary. If not provided, it will be saved
            in the same directory as the transcript file with a .summary.md extension.
        api_key: OpenAI API key. If not provided, it will be loaded from environment variables.
        max_title_length: Maximum length of the generated title.
        max_description_length: Maximum length of the generated description.

    Returns:
        Tuple containing the podcast title, description, and path to the saved summary file.
    """
    if not os.path.exists(transcript_file):
        raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
    
    # Create default output file if not provided
    if not output_file:
        transcript_path = os.path.abspath(transcript_file)
        base_path = os.path.splitext(transcript_path)[0]
        output_file = f"{base_path}.summary.md"
    
    # Read the transcript
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()
    
    # Initialize the summarizer
    summarizer = OpenAISummarizer(api_key)
    
    # Generate the summary
    title, description = summarizer.generate_summary(
        transcript_text,
        max_title_length=max_title_length,
        max_description_length=max_description_length,
    )
    
    # Save the summary
    summary_file = summarizer.save_summary(title, description, output_file)
    
    return title, description, summary_file
