"""
Synapse gRPC Clients
Communicates with Scout, Golem, and Marker microservices
"""

import grpc
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import config

# Import generated protobuf modules (will be generated from .proto files)
try:
    import scout_pb2
    import scout_pb2_grpc
    SCOUT_AVAILABLE = True
except ImportError:
    SCOUT_AVAILABLE = False

try:
    import golem_pb2
    import golem_pb2_grpc
    GOLEM_AVAILABLE = True
except ImportError:
    GOLEM_AVAILABLE = False

try:
    import marker_pb2
    import marker_pb2_grpc
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False


@dataclass
class ServiceResult:
    """Result from a microservice call"""
    success: bool
    data: Dict[str, Any] = None
    error: str = ""


class ScoutClient:
    """gRPC client for Scout - Test Scenario Generator"""

    def __init__(self, host: str = None):
        self.host = host or config.scout_grpc_host
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to Scout service"""
        if not SCOUT_AVAILABLE:
            raise ImportError("Scout protobuf modules not available. Run: python -m grpc_tools.protoc ...")

        self.channel = grpc.insecure_channel(self.host)
        self.stub = scout_pb2_grpc.ScoutServiceStub(self.channel)
        return self

    def close(self):
        """Close the connection"""
        if self.channel:
            self.channel.close()

    def generate_scenarios(
        self,
        project_path: str,
        user: str = "synapse",
        role: str = "tester"
    ) -> ServiceResult:
        """
        Generate test scenarios for a project

        Args:
            project_path: Path to the frontend project
            user: User identifier
            role: Role for scenarios
        """
        try:
            request = scout_pb2.GenerateScenariosRequest(
                project_path=project_path,
                user=user,
                role=role
            )

            response = self.stub.GenerateScenarios(request)

            return ServiceResult(
                success=response.success,
                data={
                    "output_path": response.output_path,
                    "scenarios_count": response.scenarios_count,
                    "components_count": response.components_count
                },
                error=response.error if not response.success else ""
            )

        except grpc.RpcError as e:
            return ServiceResult(
                success=False,
                error=f"gRPC error: {e.code()} - {e.details()}"
            )

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class GolemClient:
    """gRPC client for Golem - Test Generator"""

    def __init__(self, host: str = None):
        self.host = host or config.golem_grpc_host
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to Golem service"""
        if not GOLEM_AVAILABLE:
            raise ImportError("Golem protobuf modules not available")

        self.channel = grpc.insecure_channel(self.host)
        self.stub = golem_pb2_grpc.GolemServiceStub(self.channel)
        return self

    def close(self):
        """Close the connection"""
        if self.channel:
            self.channel.close()

    def generate_tests(
        self,
        scenarios_path: str,
        framework: str = "playwright",
        language: str = "python",
        base_url: str = ""
    ) -> ServiceResult:
        """
        Generate tests from scenarios

        Args:
            scenarios_path: Path to scenarios JSON file
            framework: Test framework (playwright, robot, cypress, selenium)
            language: Programming language (python, typescript)
            base_url: Base URL for tests
        """
        try:
            request = golem_pb2.GenerateTestsRequest(
                scenarios_path=scenarios_path,
                framework=framework,
                language=language,
                base_url=base_url
            )

            response = self.stub.GenerateTests(request)

            return ServiceResult(
                success=response.success,
                data={
                    "output_dir": response.output_dir,
                    "files_count": response.files_count,
                    "tests_count": response.tests_count
                },
                error=response.error if not response.success else ""
            )

        except grpc.RpcError as e:
            return ServiceResult(
                success=False,
                error=f"gRPC error: {e.code()} - {e.details()}"
            )

    def run_tests(
        self,
        test_dir: str,
        base_url: str = "",
        headed: bool = False,
        browser: str = "chromium"
    ) -> ServiceResult:
        """
        Run generated tests

        Args:
            test_dir: Directory with test files
            base_url: Base URL for tests
            headed: Run in headed mode
            browser: Browser to use
        """
        try:
            request = golem_pb2.RunTestsRequest(
                test_dir=test_dir,
                base_url=base_url,
                headed=headed,
                browser=browser
            )

            response = self.stub.RunTests(request)

            return ServiceResult(
                success=response.success,
                data={
                    "tests_run": response.tests_run,
                    "tests_passed": response.tests_passed,
                    "tests_failed": response.tests_failed,
                    "output": response.output
                },
                error=response.error if not response.success else ""
            )

        except grpc.RpcError as e:
            return ServiceResult(
                success=False,
                error=f"gRPC error: {e.code()} - {e.details()}"
            )

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MarkerClient:
    """gRPC client for Marker - Test ID Generator"""

    def __init__(self, host: str = None):
        self.host = host or config.marker_grpc_host
        self.channel = None
        self.stub = None

    def connect(self):
        """Establish connection to Marker service"""
        if not MARKER_AVAILABLE:
            raise ImportError("Marker protobuf modules not available")

        self.channel = grpc.insecure_channel(self.host)
        self.stub = marker_pb2_grpc.MarkerServiceStub(self.channel)
        return self

    def close(self):
        """Close the connection"""
        if self.channel:
            self.channel.close()

    def add_test_ids(
        self,
        project_path: str,
        dry_run: bool = False,
        file_filter: str = ""
    ) -> ServiceResult:
        """
        Add data-testid attributes to project

        Args:
            project_path: Path to the frontend project
            dry_run: Preview changes without writing
            file_filter: Filter files by name pattern
        """
        try:
            request = marker_pb2.AddTestIdsRequest(
                project_path=project_path,
                dry_run=dry_run,
                file_filter=file_filter
            )

            response = self.stub.AddTestIds(request)

            return ServiceResult(
                success=response.success,
                data={
                    "files_processed": response.files_processed,
                    "ids_added": response.ids_added
                },
                error=response.error if not response.success else ""
            )

        except grpc.RpcError as e:
            return ServiceResult(
                success=False,
                error=f"gRPC error: {e.code()} - {e.details()}"
            )

    def rollback(self, project_path: str) -> ServiceResult:
        """Rollback to backup"""
        try:
            request = marker_pb2.RollbackRequest(project_path=project_path)
            response = self.stub.Rollback(request)

            return ServiceResult(
                success=response.success,
                data={"files_restored": response.files_restored},
                error=response.error if not response.success else ""
            )

        except grpc.RpcError as e:
            return ServiceResult(
                success=False,
                error=f"gRPC error: {e.code()} - {e.details()}"
            )

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions
def get_scout_client() -> ScoutClient:
    """Get a Scout client instance"""
    return ScoutClient()


def get_golem_client() -> GolemClient:
    """Get a Golem client instance"""
    return GolemClient()


def get_marker_client() -> MarkerClient:
    """Get a Marker client instance"""
    return MarkerClient()
