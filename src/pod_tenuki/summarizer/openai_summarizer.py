"""
OpenAI API client for text summarization.

This module provides functionality to summarize transcribed text
and generate podcast titles and descriptions using OpenAI's API.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple

from openai import OpenAI

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

        # Initialize OpenAI client with API key
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_summary(
        self,
        text: str,
        max_title_length: int = 100,
        max_description_length: int = 500,
        model: str = "gpt-4o",
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
        max_text_length = 20000  # Approximate limit to stay within token limits
        if len(text) > max_text_length:
            logger.warning(f"Text is too long ({len(text)} chars), truncating to {max_text_length} chars")
            text = text[:max_text_length] + "..."
        
        try:
            logger.info("Generating podcast title and description")
            
            # Create the prompt for the API - Japanese version with humor and bullet points
            prompt = f"""
            以下のテキストはポッドキャストの文字起こしです。このポッドキャストの内容を分析してShow Notesを作成してください。

            以下の点に注意してください：

            - テンプレ的な要約や定型文を避けてください。
            - 人間味のある文体で、話者の雰囲気やテンションを感じ取れるようにしてください。
            - 面白かったポイントやユニークな視点には軽くツッコミやリアクションも入れてください。
            - Markdown形式で、500〜700語程度を目安に。
            - タイトルはキャッチーで、思わずクリックしたくなるようなものに。
            - 「これは嘘しか言わないポッドキャスト IE69なので、全ての話はフィクションであることを留意してお楽しみください。」といった意味を良い感じにまぜこんでください

            ※絶対に「〜であると述べている」「〜が重要である」というような固い表現は避けてください。

            フォーマットですが、Show Notesには以下の要素を含めてください：

            タイトル: ポッドキャストの主要トピックを反映した簡潔なタイトル（最大{max_title_length}文字程度）
            主な話題:

            話者が取り上げた重要なトピックを箇条書きで列挙、絵文字とかつかって装飾してよい
            各トピックの下に関連する詳細ポイントを小見出しとして追加
            技術的な内容や専門用語があれば、それらは正確に反映する

            感想:

            ポッドキャストの内容に対する簡潔な分析や考察（2-3段落程度）
            話者の視点や論点の特徴
            このポッドキャストが聴者にとって持つ可能性のある価値


            --- ここに文字起こしのテキストが挿入されます ---
            {text}
            """
            
            # Call the OpenAI API with higher temperature for more creative output
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "あなたはポッドキャストの専門プロデューサーで、適切なタイトルと要約文を日本語で作成します。内容を正確に把握し、丁寧で簡潔な表現で要約することが得意です。また、コンテンツから重要なトピックを抽出して、わかりやすい箇条書きリストを作成することにも長けています。情報を正確に伝えることを優先し、適切な形式でまとめてください。重要な要件として、要約文の最後は必ず「本人曰く、全ての話はフィクションであることを留意してお楽しみください。」という一文で終えてください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,  # 出力トークン数を大幅に増加
                temperature=0.7,
            )
            
            # Track API usage cost
            cost_tracker.track_openai_usage(response, model)
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            
            # マークダウンの保持のため、単純にタイトルのみを抽出する
            title = ""
            # 応答テキスト全体をそのまま説明文として使用
            description = response_text
            topics = []
            
            # タイトルのみ抽出する簡略化されたロジック
            lines = response_text.split("\n")
            
            # タイトル検出ループ
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # マークダウン形式タイトルの検出
                if line.startswith("# ") and not title:
                    title = line[2:].strip()
                    break
                
                # ### タイトル: 形式の検出（マークダウン見出しとタイトル表記が混合）
                if "###" in line and "タイトル:" in line:
                    parts = line.split("タイトル:", 1)
                    if len(parts) > 1:
                        title = parts[1].strip()
                        break
                
                # 明示的なタイトル指定
                if (line.upper().startswith("TITLE:") or line.startswith("タイトル:")) and not title:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        title = parts[1].strip()
                        break
            
            # タイトルが見つからない場合、最初の行をタイトルとして使用
            if not title and lines:
                for line in lines:
                    if line.strip():
                        title = line.strip()
                        break
                        
            # トピック抽出 (将来の参照用)
            for line in lines:
                if line.strip() and line.startswith("-"):
                    topic = line[1:].strip()
                    if topic and "トピック" not in topic and "必要に応じて" not in topic:
                        topics.append(topic)
            
            # タイトルの長さ制限のみ適用（説明文は制限しない）
            if len(title) > max_title_length:
                title = title[:max_title_length - 3] + "..."
            
            # 説明文の長さ制限は適用しない - OpenAI APIからの応答をそのまま使用
            
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
            # タイトルから不要なマークダウン記号などを削除
            clean_title = title
            # マークダウン見出しの削除 (### や ## など)
            if "###" in clean_title:
                clean_title = clean_title.replace("###", "").strip()
            if "##" in clean_title:
                clean_title = clean_title.replace("##", "").strip()
            if "#" in clean_title:
                clean_title = clean_title.replace("#", "").strip()
                
            # タイトル: プレフィックスの削除
            if "タイトル:" in clean_title:
                clean_title = clean_title.split("タイトル:", 1)[1].strip()
            if "TITLE:" in clean_title.upper():
                clean_title = clean_title.split(":", 1)[1].strip()
                
            # 余分な空白や記号の削除
            clean_title = clean_title.strip(": -_")
            
            # OpenAI APIからの応答をそのまま使用
            # 定型文の処理は行わない - システムプロンプトで既に指示済み
            
            # 最終的なコンテンツの作成 - APIからの出力をそのまま保持する
            with open(output_file, "w", encoding="utf-8") as f:
                # タイトルを付加
                f.write(f"# {clean_title}\n\n")
                
                # 説明文 - GPTが生成したままのマークダウンを保持する
                f.write(description)
                
                # トピックがまだ含まれていない場合のみ追加
                if topics and len(topics) > 0 and "##" not in description:
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
    
    # 長い行を改行で区切って処理しやすいテキストに変換する
    # 特に、非常に長い行（例：改行がない場合）は適切に処理できるよう分割する
    processed_text = ""
    line_length_limit = 1000  # 適切な長さに設定
    
    # 改行で分割して処理
    for line in transcript_text.split('\n'):
        # 行が長すぎる場合は分割して改行を挿入
        if len(line) > line_length_limit:
            # 長い行を適切な長さ（約100文字）で分割
            chunks = [line[i:i+100] for i in range(0, len(line), 100)]
            processed_text += '\n'.join(chunks) + '\n'
        else:
            processed_text += line + '\n'
    
    logger.debug(f"Original text length: {len(transcript_text)}, Processed text length: {len(processed_text)}")
    
    # Initialize the summarizer
    summarizer = OpenAISummarizer(api_key)
    
    # Generate the summary with topics
    title, description, topics = summarizer.generate_summary(
        processed_text,
        max_title_length=max_title_length,
        max_description_length=max_description_length,
    )
    
    # Save the summary with topics
    summary_file = summarizer.save_summary(title, description, output_file, topics)
    
    return title, description, topics, summary_file
