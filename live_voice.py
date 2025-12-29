"""
Synapse Live Voice Module
Real-time voice interaction using Gemini Live API
Uses sounddevice for cross-platform audio (no compilation needed)
"""

import asyncio
import sys
import traceback
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from google import genai

from config import config

# Audio settings
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
DTYPE = np.int16

# System instruction for test automation assistant
SYSTEM_INSTRUCTION = """You are Synapse, a voice-controlled test automation assistant.
You help users with test automation tasks by understanding their voice commands.

IMPORTANT: The user can speak to you OR type in the console. For paths, URLs, and technical details,
ASK the user to TYPE them in the console - don't try to understand paths from voice.

When you need a path or URL, say something like:
- "Please type the project path in the console"
- "Napíš cestu k projektu do konzoly"

Available actions:
1. generate_scenarios - Generate test scenarios from a frontend project
   - Requires: project_path (ask user to type it)

2. generate_tests - Generate Playwright tests from scenarios
   - Requires: scenarios_path (ask user to type it)
   - Optional: framework (playwright/robot/cypress), base_url

3. run_tests - Run the generated tests
   - Requires: test_dir (ask user to type it)
   - Optional: base_url, headed (true/false)

4. add_test_ids - Add data-testid attributes to frontend components
   - Requires: project_path (ask user to type it)

Workflow:
1. User says what they want (e.g. "generate scenarios")
2. You identify the intent and ask them to TYPE any required paths/URLs
3. User types the path in console
4. You confirm and execute

Speak naturally in Slovak or English based on the user's language.
Keep responses concise. Always ask for paths via typing, not voice.
"""


class SynapseLive:
    """Real-time voice interaction with Gemini Live API"""

    def __init__(self, tool_handler: Optional[Callable] = None):
        """
        Initialize the live voice session.

        Args:
            tool_handler: Optional callback for handling tool calls
        """
        self.tool_handler = tool_handler
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.running = False
        self.input_stream = None
        self.output_stream = None

        # Setup client
        self.client = genai.Client(
            api_key=config.google_api_key,
            http_options={"api_version": "v1beta"}
        )

    def _audio_input_callback(self, indata, frames, time, status):
        """Callback for audio input stream"""
        if status:
            print(f"Input status: {status}")
        if self.running and self.out_queue:
            # Convert numpy array to bytes
            audio_bytes = indata.tobytes()
            try:
                self.out_queue.put_nowait({"data": audio_bytes, "mime_type": "audio/pcm"})
            except asyncio.QueueFull:
                pass  # Skip if queue is full

    async def listen_audio(self):
        """Start audio input stream"""
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time, status):
            if status:
                print(f"Input status: {status}")
            if self.running:
                audio_bytes = indata.tobytes()
                loop.call_soon_threadsafe(
                    lambda: self.out_queue.put_nowait({"data": audio_bytes, "mime_type": "audio/pcm"})
                    if not self.out_queue.full() else None
                )

        self.input_stream = sd.InputStream(
            samplerate=SEND_SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=CHUNK_SIZE,
            callback=callback
        )
        self.input_stream.start()

        # Keep running until stopped
        while self.running:
            await asyncio.sleep(0.1)

        self.input_stream.stop()
        self.input_stream.close()

    async def send_realtime(self):
        """Send audio/data to the model in real-time"""
        while self.running:
            try:
                msg = await asyncio.wait_for(self.out_queue.get(), timeout=0.1)
                await self.session.send(input=msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"Send error: {e}")
                break

    async def receive_audio(self):
        """Receive and process model responses"""
        while self.running:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Handle audio data
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue

                    # Handle text output
                    if text := response.text:
                        print(text, end="", flush=True)

                    # Handle tool calls
                    if hasattr(response, 'tool_call') and response.tool_call:
                        await self._handle_tool_call(response.tool_call)

                # Clear audio queue on turn complete (for interruptions)
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

            except Exception as e:
                if self.running:
                    print(f"\nReceive error: {e}")
                break

    async def _handle_tool_call(self, tool_call):
        """Handle a tool call from the model"""
        tool_name = tool_call.name
        tool_args = tool_call.args

        print(f"\n[Tool Call: {tool_name}]")
        print(f"Arguments: {tool_args}")

        if self.tool_handler:
            try:
                result = await asyncio.to_thread(
                    self.tool_handler, tool_name, tool_args
                )
                # Send result back to model
                await self.session.send(
                    input=f"Tool result for {tool_name}: {result}",
                    end_of_turn=True
                )
            except Exception as e:
                await self.session.send(
                    input=f"Tool error for {tool_name}: {str(e)}",
                    end_of_turn=True
                )

    async def play_audio(self):
        """Play audio responses from the model"""
        self.output_stream = sd.OutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
        )
        self.output_stream.start()

        while self.running:
            try:
                bytestream = await asyncio.wait_for(
                    self.audio_in_queue.get(), timeout=0.1
                )
                # Convert bytes to numpy array and play
                audio_array = np.frombuffer(bytestream, dtype=DTYPE)
                await asyncio.to_thread(self.output_stream.write, audio_array)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"Audio output error: {e}")
                break

        self.output_stream.stop()
        self.output_stream.close()

    async def send_text(self):
        """Allow text input alongside voice"""
        while self.running:
            try:
                text = await asyncio.to_thread(input, "[type here] > ")
                if text.lower() in ["q", "quit", "exit", "stop", "koniec"]:
                    self.running = False
                    break
                if text:
                    print(f">>> {text}")
                    await self.session.send(input=text, end_of_turn=True)
            except EOFError:
                break
            except Exception as e:
                if self.running:
                    print(f"Input error: {e}")
                break

    async def run(self):
        """Main run loop"""
        print("\n" + "=" * 60)
        print("SYNAPSE - Live Voice Mode")
        print("=" * 60)
        print("Connecting to Gemini Live API...")
        print()
        print("  VOICE: Speak commands naturally")
        print("  TYPE:  Enter paths, URLs, or any text below")
        print("  EXIT:  Say 'stop'/'koniec' or type 'q'")
        print()
        print("  TIP: Use headphones to prevent echo!")
        print("=" * 60 + "\n")

        self.running = True

        # Configure session
        session_config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": SYSTEM_INSTRUCTION,
        }

        try:
            async with (
                self.client.aio.live.connect(
                    model=config.gemini_live_model,
                    config=session_config
                ) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                print("Connected! Listening...\n")

                # Start all tasks
                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                self.running = False

        except asyncio.CancelledError:
            pass
        except Exception as e:
            traceback.print_exception(e)
        finally:
            self.running = False
            print("\nSession ended.")

    def start(self):
        """Start the live voice session"""
        asyncio.run(self.run())


def main():
    """Entry point for testing"""
    live = SynapseLive()
    live.start()


if __name__ == "__main__":
    main()
