"""Tests for speech-to-text functionality."""

import pytest
import speech_recognition as sr

from app.voice.speech_input import SpeechInput, SpeechInputError


def test_transcribe_returns_clean_text(monkeypatch):
    """Recognized speech should be stripped of extra whitespace."""
    speech_input = SpeechInput()
    audio = sr.AudioData(b"\x00\x00", 16000, 2)

    monkeypatch.setattr(
        speech_input.recognizer,
        "recognize_google",
        lambda audio, language: "  Open WhatsApp  ",
    )

    assert speech_input.transcribe(audio) == "Open WhatsApp"


def test_transcribe_handles_unrecognized_speech(monkeypatch):
    """Unintelligible speech should produce a helpful error."""
    speech_input = SpeechInput()
    audio = sr.AudioData(b"\x00\x00", 16000, 2)

    def raise_unknown_value(audio, language):
        raise sr.UnknownValueError()

    monkeypatch.setattr(
        speech_input.recognizer,
        "recognize_google",
        raise_unknown_value,
    )

    with pytest.raises(SpeechInputError, match="could not be understood"):
        speech_input.transcribe(audio)


def test_transcribe_handles_service_failure(monkeypatch):
    """Recognition service failures should be handled gracefully."""
    speech_input = SpeechInput()
    audio = sr.AudioData(b"\x00\x00", 16000, 2)

    def raise_request_error(audio, language):
        raise sr.RequestError("Service unavailable")

    monkeypatch.setattr(
        speech_input.recognizer,
        "recognize_google",
        raise_request_error,
    )

    with pytest.raises(SpeechInputError, match="internet connection"):
        speech_input.transcribe(audio)
