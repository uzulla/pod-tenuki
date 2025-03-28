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
            
            # Create the prompt for the API - Japanese version with humor and bullet points
            prompt = f"""
            以下のテキストはポッドキャストの文字起こしです。このポッドキャストの内容を分析し、Show Notesを作成してください。
            Show Notesには以下の要素を含めてください：

            タイトル: ポッドキャストの主要トピックを反映した簡潔なタイトル（最大{max_title_length}文字）
            主な話題:

            話者が取り上げた重要なトピックを箇条書きで列挙
            各トピックの下に関連する詳細ポイントを小見出しとして追加
            技術的な内容や専門用語があれば、それらを正確に反映する


            感想:

            ポッドキャストの内容に対する簡潔な分析や考察（2-3段落程度）
            話者の視点や論点の特徴
            このポッドキャストが聴者にとって持つ可能性のある価値


            最後に:

            ポッドキャストのタイトルやシリーズ名がわかる場合は、それを記載
            特に「嘘しか言わないポッドキャスト IE69」というタイトルがある場合は記載

            全体的なフォーマットはMarkdown形式で、読みやすく整理してください。専門的なトピックは正確に表現しつつも、一般の聴者にも理解しやすい言葉で要約してください。
            Show Notesの全体の長さは適度に簡潔にし、約500-700単語を目安としてください。
            --- ここに文字起こしのテキストが挿入されます ---
            {text}
            """
            
            # Call the OpenAI API with higher temperature for more creative output
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "あなたはポッドキャストの専門プロデューサーで、適切なタイトルと要約文を日本語で作成します。内容を正確に把握し、丁寧で簡潔な表現で要約することが得意です。また、コンテンツから重要なトピックを抽出して、わかりやすい箇条書きリストを作成することにも長けています。情報を正確に伝えることを優先し、適切な形式でまとめてください。重要な要件として、要約文の最後は必ず「本人曰く、全ての話はフィクションであることを留意してお楽しみください。」という一文で終えてください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.7,
            )
            
            # Track API usage cost
            cost_tracker.track_openai_usage(response, model)
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            
            # Parse the response to extract title, description, and topics
            title = ""
            description = ""
            topics = []
            
            # Parse mode: 0 = looking for title/description, 1 = collecting topics
            parse_mode = 0
            
            for line in response_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("TITLE:"):
                    title = line[6:].strip()
                elif line.startswith("DESCRIPTION:"):
                    description = line[12:].strip()
                elif line.startswith("TOPICS:"):
                    parse_mode = 1  # Switch to topics collection mode
                elif parse_mode == 1 and line.startswith("-"):
                    # Extract topic from list item, removing the leading "- "
                    topic = line[1:].strip()
                    if topic.startswith("[") and topic.endswith("]"):
                        topic = topic[1:-1].strip()  # Remove [] if present
                    if topic and not topic.startswith("トピック") and "必要に応じて" not in topic:
                        topics.append(topic)
            
            # Ensure the title and description are within the specified length limits
            if len(title) > max_title_length:
                title = title[:max_title_length - 3] + "..."
            
            if len(description) > max_description_length:
                description = description[:max_description_length - 3] + "..."
            
            logger.info(f"Generated title: {title}")
            logger.debug(f"Generated description: {description[:50]}...")
            logger.debug(f"Generated {len(topics)} topics")
            
            return title, description, topics
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    def save_summary(
        self,
        title: str,
        description: str,
        output_file: str,
        topics: list = None
    ) -> str:
        """
        Save the generated title, description, and topics to a file.

        Args:
            title: Generated podcast title.
            description: Generated podcast description.
            output_file: Path to save the summary.
            topics: Optional list of topics for the podcast.

        Returns:
            Path to the saved summary file.
        """
        try:
            # 必要な文言とその可能性のある変形
            required_text = "本人曰く、全ての話はフィクションであることを留意してお楽しみください。"
            variations = [
                "本人曰く、全ての話はフィクションであることを留意してお楽しみください。",
                "全ての話はフィクションであることを留意してお楽しみください。",
                "全てフィクションであることを留意してお楽しみください。"
            ]
            
            # まず全ての変形を文章から削除する
            for variation in variations:
                description = description.replace(variation, "")
            
            # 連続した空白を削除して整形
            description = ' '.join(description.split())
            
            # 末尾にピリオドがあるか確認
            if description.endswith("."):
                description = description[:-1] + " " + required_text
            else:
                description = description + " " + required_text
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{description}")
                
                # Add topics if available
                if topics and len(topics) > 0:
                    f.write("\n\n## 今回のトピック\n")
                    for topic in topics:
                        f.write(f"- {topic}\n")
            
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
) -> Tuple[str, str, list, str]:
    """
    Summarize a transcript file and generate a podcast title, description, and topics.

    Args:
        transcript_file: Path to the transcript file.
        output_file: Path to save the summary. If not provided, it will be saved
            in the same directory as the transcript file with a .summary.md extension.
        api_key: OpenAI API key. If not provided, it will be loaded from environment variables.
        max_title_length: Maximum length of the generated title.
        max_description_length: Maximum length of the generated description.

    Returns:
        Tuple containing the podcast title, description, topics list, and path to the saved summary file.
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
    
    # Generate the summary with topics
    title, description, topics = summarizer.generate_summary(
        transcript_text,
        max_title_length=max_title_length,
        max_description_length=max_description_length,
    )
    
    # Save the summary with topics
    summary_file = summarizer.save_summary(title, description, output_file, topics)
    
    return title, description, topics, summary_file
