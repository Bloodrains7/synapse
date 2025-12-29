"""
Synapse - Voice Commander for Test Automation
Main entry point
"""

import argparse
import sys

from config import config
from agents import SynapseCrew, handle_tool_call


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
║              Powered by Gemini Live API                       ║
╚═══════════════════════════════════════════════════════════════╝
""")


def live_mode():
    """Run in live voice mode with Gemini Live API"""
    print_banner()

    try:
        from live_voice import SynapseLive

        live = SynapseLive(tool_handler=handle_tool_call)
        live.start()
    except ImportError as e:
        print(f"Error: Missing dependencies for live mode: {e}")
        print("Install with: pip install google-genai pyaudio")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting live mode: {e}")
        sys.exit(1)


def text_mode():
    """Run in text command mode (for testing without microphone)"""
    print_banner()
    print("Text Command Mode")
    print("-" * 60)

    crew = SynapseCrew()

    print("Enter commands (type 'exit' to quit):\n")
    print("Examples:")
    print('  - "Generate scenarios for C:/Projects/company-angular"')
    print('  - "Generate Playwright tests from result/scenarios.json"')
    print('  - "Run tests in result/tests against localhost:4200"')
    print()

    while True:
        try:
            command = input(">>> ").strip()

            if not command:
                continue

            if command.lower() in ["exit", "quit", "stop", "q"]:
                print("Exiting...")
                break

            # Process the command
            response = crew.process_command(command)
            print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def single_command(command: str):
    """Execute a single command"""
    print_banner()

    crew = SynapseCrew()
    response = crew.process_command(command)
    print(response)


def list_microphones():
    """List available audio devices"""
    try:
        import sounddevice as sd

        print("Available Audio Devices:")
        print("-" * 60)
        print(sd.query_devices())
        print()
        print(f"Default input:  {sd.query_devices(kind='input')['name']}")
        print(f"Default output: {sd.query_devices(kind='output')['name']}")
    except ImportError:
        print("sounddevice not installed. Run: pip install sounddevice")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Synapse - Voice Commander for Test Automation"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Live mode (default)
    live_parser = subparsers.add_parser("live", help="Live voice mode with Gemini Live API")

    # Text mode
    text_parser = subparsers.add_parser("text", help="Text command mode")

    # Single command mode
    cmd_parser = subparsers.add_parser("command", help="Execute single command")
    cmd_parser.add_argument("command", help="Command to execute")

    # List audio devices
    devices_parser = subparsers.add_parser("devices", help="List available audio devices")

    args = parser.parse_args()

    if args.mode == "live":
        live_mode()

    elif args.mode == "text":
        text_mode()

    elif args.mode == "command":
        single_command(args.command)

    elif args.mode == "devices":
        list_microphones()

    else:
        # Default to text mode (safer than live mode)
        text_mode()


if __name__ == "__main__":
    main()
