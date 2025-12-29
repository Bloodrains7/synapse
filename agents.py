"""
Synapse AI Agents
Tool handlers for test automation using gRPC services
"""

from typing import Dict, Any
import json

from config import config
from grpc_clients import ScoutClient, GolemClient, MarkerClient


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

def generate_scenarios(project_path: str) -> Dict[str, Any]:
    """Generate test scenarios using Scout"""
    try:
        with ScoutClient() as client:
            result = client.generate_scenarios(project_path)
            if result.success:
                return {
                    "status": "success",
                    "message": f"Generated {result.data['scenarios_count']} scenarios",
                    "output_path": result.data["output_path"],
                    "scenarios_count": result.data["scenarios_count"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def generate_tests(
    scenarios_path: str,
    framework: str = "playwright",
    base_url: str = ""
) -> Dict[str, Any]:
    """Generate tests using Golem"""
    try:
        with GolemClient() as client:
            result = client.generate_tests(scenarios_path, framework, "python", base_url)
            if result.success:
                return {
                    "status": "success",
                    "message": f"Generated {result.data['tests_count']} tests",
                    "output_dir": result.data["output_dir"],
                    "tests_count": result.data["tests_count"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_tests(
    test_dir: str,
    base_url: str = "",
    headed: bool = False
) -> Dict[str, Any]:
    """Run tests using Golem"""
    try:
        with GolemClient() as client:
            result = client.run_tests(test_dir, base_url, headed)
            if result.success:
                passed = result.data["tests_passed"]
                failed = result.data["tests_failed"]
                total = result.data["tests_run"]
                return {
                    "status": "success",
                    "message": f"Tests completed: {passed}/{total} passed, {failed} failed",
                    "tests_run": total,
                    "tests_passed": passed,
                    "tests_failed": failed
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def add_test_ids(project_path: str) -> Dict[str, Any]:
    """Add test IDs using Marker"""
    try:
        with MarkerClient() as client:
            result = client.add_test_ids(project_path)
            if result.success:
                return {
                    "status": "success",
                    "message": f"Added {result.data['ids_added']} test IDs to {result.data['files_processed']} files",
                    "files_processed": result.data["files_processed"],
                    "ids_added": result.data["ids_added"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# TOOL HANDLER
# =============================================================================

def handle_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """
    Handle a tool call from the Gemini model.

    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool

    Returns:
        JSON string with the result
    """
    tools = {
        "generate_scenarios": lambda a: generate_scenarios(a.get("project_path", "")),
        "generate_tests": lambda a: generate_tests(
            a.get("scenarios_path", ""),
            a.get("framework", "playwright"),
            a.get("base_url", "")
        ),
        "run_tests": lambda a: run_tests(
            a.get("test_dir", ""),
            a.get("base_url", ""),
            a.get("headed", False)
        ),
        "add_test_ids": lambda a: add_test_ids(a.get("project_path", ""))
    }

    if tool_name in tools:
        result = tools[tool_name](args)
        return json.dumps(result, indent=2)
    else:
        return json.dumps({"status": "error", "error": f"Unknown tool: {tool_name}"})


# =============================================================================
# TEXT MODE COMMAND PROCESSOR
# =============================================================================

class CommandProcessor:
    """Simple command processor for text mode"""

    def __init__(self):
        try:
            from google import genai
            self.client = genai.Client(api_key=config.google_api_key)
            self.model = config.gemini_text_model
        except ImportError:
            self.client = None
            self.model = None

    def process_command(self, command: str) -> str:
        """Process a text command and return result"""
        if not self.client:
            return "Error: google-genai package not installed"

        # Use Gemini to parse the command
        prompt = f"""Parse this test automation command and extract the intent and parameters.

Command: "{command}"

Return a JSON object with:
- intent: one of [generate_scenarios, generate_tests, run_tests, add_test_ids, unknown]
- project_path: path if mentioned
- scenarios_path: scenarios file path if mentioned
- test_dir: test directory if mentioned
- base_url: URL if mentioned
- framework: playwright/robot/cypress/selenium (default: playwright)
- headed: true/false (default: false)

Intent mapping:
- "vygeneruj scenare", "generate scenarios" -> generate_scenarios
- "vygeneruj testy", "generate tests" -> generate_tests
- "spusti testy", "run tests" -> run_tests
- "pridaj test id", "add test ids" -> add_test_ids

Return ONLY the JSON object."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            # Parse the response
            import re
            text = response.text
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(text)

            intent = parsed.get("intent", "unknown")

            # Execute the appropriate tool
            if intent == "generate_scenarios":
                project_path = parsed.get("project_path")
                if not project_path:
                    return "Error: Project path not specified"
                result = generate_scenarios(project_path)
                return self._format_result("Generate Scenarios", result)

            elif intent == "generate_tests":
                scenarios_path = parsed.get("scenarios_path")
                if not scenarios_path:
                    return "Error: Scenarios path not specified"
                result = generate_tests(
                    scenarios_path,
                    parsed.get("framework", "playwright"),
                    parsed.get("base_url", "")
                )
                return self._format_result("Generate Tests", result)

            elif intent == "run_tests":
                test_dir = parsed.get("test_dir")
                if not test_dir:
                    return "Error: Test directory not specified"
                result = run_tests(
                    test_dir,
                    parsed.get("base_url", ""),
                    parsed.get("headed", False)
                )
                return self._format_result("Run Tests", result)

            elif intent == "add_test_ids":
                project_path = parsed.get("project_path")
                if not project_path:
                    return "Error: Project path not specified"
                result = add_test_ids(project_path)
                return self._format_result("Add Test IDs", result)

            else:
                return f"""Unknown command: {intent}

Supported commands:
- Generate scenarios for [project path]
- Generate tests from [scenarios path]
- Run tests in [test directory]
- Add test IDs to [project path]"""

        except Exception as e:
            return f"Error processing command: {e}"

    def _format_result(self, action: str, result: Dict[str, Any]) -> str:
        """Format the result for display"""
        if result.get("status") == "success":
            output = f"{action} - SUCCESS\n"
            output += f"  {result.get('message', '')}\n"
            for key, value in result.items():
                if key not in ["status", "message"]:
                    output += f"  {key}: {value}\n"
            return output
        else:
            return f"{action} - ERROR\n  {result.get('error', 'Unknown error')}"


# For backwards compatibility
class SynapseCrew:
    """Wrapper for command processing"""

    def __init__(self):
        self.processor = CommandProcessor()

    def process_command(self, voice_text: str) -> str:
        print(f"\n{'='*60}")
        print(f"Processing command: {voice_text}")
        print('='*60)
        return self.processor.process_command(voice_text)
