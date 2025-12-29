"""
Synapse - Voice Commander for Test Automation
Main entry point
"""

import argparse
import sys
from typing import Optional

from config import config
from voice_input import VoiceInput, VoiceStatus, VoiceResult
from agents import SynapseCrew


def print_banner():
    """Print application banner"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗ ║
║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝ ║
║   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗   ║
║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝   ║
║   ███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗ ║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝ ║
║                                                               ║
║           Voice Commander for Test Automation                 ║
║                 Powered by Gemini & CrewAI                    ║
╚═══════════════════════════════════════════════════════════════╝
""")


def voice_mode(language: str = None):
    """Run in voice command mode"""
    print_banner()
    print("Voice Command Mode")
    print("-" * 60)

    voice = VoiceInput(language=language)
    crew = SynapseCrew()

    print("Calibrating microphone...")
    voice.calibrate()

    print("\nReady! Speak your command.")
    print("Examples:")
    print('  - "Vygeneruj testovacie scenare pre projekt company-angular"')
    print('  - "Generate Playwright tests for the scenarios"')
    print('  - "Run the tests against localhost:4200"')
    print('  - "Nadiktujem scenar: klikni na submit button a over ze sa zobrazi success message"')
    print('\nSay "stop" or "koniec" to exit.\n')

    def handle_command(result: VoiceResult) -> bool:
        """Handle a recognized voice command"""
        print(f"\n>>> Recognized: {result.text}")

        # Check for stop commands
        stop_words = ["stop", "koniec", "exit", "quit", "ukonci"]
        if any(word in result.text.lower() for word in stop_words):
            print("Stopping...")
            return False

        # Process the command
        try:
            response = crew.process_command(result.text)
            print(f"\n<<< Response:\n{response}")
        except Exception as e:
            print(f"\n<<< Error: {e}")

        print("\n" + "-" * 60)
        print("Listening for next command...")
        return True

    # Start continuous listening
    voice.listen_continuous(handle_command, stop_phrase="stop")


def text_mode():
    """Run in text command mode (for testing without microphone)"""
    print_banner()
    print("Text Command Mode")
    print("-" * 60)

    crew = SynapseCrew()

    print("Enter commands (type 'exit' to quit):\n")

    while True:
        try:
            command = input(">>> ").strip()

            if not command:
                continue

            if command.lower() in ["exit", "quit", "stop"]:
                print("Exiting...")
                break

            # Process the command
            response = crew.process_command(command)
            print(f"\n<<< Response:\n{response}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n<<< Error: {e}\n")


def single_command(command: str):
    """Execute a single command"""
    print_banner()

    crew = SynapseCrew()
    response = crew.process_command(command)
    print(response)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Synapse - Voice Commander for Test Automation"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Voice mode
    voice_parser = subparsers.add_parser("voice", help="Voice command mode")
    voice_parser.add_argument(
        "--language", "-l",
        default=config.voice_language,
        help="Voice recognition language (e.g., sk-SK, en-US)"
    )

    # Text mode
    text_parser = subparsers.add_parser("text", help="Text command mode")

    # Single command mode
    cmd_parser = subparsers.add_parser("command", help="Execute single command")
    cmd_parser.add_argument("command", help="Command to execute")

    # List microphones
    mic_parser = subparsers.add_parser("mics", help="List available microphones")

    args = parser.parse_args()

    if args.mode == "voice":
        voice_mode(language=args.language)

    elif args.mode == "text":
        text_mode()

    elif args.mode == "command":
        single_command(args.command)

    elif args.mode == "mics":
        voice = VoiceInput()
        print("Available microphones:")
        for i, mic in enumerate(voice.list_microphones()):
            print(f"  {i}: {mic}")

    else:
        # Default to text mode
        text_mode()


if __name__ == "__main__":
    main()
