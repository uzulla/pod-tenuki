"""Transcriber module for pod-tenuki."""
from pod_tenuki.transcriber.google_speech import (
    GoogleSpeechClient,
    transcribe_audio_file,
)

__all__ = [
    'GoogleSpeechClient',
    'transcribe_audio_file',
]
