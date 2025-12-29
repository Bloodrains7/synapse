"""
Command Parser Module
Parses voice commands and extracts intent and parameters
"""
import re
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from rich.console import Console

console = Console()


class CommandType(Enum):
    """Types of commands the system can handle."""
    GENERATE_SCENARIOS = "generate_scenarios"
    GENERATE_PLAYWRIGHT = "generate_playwright"
    DICTATE_SCENARIO = "dictate_scenario"
    GENERATE_FROM_FILE = "generate_from_file"
    CODE_REVIEW = "code_review"
    # Marker commands (via gRPC)
    MARKER_RUN = "marker_run"
    MARKER_PREVIEW = "marker_preview"
    MARKER_ROLLBACK = "marker_rollback"
    MARKER_ANALYZE = "marker_analyze"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Parsed command with type and parameters."""
    command_type: CommandType
    target: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    raw_text: str = ""

    def __str__(self):
        return f"Command: {self.command_type.value}, Target: {self.target}"


class CommandParser:
    """Parses voice/text commands into structured format."""

    # Command patterns (regex)
    PATTERNS = {
        CommandType.GENERATE_SCENARIOS: [
            r"(?:generate|create|write)\s+(?:test\s+)?scenarios?\s+(?:for\s+)?(.+)",
            r"(?:make|build)\s+(?:test\s+)?scenarios?\s+(?:for\s+)?(.+)",
            r"scenarios?\s+(?:for\s+)?(.+)",
        ],
        CommandType.GENERATE_PLAYWRIGHT: [
            r"(?:generate|create|write)\s+playwright\s+(?:tests?\s+)?(?:for\s+)?(.+)",
            r"(?:make|build)\s+playwright\s+(?:tests?\s+)?(?:for\s+)?(.+)",
            r"playwright\s+(?:tests?\s+)?(?:for\s+)?(.+)",
            r"(?:generate|create)\s+(?:e2e|end.to.end)\s+tests?\s+(?:for\s+)?(.+)",
        ],
        CommandType.DICTATE_SCENARIO: [
            r"dictate\s+(?:a\s+)?(?:test\s+)?scenario",
            r"record\s+(?:a\s+)?(?:test\s+)?scenario",
            r"start\s+dictation",
        ],
        CommandType.GENERATE_FROM_FILE: [
            r"(?:generate|create)\s+(?:tests?\s+)?from\s+(?:file\s+)?(.+)",
            r"(?:convert|transform)\s+(?:file\s+)?(.+)\s+to\s+(?:playwright\s+)?tests?",
        ],
        CommandType.CODE_REVIEW: [
            r"(?:review|check)\s+(?:code\s+)?(?:in\s+)?(.+)",
            r"code\s+review\s+(?:for\s+)?(.+)",
        ],
        # Marker commands
        CommandType.MARKER_RUN: [
            r"(?:run|add|apply)\s+(?:test\s+)?(?:id|ids|marker)\s+(?:to|for|on)\s+(.+)",
            r"marker\s+(?:run|add)\s+(?:on\s+)?(.+)",
            r"add\s+test\s+ids?\s+(?:to\s+)?(.+)",
        ],
        CommandType.MARKER_PREVIEW: [
            r"(?:preview|show)\s+(?:test\s+)?(?:id|ids|marker)\s+(?:changes?\s+)?(?:for\s+)?(.+)",
            r"marker\s+preview\s+(.+)",
            r"dry.?run\s+marker\s+(?:on\s+)?(.+)",
        ],
        CommandType.MARKER_ROLLBACK: [
            r"(?:rollback|undo|revert)\s+(?:test\s+)?(?:id|ids|marker)\s+(?:changes?\s+)?(?:for\s+)?(.+)?",
            r"marker\s+rollback\s*(.+)?",
        ],
        CommandType.MARKER_ANALYZE: [
            r"(?:analyze|scan)\s+(?:project\s+)?(.+)\s+(?:for\s+)?(?:test\s+)?(?:id|ids)",
            r"marker\s+analyze\s+(.+)",
        ],
        CommandType.HELP: [
            r"^help$",
            r"^what\s+can\s+you\s+do",
            r"^show\s+commands?$",
        ],
        CommandType.EXIT: [
            r"^(?:exit|quit|bye|stop)$",
            r"^close\s+synapse$",
        ],
    }

    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = {
            cmd_type: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cmd_type, patterns in self.PATTERNS.items()
        }

    def parse(self, text: str) -> ParsedCommand:
        """Parse text into a command."""
        text = text.strip()

        if not text:
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                raw_text=text
            )

        # Try each command type
        for cmd_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    target = None
                    if match.groups():
                        target = match.group(1).strip() if match.group(1) else None

                    return ParsedCommand(
                        command_type=cmd_type,
                        target=target,
                        raw_text=text
                    )

        # Unknown command
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            target=text,
            raw_text=text
        )

    def get_help_text(self) -> str:
        """Return help text with available commands."""
        return """
Available Commands:

[bold cyan]Generate Test Scenarios:[/bold cyan]
  "Generate scenarios for user login"
  "Create test scenarios for shopping cart"

[bold cyan]Generate Playwright Tests:[/bold cyan]
  "Generate Playwright tests for checkout flow"
  "Create e2e tests for registration"

[bold cyan]Dictate Scenario:[/bold cyan]
  "Dictate scenario" - Start recording a test scenario

[bold cyan]Generate from File:[/bold cyan]
  "Generate tests from features/login.feature"
  "Convert scenarios.md to Playwright tests"

[bold cyan]Code Review:[/bold cyan]
  "Review code in tests/login.spec.ts"

[bold cyan]Marker (Test IDs):[/bold cyan]
  "Add test ids to /path/to/project"
  "Preview marker changes for /path"
  "Rollback marker changes"
  "Analyze project for test ids"

[bold cyan]Other:[/bold cyan]
  "help" - Show this help
  "exit" - Exit Synapse
"""


class CommandEnhancer:
    """Enhances parsed commands with additional context."""

    @staticmethod
    def enhance(command: ParsedCommand) -> ParsedCommand:
        """Add additional parameters based on target analysis."""
        if not command.target:
            return command

        parameters = {}

        # Detect if target mentions specific features
        target_lower = command.target.lower()

        # Detect authentication-related
        if any(word in target_lower for word in ['login', 'auth', 'signin', 'signup', 'register', 'password']):
            parameters['category'] = 'authentication'
            parameters['priority'] = 'high'

        # Detect e-commerce
        if any(word in target_lower for word in ['cart', 'checkout', 'payment', 'order', 'product']):
            parameters['category'] = 'e-commerce'
            parameters['priority'] = 'high'

        # Detect form-related
        if any(word in target_lower for word in ['form', 'input', 'validation', 'submit']):
            parameters['category'] = 'forms'
            parameters['includes_validation'] = True

        # Detect navigation
        if any(word in target_lower for word in ['navigation', 'menu', 'link', 'route', 'page']):
            parameters['category'] = 'navigation'

        # Detect API-related
        if any(word in target_lower for word in ['api', 'request', 'response', 'endpoint']):
            parameters['category'] = 'api'
            parameters['test_type'] = 'api'

        command.parameters = parameters
        return command
