"""Pytest configuration and fixtures."""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file for testing."""
    audio_file = temp_dir / "test_audio.mp3"
    # Create a minimal MP3 file (just for testing file operations)
    audio_file.write_bytes(b'\xff\xfb\x90\x00' * 100)
    return str(audio_file)


@pytest.fixture
def sample_wav_files(temp_dir):
    """Create sample WAV files for testing."""
    wav_files = []
    for i in range(3):
        wav_file = temp_dir / f"test_{i}.wav"
        # Create a minimal WAV file header
        wav_file.write_bytes(
            b'RIFF' + (100).to_bytes(4, 'little') + b'WAVEfmt ' +
            (16).to_bytes(4, 'little') + b'\x01\x00\x01\x00' +
            (44100).to_bytes(4, 'little') + b'\x00' * 100
        )
        wav_files.append(str(wav_file))
    return wav_files


@pytest.fixture
def sample_transcript(temp_dir):
    """Create a sample transcript file for testing."""
    transcript_file = temp_dir / "test_transcript.txt"
    transcript_file.write_text(
        "これはテスト用の文字起こしです。ポッドキャストの内容をテストするために使用されます。"
        "様々なトピックについて話しています。技術的な話題や日常的な話題も含まれます。"
    )
    return str(transcript_file)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        'AUPHONIC_API_KEY': 'test_auphonic_key',
        'OPENAI_API_KEY': 'test_openai_key',
        'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/credentials.json',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_STORAGE_BUCKET': 'test-bucket',
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = """# テストポッドキャストのタイトル

## 主な話題
- トピック1: 技術的な話題
- トピック2: 日常的な話題

## 感想
これは面白いポッドキャストでした。

本人曰く、全ての話はフィクションであることを留意してお楽しみください。"""
    response.usage = Mock()
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 50
    return response


@pytest.fixture
def mock_google_speech_response():
    """Mock Google Speech API response."""
    response = Mock()
    result = Mock()
    alternative = Mock()
    alternative.transcript = "これはテストの文字起こしです。"
    alternative.words = []
    result.alternatives = [alternative]
    response.results = [result]
    return response


@pytest.fixture
def mock_auphonic_production():
    """Mock Auphonic production response."""
    return {
        'uuid': 'test-uuid-123',
        'status': 'Done',
        'output_files': [
            {
                'format': 'mp3',
                'ending': 'mp3',
                'download_url': 'https://example.com/test.mp3',
                'size': 1024000
            }
        ]
    }
