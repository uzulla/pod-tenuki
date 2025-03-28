"""Transcriber module for pod-tenuki."""
# Google Cloud Speech-to-Text APIを使用した文字起こし
from pod_tenuki.transcriber.google_speech import (
    GoogleSpeechClient,
    transcribe_audio_file,
)

__all__ = [
    'GoogleSpeechClient',
    'transcribe_audio_file',
]
