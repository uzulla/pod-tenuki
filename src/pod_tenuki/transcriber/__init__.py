"""Transcriber module for pod-tenuki."""
# Gemini APIの代わりにGoogle Cloud Speech-to-Textを使用
from pod_tenuki.transcriber.google_speech import (
    GoogleSpeechClient,
    transcribe_audio_file,
)

# 以前の実装も残しておくが、デフォルトではGoogle Speechを使用する
from pod_tenuki.transcriber.gemini_transcriber import (
    GeminiTranscriber,
)

__all__ = [
    'GoogleSpeechClient',
    'GeminiTranscriber',
    'transcribe_audio_file',
]
