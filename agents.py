"""
Synapse AI Agents
AI agents for voice command processing and test automation using Google Gemini
"""

import google.generativeai as genai
from typing import Dict, Any
import json
import re

from config import config
from grpc_clients import ScoutClient, GolemClient, MarkerClient


# =============================================================================
# GEMINI SETUP
# =============================================================================

def setup_gemini():
    """Configure Gemini API"""
    genai.configure(api_key=config.gemini_api_key)
    return genai.GenerativeModel(config.gemini_model)


# =============================================================================
# TOOLS - Direct service calls
# =============================================================================

def generate_scenarios(project_path: str) -> Dict[str, Any]:
    """Generate test scenarios using Scout"""
    try:
        with ScoutClient() as client:
            result = client.generate_scenarios(project_path)
            if result.success:
                return {
                    "status": "success",
                    "output_path": result.data["output_path"],
                    "scenarios_count": result.data["scenarios_count"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def generate_tests(scenarios_path: str, framework: str = "playwright", base_url: str = "") -> Dict[str, Any]:
    """Generate tests using Golem"""
    try:
        with GolemClient() as client:
            result = client.generate_tests(scenarios_path, framework, "python", base_url)
            if result.success:
                return {
                    "status": "success",
                    "output_dir": result.data["output_dir"],
                    "tests_count": result.data["tests_count"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_tests(test_dir: str, base_url: str = "", headed: bool = False) -> Dict[str, Any]:
    """Run tests using Golem"""
    try:
        with GolemClient() as client:
            result = client.run_tests(test_dir, base_url, headed)
            if result.success:
                return {
                    "status": "success",
                    "tests_run": result.data["tests_run"],
                    "tests_passed": result.data["tests_passed"],
                    "tests_failed": result.data["tests_failed"]
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
                    "files_processed": result.data["files_processed"],
                    "ids_added": result.data["ids_added"]
                }
            else:
                return {"status": "error", "error": result.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# COMMAND PARSER
# =============================================================================

class CommandParser:
    """Parses voice commands using Gemini LLM"""

    def __init__(self):
        self.model = setup_gemini()

    def parse_command(self, command: str) -> Dict[str, Any]:
        """Parse a voice command and extract intent and parameters"""
        prompt = f"""Parse this voice command for a test automation system.

Command: "{command}"

Extract the following information and return ONLY a valid JSON object:
{{
    "intent": "<one of: generate_scenarios, generate_tests, run_tests, add_test_ids, dictate_scenario, unknown>",
    "project_path": "<path if mentioned, otherwise null>",
    "scenarios_path": "<scenarios file path if mentioned, otherwise null>",
    "test_dir": "<test directory if mentioned, otherwise null>",
    "base_url": "<URL if mentioned, otherwise null>",
    "framework": "<playwright, robot, cypress, selenium - default: playwright>",
    "headed": <true or false>,
    "dictation": "<if dictating a scenario, the scenario text, otherwise null>"
}}

Intent mapping:
- "vygeneruj scenare", "generate scenarios", "create scenarios" -> generate_scenarios
- "vygeneruj testy", "generate tests", "create tests" -> generate_tests
- "spusti testy", "run tests", "execute tests" -> run_tests
- "pridaj test id", "add test ids", "mark elements" -> add_test_ids
- "nadiktujem", "dictate scenario", "novy scenar" -> dictate_scenario

Return ONLY the JSON object, no additional text."""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            return {"intent": "unknown", "error": str(e)}

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            # Try parsing the whole response
            return json.loads(response)
        except Exception as e:
            return {"intent": "unknown", "error": f"Parse error: {e}"}


# =============================================================================
# SCENARIO DICTATION
# =============================================================================

class ScenarioDictator:
    """Converts dictated scenarios to structured format using Gemini"""

    def __init__(self):
        self.model = setup_gemini()

    def process_dictation(self, dictation: str, component_name: str = "dictated") -> Dict[str, Any]:
        """Convert dictated scenario to structured format"""
        prompt = f"""Convert this dictated test scenario into a structured JSON format.

Dictation: "{dictation}"

Create a test scenario with this EXACT structure (return ONLY valid JSON):
{{
    "name": "<short descriptive name>",
    "description": "<what the test verifies>",
    "steps": [
        {{
            "action": "<click|fill|verify_visible|verify_text|submit>",
            "selector": "<CSS selector with data-testid>",
            "value": "<value for fill action, otherwise null>",
            "description": "<what this step does>"
        }}
    ]
}}

Guidelines:
- Use data-testid selectors: [data-testid='element-name']
- Actions: click, fill (for inputs), verify_visible, verify_text, submit
- Generate realistic selectors based on the described elements

Return ONLY the JSON object."""

        try:
            response = self.model.generate_content(prompt)
            scenario = self._parse_scenario(response.text)
            return {
                "component": component_name,
                "scenario": scenario
            }
        except Exception as e:
            return {"error": str(e)}

    def _parse_scenario(self, response: str) -> Dict[str, Any]:
        """Extract scenario JSON from response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except Exception:
            return {"error": "Could not parse scenario"}


# =============================================================================
# SYNAPSE CREW - Main Orchestrator
# =============================================================================

class SynapseCrew:
    """Main orchestrator that processes voice commands"""

    def __init__(self):
        self.parser = CommandParser()
        self.dictator = ScenarioDictator()

    def process_command(self, voice_text: str) -> str:
        """Process a voice command and execute the appropriate action"""
        print(f"\n{'='*60}")
        print(f"Processing command: {voice_text}")
        print('='*60)

        # Step 1: Parse the command
        parsed = self.parser.parse_command(voice_text)
        intent = parsed.get("intent", "unknown")

        print(f"Detected intent: {intent}")
        print(f"Parameters: {json.dumps(parsed, indent=2)}")

        # Step 2: Execute based on intent
        if intent == "generate_scenarios":
            project_path = parsed.get("project_path")
            if not project_path:
                return "Error: Project path not specified. Please include the project path in your command."
            result = generate_scenarios(project_path)
            return self._format_result("Generate Scenarios", result)

        elif intent == "generate_tests":
            scenarios_path = parsed.get("scenarios_path")
            if not scenarios_path:
                return "Error: Scenarios path not specified. Please include the scenarios file path."
            result = generate_tests(
                scenarios_path,
                parsed.get("framework", "playwright"),
                parsed.get("base_url", "")
            )
            return self._format_result("Generate Tests", result)

        elif intent == "run_tests":
            test_dir = parsed.get("test_dir")
            if not test_dir:
                return "Error: Test directory not specified. Please include the test directory path."
            result = run_tests(
                test_dir,
                parsed.get("base_url", ""),
                parsed.get("headed", False)
            )
            return self._format_result("Run Tests", result)

        elif intent == "add_test_ids":
            project_path = parsed.get("project_path")
            if not project_path:
                return "Error: Project path not specified. Please include the project path."
            result = add_test_ids(project_path)
            return self._format_result("Add Test IDs", result)

        elif intent == "dictate_scenario":
            dictation = parsed.get("dictation", voice_text)
            result = self.dictator.process_dictation(dictation)
            return json.dumps(result, indent=2, ensure_ascii=False)

        else:
            return f"Unknown command intent: {intent}\n\nSupported commands:\n" \
                   f"- Generate scenarios for [project path]\n" \
                   f"- Generate tests from [scenarios path]\n" \
                   f"- Run tests in [test directory]\n" \
                   f"- Add test IDs to [project path]\n" \
                   f"- Dictate scenario: [your scenario description]"

    def _format_result(self, action: str, result: Dict[str, Any]) -> str:
        """Format the result for display"""
        if result.get("status") == "success":
            output = f"{action} - SUCCESS\n"
            for key, value in result.items():
                if key != "status":
                    output += f"  {key}: {value}\n"
            return output
        else:
            return f"{action} - ERROR\n  {result.get('error', 'Unknown error')}"
