"""
Voice Transcriber Module
Handles speech-to-text conversion using Google Speech Recognition
"""
import os
import speech_recognition as sr
from typing import Optional, Callable
from rich.console import Console
from rich.panel import Panel

console = Console()


class VoiceTranscriber:
    """Handles voice input and transcription."""

    def __init__(
        self,
        language: str = "en-US",
        timeout: int = 5,
        phrase_timeout: int = 3
    ):
        self.language = language
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        self.recognizer = sr.Recognizer()
        self.microphone = None

        # Adjust for ambient noise
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000

    def initialize_microphone(self) -> bool:
        """Initialize the microphone."""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                console.print("[dim]Calibrating microphone for ambient noise...[/dim]")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            console.print("[green]Microphone ready![/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error initializing microphone: {e}[/red]")
            return False

    def listen(self, prompt: str = "Listening...") -> Optional[str]:
        """Listen for voice input and transcribe."""
        if not self.microphone:
            if not self.initialize_microphone():
                return None

        try:
            with self.microphone as source:
                console.print(Panel(prompt, style="cyan"))
                console.print("[dim]Speak now...[/dim]")

                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_timeout * 3  # Allow longer phrases
                )

            console.print("[dim]Processing speech...[/dim]")
            text = self.recognizer.recognize_google(
                audio,
                language=self.language
            )

            console.print(f"[green]Recognized:[/green] {text}")
            return text

        except sr.WaitTimeoutError:
            console.print("[yellow]No speech detected. Please try again.[/yellow]")
            return None
        except sr.UnknownValueError:
            console.print("[yellow]Could not understand audio. Please try again.[/yellow]")
            return None
        except sr.RequestError as e:
            console.print(f"[red]Speech recognition service error: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error during transcription: {e}[/red]")
            return None

    def listen_continuous(
        self,
        callback: Callable[[str], None],
        stop_phrase: str = "stop listening"
    ):
        """Continuously listen and call callback with transcribed text."""
        console.print(f"[cyan]Continuous listening mode. Say '{stop_phrase}' to stop.[/cyan]")

        while True:
            text = self.listen("Waiting for command...")
            if text:
                if stop_phrase.lower() in text.lower():
                    console.print("[yellow]Stopping continuous listening.[/yellow]")
                    break
                callback(text)

    def listen_for_dictation(self, max_duration: int = 60) -> Optional[str]:
        """Listen for longer dictation (test scenarios)."""
        if not self.microphone:
            if not self.initialize_microphone():
                return None

        try:
            with self.microphone as source:
                console.print(Panel(
                    "Dictation Mode - Speak your test scenario",
                    style="cyan"
                ))
                console.print(f"[dim]Recording for up to {max_duration} seconds...[/dim]")
                console.print("[dim]Say 'end dictation' when finished.[/dim]")

                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=max_duration
                )

            console.print("[dim]Processing dictation...[/dim]")
            text = self.recognizer.recognize_google(
                audio,
                language=self.language
            )

            # Clean up end marker
            text = text.replace("end dictation", "").strip()

            console.print(f"[green]Dictation recorded:[/green]\n{text}")
            return text

        except Exception as e:
            console.print(f"[red]Error during dictation: {e}[/red]")
            return None


class TextInput:
    """Fallback text input when microphone is not available."""

    @staticmethod
    def get_input(prompt: str = "Enter command: ") -> str:
        """Get text input from user."""
        console.print(Panel(prompt, style="cyan"))
        return console.input("[bold]> [/bold]")

    @staticmethod
    def get_multiline_input(prompt: str = "Enter text (empty line to finish):") -> str:
        """Get multiline text input."""
        console.print(Panel(prompt, style="cyan"))
        lines = []
        while True:
            line = console.input()
            if not line:
                break
            lines.append(line)
        return "\n".join(lines)
