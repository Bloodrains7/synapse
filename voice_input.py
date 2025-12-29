"""
Synapse Voice Input
Captures voice commands using speech recognition
"""

import speech_recognition as sr
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

from config import config


class VoiceStatus(Enum):
    LISTENING = "listening"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class VoiceResult:
    """Result of voice recognition"""
    status: VoiceStatus
    text: str = ""
    confidence: float = 0.0
    error: str = ""


class VoiceInput:
    """Captures and processes voice input"""

    def __init__(self, language: str = None):
        self.recognizer = sr.Recognizer()
        self.language = language or config.voice_language
        self.microphone = None

    def list_microphones(self) -> list[str]:
        """List available microphones"""
        return sr.Microphone.list_microphone_names()

    def calibrate(self, duration: float = 1.0):
        """Calibrate for ambient noise"""
        with sr.Microphone() as source:
            print("Calibrating for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            print("Calibration complete")

    def listen(
        self,
        timeout: int = None,
        phrase_time_limit: int = None,
        on_status: Optional[Callable[[VoiceStatus], None]] = None
    ) -> VoiceResult:
        """
        Listen for voice input and return transcribed text

        Args:
            timeout: Maximum time to wait for speech to start
            phrase_time_limit: Maximum time for the phrase
            on_status: Callback for status updates
        """
        timeout = timeout or config.voice_timeout

        try:
            with sr.Microphone() as source:
                if on_status:
                    on_status(VoiceStatus.LISTENING)

                print(f"Listening... (language: {self.language})")

                # Listen for audio
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit or 30
                )

                if on_status:
                    on_status(VoiceStatus.PROCESSING)

                print("Processing speech...")

                # Try Google Speech Recognition
                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language=self.language,
                        show_all=False
                    )

                    if on_status:
                        on_status(VoiceStatus.SUCCESS)

                    return VoiceResult(
                        status=VoiceStatus.SUCCESS,
                        text=text,
                        confidence=1.0
                    )

                except sr.UnknownValueError:
                    return VoiceResult(
                        status=VoiceStatus.ERROR,
                        error="Could not understand audio"
                    )

                except sr.RequestError as e:
                    return VoiceResult(
                        status=VoiceStatus.ERROR,
                        error=f"Speech recognition service error: {e}"
                    )

        except sr.WaitTimeoutError:
            if on_status:
                on_status(VoiceStatus.TIMEOUT)
            return VoiceResult(
                status=VoiceStatus.TIMEOUT,
                error="No speech detected within timeout"
            )

        except Exception as e:
            if on_status:
                on_status(VoiceStatus.ERROR)
            return VoiceResult(
                status=VoiceStatus.ERROR,
                error=str(e)
            )

    def listen_continuous(
        self,
        callback: Callable[[VoiceResult], bool],
        stop_phrase: str = "stop"
    ):
        """
        Continuously listen for voice commands

        Args:
            callback: Function to call with each result. Return False to stop.
            stop_phrase: Phrase that stops listening
        """
        print(f"Continuous listening mode. Say '{stop_phrase}' to exit.")

        while True:
            result = self.listen()

            if result.status == VoiceStatus.SUCCESS:
                if stop_phrase.lower() in result.text.lower():
                    print("Stop phrase detected. Exiting.")
                    break

                # Call the callback
                if not callback(result):
                    break

            elif result.status == VoiceStatus.TIMEOUT:
                # Continue listening on timeout
                continue

            elif result.status == VoiceStatus.ERROR:
                print(f"Error: {result.error}")
                # Continue listening on error
                continue


def create_voice_input(language: str = None) -> VoiceInput:
    """Create a voice input instance"""
    return VoiceInput(language=language)


if __name__ == "__main__":
    # Test voice input
    voice = VoiceInput()

    print("Available microphones:")
    for i, mic in enumerate(voice.list_microphones()):
        print(f"  {i}: {mic}")

    print("\nCalibrating...")
    voice.calibrate()

    print("\nListening for command...")
    result = voice.listen(timeout=10)

    if result.status == VoiceStatus.SUCCESS:
        print(f"You said: {result.text}")
    else:
        print(f"Error: {result.error}")
