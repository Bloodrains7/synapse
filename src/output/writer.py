"""
Output Writer Module
Handles saving generated content to files
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class OutputWriter:
    """Handles writing generated content to files."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Convert name to valid filename."""
        # Remove special characters
        name = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces with underscores
        name = re.sub(r'\s+', '_', name)
        # Convert to lowercase
        return name.lower()[:50]

    def _get_timestamp(self) -> str:
        """Get timestamp for unique filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def save_scenarios(self, content: str, name: str) -> Path:
        """Save Gherkin scenarios to .feature file."""
        filename = f"{self._sanitize_filename(name)}.feature"
        filepath = self.output_dir / filename

        # Extract just the feature content if wrapped in markdown
        content = self._extract_code_block(content, "gherkin")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]Scenarios saved to: {filepath}[/green]")
        return filepath

    def save_playwright_tests(self, content: str, name: str) -> Path:
        """Save Playwright tests to .spec.ts file."""
        filename = f"{self._sanitize_filename(name)}.spec.ts"
        filepath = self.output_dir / filename

        # Extract TypeScript code if wrapped in markdown
        content = self._extract_code_block(content, "typescript")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]Playwright tests saved to: {filepath}[/green]")
        return filepath

    def save_review(self, content: str, name: str) -> Path:
        """Save code review to markdown file."""
        filename = f"{self._sanitize_filename(name)}_review.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Code Review: {name}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(content)

        console.print(f"[green]Review saved to: {filepath}[/green]")
        return filepath

    def save_full_suite(self, results: dict, name: str) -> dict:
        """Save complete test suite (scenarios, tests, review)."""
        paths = {}

        if results.get('scenarios'):
            paths['scenarios'] = self.save_scenarios(results['scenarios'], name)

        if results.get('playwright_tests'):
            paths['tests'] = self.save_playwright_tests(results['playwright_tests'], name)

        if results.get('review'):
            paths['review'] = self.save_review(results['review'], name)

        return paths

    def _extract_code_block(self, content: str, language: str) -> str:
        """Extract code from markdown code blocks."""
        # Pattern for code blocks
        patterns = [
            rf"```{language}\n(.*?)```",
            rf"```{language.lower()}\n(.*?)```",
            r"```\n(.*?)```",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()

        # If no code block found, return original content
        return content.strip()

    def list_outputs(self) -> list:
        """List all generated output files."""
        files = []
        for f in self.output_dir.iterdir():
            if f.is_file():
                files.append({
                    'name': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def read_file(self, filename: str) -> Optional[str]:
        """Read a file from output directory."""
        filepath = self.output_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None
