"""
Synapse AI Agents with Direct Gemini Integration
No CrewAI dependency - Python 3.14 compatible
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
from rich.console import Console

load_dotenv()

console = Console()


class GeminiClient:
    """Direct Gemini API client."""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        if not api_key or api_key == "your-gemini-api-key-here":
            console.print("[red]Error: GOOGLE_API_KEY not configured in .env[/red]")
            console.print("[yellow]Get your API key from: https://aistudio.google.com/apikey[/yellow]")
            raise ValueError("GOOGLE_API_KEY not configured")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        console.print(f"[green]Gemini model initialized: {model_name}[/green]")

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """Generate response from Gemini."""
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        response = self.model.generate_content(full_prompt)
        return response.text


class ScenarioAgent:
    """Test Scenario Generator Agent."""

    SYSTEM_INSTRUCTION = """You are an expert QA architect with 15 years of experience in software testing.
You specialize in creating thorough test scenarios that cover happy paths, edge cases,
error handling, and security considerations. You write in Gherkin format (Given/When/Then)
and always consider user perspective, accessibility, and real-world usage patterns."""

    def __init__(self, client: GeminiClient):
        self.client = client

    def generate(self, target: str, context: dict = None) -> str:
        """Generate test scenarios for a target."""
        context_str = ""
        if context:
            if context.get('category'):
                context_str += f"\nCategory: {context['category']}"
            if context.get('includes_validation'):
                context_str += "\nInclude validation scenarios"

        prompt = f"""Generate comprehensive test scenarios for: {target}
{context_str}

Requirements:
1. Use Gherkin format (Feature, Scenario, Given/When/Then)
2. Include at least 5-8 scenarios covering:
   - Happy path / main flow
   - Edge cases
   - Error handling
   - Input validation (if applicable)
   - Security considerations (if applicable)
3. Each scenario should be clear and testable
4. Include relevant tags (@smoke, @regression, etc.)
5. Add background section if there's common setup

Output the complete .feature file content."""

        return self.client.generate(prompt, self.SYSTEM_INSTRUCTION)


class PlaywrightAgent:
    """Playwright Test Generator Agent."""

    SYSTEM_INSTRUCTION = """You are a senior automation engineer specializing in Playwright and TypeScript.
You write clean, maintainable, and robust end-to-end tests. You follow Page Object Model patterns,
use proper selectors (preferring data-testid), implement proper waits, handle async operations,
and include meaningful assertions. Your tests are reliable and don't have flaky behavior."""

    def __init__(self, client: GeminiClient):
        self.client = client

    def generate(self, target: str, scenarios: str = None) -> str:
        """Generate Playwright tests for a target."""
        scenario_context = ""
        if scenarios:
            scenario_context = f"\nBased on these scenarios:\n{scenarios}\n"

        prompt = f"""Generate Playwright TypeScript tests for: {target}
{scenario_context}

Requirements:
1. Use TypeScript with Playwright Test
2. Follow Page Object Model pattern when appropriate
3. Use data-testid selectors primarily
4. Include proper imports and test structure
5. Add beforeEach/afterEach hooks as needed
6. Use proper async/await
7. Include meaningful assertions
8. Add comments explaining complex logic
9. Handle loading states and waits properly
10. Group related tests with describe blocks

Output complete, runnable TypeScript test file(s)."""

        return self.client.generate(prompt, self.SYSTEM_INSTRUCTION)


class ReviewAgent:
    """Code Review Agent."""

    SYSTEM_INSTRUCTION = """You are a meticulous code reviewer with deep expertise in test automation.
You check for proper test isolation, clear assertions, maintainability, performance,
and adherence to testing best practices. You provide constructive feedback and suggestions
for improvement."""

    def __init__(self, client: GeminiClient):
        self.client = client

    def review(self, code: str) -> str:
        """Review provided test code."""
        prompt = f"""Review the following test code and provide feedback:

```typescript
{code}
```

Check for:
1. Test isolation and independence
2. Proper assertions
3. Selector best practices
4. Async handling
5. Error handling
6. Code organization
7. Naming conventions
8. Potential flakiness
9. Missing edge cases
10. Performance considerations

Provide:
- Overall quality score (1-10)
- List of issues found
- Suggestions for improvement
- Improved code if needed"""

        return self.client.generate(prompt, self.SYSTEM_INSTRUCTION)


class SynapseCrew:
    """Main orchestrator for Synapse AI agents."""

    def __init__(self):
        self.client = GeminiClient()
        self.scenario_agent = ScenarioAgent(self.client)
        self.playwright_agent = PlaywrightAgent(self.client)
        self.review_agent = ReviewAgent(self.client)

    def generate_scenarios(self, target: str, context: dict = None) -> str:
        """Generate test scenarios for a target."""
        console.print(f"[cyan]Generating scenarios for: {target}[/cyan]")
        result = self.scenario_agent.generate(target, context)
        console.print("[green]Scenarios generated![/green]")
        return result

    def generate_playwright_tests(self, target: str, scenarios: str = None) -> str:
        """Generate Playwright tests."""
        console.print(f"[cyan]Generating Playwright tests for: {target}[/cyan]")
        result = self.playwright_agent.generate(target, scenarios)
        console.print("[green]Playwright tests generated![/green]")
        return result

    def generate_full_suite(self, target: str, context: dict = None) -> dict:
        """Generate scenarios, then Playwright tests, then review."""
        console.print(f"[bold cyan]Full test suite generation for: {target}[/bold cyan]")

        # Step 1: Generate scenarios
        console.print("\n[bold]Step 1: Generating Scenarios[/bold]")
        scenarios = self.scenario_agent.generate(target, context)
        console.print("[green]Scenarios complete![/green]")

        # Step 2: Generate Playwright tests based on scenarios
        console.print("\n[bold]Step 2: Generating Playwright Tests[/bold]")
        playwright_tests = self.playwright_agent.generate(target, scenarios)
        console.print("[green]Playwright tests complete![/green]")

        # Step 3: Review the generated tests
        console.print("\n[bold]Step 3: Code Review[/bold]")
        review = self.review_agent.review(playwright_tests)
        console.print("[green]Review complete![/green]")

        return {
            "scenarios": scenarios,
            "playwright_tests": playwright_tests,
            "review": review,
            "final": f"Generated full test suite for: {target}"
        }

    def review_code(self, code: str) -> str:
        """Review provided code."""
        console.print("[cyan]Reviewing code...[/cyan]")
        result = self.review_agent.review(code)
        console.print("[green]Review complete![/green]")
        return result
