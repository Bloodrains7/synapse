"""
Synapse - Voice Commander
AI-powered voice command system for generating test scenarios and Playwright tests
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from voice.transcriber import VoiceTranscriber, TextInput
from parser.command_parser import CommandParser, CommandEnhancer, CommandType
from agents.crew import SynapseCrew
from output.writer import OutputWriter
from grpc_client import MarkerClient

load_dotenv()

app = typer.Typer(help="Synapse - Voice Commander for Test Generation")
console = Console()


class Synapse:
    """Main Synapse application."""

    def __init__(self, use_voice: bool = True):
        self.use_voice = use_voice
        self.parser = CommandParser()
        self.enhancer = CommandEnhancer()
        self.writer = OutputWriter(os.getenv("OUTPUT_DIR", "./output"))
        self.crew = None  # Lazy initialization
        self.marker_client = None  # Lazy initialization

        if use_voice:
            self.voice = VoiceTranscriber(
                language=os.getenv("VOICE_LANGUAGE", "en-US"),
                timeout=int(os.getenv("VOICE_TIMEOUT", "5")),
                phrase_timeout=int(os.getenv("VOICE_PHRASE_TIMEOUT", "3"))
            )
        else:
            self.voice = None

    def _init_crew(self):
        """Initialize AI agents (lazy loading)."""
        if self.crew is None:
            console.print("[dim]Initializing AI agents...[/dim]")
            self.crew = SynapseCrew()
            console.print("[green]AI agents ready![/green]")

    def _init_marker(self):
        """Initialize Marker gRPC client (lazy loading)."""
        if self.marker_client is None:
            console.print("[dim]Connecting to Marker service...[/dim]")
            try:
                self.marker_client = MarkerClient()
                self.marker_client.connect()
                console.print("[green]Marker service connected![/green]")
            except Exception as e:
                console.print(f"[red]Failed to connect to Marker: {e}[/red]")
                console.print("[yellow]Make sure Marker gRPC server is running[/yellow]")
                self.marker_client = None

    def get_input(self, prompt: str = "Waiting for command...") -> str:
        """Get input from voice or text."""
        if self.use_voice and self.voice:
            return self.voice.listen(prompt) or ""
        else:
            return TextInput.get_input(prompt)

    def process_command(self, text: str) -> bool:
        """Process a command. Returns False if should exit."""
        command = self.parser.parse(text)
        command = self.enhancer.enhance(command)

        console.print(f"[dim]Parsed: {command}[/dim]")

        if command.command_type == CommandType.EXIT:
            console.print("[yellow]Goodbye![/yellow]")
            return False

        elif command.command_type == CommandType.HELP:
            console.print(Markdown(self.parser.get_help_text()))

        elif command.command_type == CommandType.GENERATE_SCENARIOS:
            self._generate_scenarios(command.target, command.parameters)

        elif command.command_type == CommandType.GENERATE_PLAYWRIGHT:
            self._generate_playwright(command.target, command.parameters)

        elif command.command_type == CommandType.DICTATE_SCENARIO:
            self._dictate_scenario()

        elif command.command_type == CommandType.GENERATE_FROM_FILE:
            self._generate_from_file(command.target)

        elif command.command_type == CommandType.CODE_REVIEW:
            self._code_review(command.target)

        # Marker commands (via gRPC)
        elif command.command_type == CommandType.MARKER_RUN:
            self._marker_run(command.target)

        elif command.command_type == CommandType.MARKER_PREVIEW:
            self._marker_preview(command.target)

        elif command.command_type == CommandType.MARKER_ROLLBACK:
            self._marker_rollback(command.target)

        elif command.command_type == CommandType.MARKER_ANALYZE:
            self._marker_analyze(command.target)

        elif command.command_type == CommandType.UNKNOWN:
            console.print(f"[yellow]Unknown command. Processing as general request...[/yellow]")
            self._process_general_request(text)

        return True

    def _generate_scenarios(self, target: str, context: dict = None):
        """Generate test scenarios."""
        if not target:
            console.print("[red]Please specify what to generate scenarios for.[/red]")
            return

        self._init_crew()

        try:
            result = self.crew.generate_scenarios(target, context)
            self.writer.save_scenarios(result, target)
            console.print(Panel(result, title="Generated Scenarios", border_style="green"))
        except Exception as e:
            console.print(f"[red]Error generating scenarios: {e}[/red]")

    def _generate_playwright(self, target: str, context: dict = None):
        """Generate Playwright tests."""
        if not target:
            console.print("[red]Please specify what to generate tests for.[/red]")
            return

        self._init_crew()

        try:
            # Ask if user wants scenarios first
            console.print("[cyan]Generate test scenarios first? (yes/no)[/cyan]")
            response = self.get_input("Yes or No?").lower()

            if response.startswith('y'):
                results = self.crew.generate_full_suite(target, context)
                paths = self.writer.save_full_suite(results, target)
                console.print(Panel(
                    f"Generated files:\n" + "\n".join([f"- {p}" for p in paths.values()]),
                    title="Full Test Suite Generated",
                    border_style="green"
                ))
            else:
                result = self.crew.generate_playwright_tests(target)
                self.writer.save_playwright_tests(result, target)
                console.print(Panel(result, title="Generated Playwright Tests", border_style="green"))

        except Exception as e:
            console.print(f"[red]Error generating tests: {e}[/red]")

    def _dictate_scenario(self):
        """Dictate a test scenario via voice."""
        console.print("[cyan]Dictation mode. Describe your test scenario.[/cyan]")

        if self.use_voice and self.voice:
            scenario = self.voice.listen_for_dictation()
        else:
            scenario = TextInput.get_multiline_input("Enter your test scenario:")

        if scenario:
            console.print(f"\n[bold]Recorded scenario:[/bold]\n{scenario}")

            console.print("\n[cyan]Generate Playwright tests from this scenario? (yes/no)[/cyan]")
            response = self.get_input().lower()

            if response.startswith('y'):
                self._init_crew()
                result = self.crew.generate_playwright_tests(
                    "dictated scenario",
                    scenarios=scenario
                )
                self.writer.save_playwright_tests(result, "dictated_scenario")
                console.print(Panel(result, title="Generated Tests", border_style="green"))

    def _generate_from_file(self, filepath: str):
        """Generate tests from an existing file."""
        if not filepath:
            console.print("[red]Please specify the file path.[/red]")
            return

        path = Path(filepath)
        if not path.exists():
            console.print(f"[red]File not found: {filepath}[/red]")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._init_crew()
            result = self.crew.generate_playwright_tests(
                f"from file {path.name}",
                scenarios=content
            )
            self.writer.save_playwright_tests(result, path.stem)
            console.print(Panel(result, title="Generated Tests", border_style="green"))

        except Exception as e:
            console.print(f"[red]Error processing file: {e}[/red]")

    def _code_review(self, target: str):
        """Review code from a file."""
        if not target:
            console.print("[red]Please specify the file to review.[/red]")
            return

        path = Path(target)
        if not path.exists():
            console.print(f"[red]File not found: {target}[/red]")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()

            self._init_crew()
            result = self.crew.review_code(code)
            self.writer.save_review(result, path.stem)
            console.print(Panel(result, title="Code Review", border_style="cyan"))

        except Exception as e:
            console.print(f"[red]Error reviewing code: {e}[/red]")

    def _process_general_request(self, text: str):
        """Process a general/unknown request."""
        self._init_crew()
        try:
            result = self.crew.generate_scenarios(text)
            self.writer.save_scenarios(result, "general_request")
            console.print(Panel(result, title="Generated Response", border_style="green"))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _marker_run(self, target: str):
        """Run Marker to add test IDs to a project."""
        if not target:
            console.print("[red]Please specify the project path.[/red]")
            return

        self._init_marker()
        if not self.marker_client:
            return

        try:
            console.print(f"[cyan]Running Marker on: {target}[/cyan]")
            result = self.marker_client.run_marker(target)

            if result['success']:
                console.print(Panel(
                    f"Files processed: {result.get('files_processed', 0)}\n"
                    f"IDs added: {result.get('ids_added', 0)}",
                    title="Marker Complete",
                    border_style="green"
                ))
            else:
                console.print(f"[red]Marker failed: {result.get('error_message', 'Unknown error')}[/red]")

        except Exception as e:
            console.print(f"[red]Error running Marker: {e}[/red]")

    def _marker_preview(self, target: str):
        """Preview Marker changes (dry-run)."""
        if not target:
            console.print("[red]Please specify the project path.[/red]")
            return

        self._init_marker()
        if not self.marker_client:
            return

        try:
            console.print(f"[cyan]Previewing Marker changes for: {target}[/cyan]")
            result = self.marker_client.preview_changes(target)

            if result['success']:
                console.print(Panel(
                    f"Files found: {result.get('files_found', 0)}\n"
                    f"Potential IDs: {result.get('potential_ids', 0)}",
                    title="Marker Preview",
                    border_style="cyan"
                ))

                # Show previews
                for preview in result.get('previews', [])[:5]:
                    console.print(f"\n[bold]{preview['file_path']}[/bold] ({preview['potential_ids']} IDs)")
                    for el in preview.get('elements', [])[:3]:
                        console.print(f"  - {el['element_type']}: {el['test_id']}")

            else:
                console.print(f"[red]Preview failed: {result.get('error_message', 'Unknown error')}[/red]")

        except Exception as e:
            console.print(f"[red]Error previewing: {e}[/red]")

    def _marker_rollback(self, target: str = None):
        """Rollback Marker changes."""
        if not target:
            console.print("[yellow]No project specified. Please specify the project path to rollback.[/yellow]")
            return

        self._init_marker()
        if not self.marker_client:
            return

        try:
            console.print(f"[cyan]Rolling back Marker changes for: {target}[/cyan]")
            result = self.marker_client.rollback(target)

            if result['success']:
                console.print(Panel(
                    f"Files restored: {result.get('files_restored', 0)}",
                    title="Rollback Complete",
                    border_style="green"
                ))
            else:
                console.print(f"[red]Rollback failed: {result.get('error_message', 'Unknown error')}[/red]")

        except Exception as e:
            console.print(f"[red]Error rolling back: {e}[/red]")

    def _marker_analyze(self, target: str):
        """Analyze project for test IDs."""
        if not target:
            console.print("[red]Please specify the project path.[/red]")
            return

        self._init_marker()
        if not self.marker_client:
            return

        try:
            console.print(f"[cyan]Analyzing project: {target}[/cyan]")
            result = self.marker_client.analyze_project(target)

            if result['success']:
                table = Table(title="Project Analysis")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", justify="right")

                table.add_row("Total Files", str(result.get('total_files', 0)))

                for ext, count in result.get('file_types', {}).items():
                    table.add_row(f"  {ext} files", str(count))

                console.print(table)
            else:
                console.print(f"[red]Analysis failed: {result.get('error_message', 'Unknown error')}[/red]")

        except Exception as e:
            console.print(f"[red]Error analyzing: {e}[/red]")

    def run_interactive(self):
        """Run in interactive mode."""
        console.print(Panel.fit(
            "[bold cyan]Synapse - Voice Commander[/bold cyan]\n"
            "AI-powered test generation system\n\n"
            "Say 'help' for available commands\n"
            "Say 'exit' to quit",
            border_style="cyan"
        ))

        while True:
            try:
                text = self.get_input()
                if text:
                    if not self.process_command(text):
                        break
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Say 'exit' to quit.[/yellow]")


# CLI Commands
@app.command()
def interactive(
    voice: bool = typer.Option(True, "--voice/--no-voice", help="Use voice input"),
):
    """Start Synapse in interactive mode."""
    synapse = Synapse(use_voice=voice)
    synapse.run_interactive()


@app.command()
def scenarios(
    target: str = typer.Argument(..., help="What to generate scenarios for"),
):
    """Generate test scenarios for a target."""
    synapse = Synapse(use_voice=False)
    synapse._generate_scenarios(target)


@app.command()
def playwright(
    target: str = typer.Argument(..., help="What to generate tests for"),
    scenarios_file: str = typer.Option(None, "--scenarios", "-s", help="Scenarios file to use"),
):
    """Generate Playwright tests."""
    synapse = Synapse(use_voice=False)

    if scenarios_file:
        synapse._generate_from_file(scenarios_file)
    else:
        synapse._init_crew()
        result = synapse.crew.generate_playwright_tests(target)
        synapse.writer.save_playwright_tests(result, target)
        console.print(Panel(result, title="Generated Tests", border_style="green"))


@app.command()
def review(
    filepath: str = typer.Argument(..., help="File to review"),
):
    """Review code in a file."""
    synapse = Synapse(use_voice=False)
    synapse._code_review(filepath)


@app.command()
def outputs():
    """List generated output files."""
    writer = OutputWriter()
    files = writer.list_outputs()

    if not files:
        console.print("[yellow]No output files yet.[/yellow]")
        return

    table = Table(title="Generated Files")
    table.add_column("Name", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Modified")

    for f in files:
        table.add_row(f['name'], f"{f['size']} bytes", f['modified'])

    console.print(table)


# Marker CLI commands
@app.command()
def marker(
    project_path: str = typer.Argument(..., help="Project path to add test IDs"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview changes without applying"),
):
    """Add test IDs to a project via Marker service."""
    synapse = Synapse(use_voice=False)
    if dry_run:
        synapse._marker_preview(project_path)
    else:
        synapse._marker_run(project_path)


@app.command()
def marker_rollback(
    project_path: str = typer.Argument(..., help="Project path to rollback"),
):
    """Rollback Marker changes."""
    synapse = Synapse(use_voice=False)
    synapse._marker_rollback(project_path)


@app.command()
def marker_analyze(
    project_path: str = typer.Argument(..., help="Project path to analyze"),
):
    """Analyze project for test IDs."""
    synapse = Synapse(use_voice=False)
    synapse._marker_analyze(project_path)


if __name__ == "__main__":
    app()
