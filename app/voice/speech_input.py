"""Microphone capture and speech-to-text functionality."""

import speech_recognition as sr


class SpeechInputError(Exception):
    """Raised when speech input cannot be captured or transcribed."""


class SpeechInput:
    """Capture a single spoken command and transcribe it."""

    def __init__(
        self,
        language: str = "en-US",
        timeout: int = 5,
        phrase_time_limit: int = 10,
    ) -> None:
        """Initialize speech recognition settings."""
        self.recognizer = sr.Recognizer()
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit

    def listen_once(self) -> str:
        """Capture microphone audio and return the recognized text."""
        try:
            with sr.Microphone() as source:
                print("Listening... Speak your command.")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5,
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )

        except sr.WaitTimeoutError as exc:
            raise SpeechInputError(
                "No speech detected before the listening timeout."
            ) from exc

        return self.transcribe(audio)

    def transcribe(self, audio: sr.AudioData) -> str:
        """Convert recorded audio into text using online recognition."""
        try:
            text = self.recognizer.recognize_google(
                audio,
                language=self.language,
            ).strip()

        except sr.UnknownValueError as exc:
            raise SpeechInputError(
                "Speech could not be understood. Please try again."
            ) from exc

        except sr.RequestError as exc:
            raise SpeechInputError(
                "Speech recognition service is unavailable. "
                "Check your internet connection."
            ) from exc

        if not text:
            raise SpeechInputError(
                "Speech recognition returned an empty command."
            )

        return text
