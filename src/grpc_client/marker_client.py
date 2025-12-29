"""
Marker gRPC Client
Connects to Marker service for test ID generation
"""
import os
import sys
from pathlib import Path
from typing import Callable, Optional
import grpc
from rich.console import Console

console = Console()

# Compile proto on import if needed
def _ensure_proto_compiled():
    """Ensure proto files are compiled."""
    proto_dir = Path(__file__).parent.parent.parent / "proto"
    output_dir = Path(__file__).parent

    pb2_file = output_dir / "marker_pb2.py"

    # Check if already compiled
    if pb2_file.exists():
        return True

    try:
        from grpc_tools import protoc

        proto_file = proto_dir / "marker.proto"
        if not proto_file.exists():
            console.print(f"[red]Proto file not found: {proto_file}[/red]")
            return False

        # Compile proto
        result = protoc.main([
            'grpc_tools.protoc',
            f'-I{proto_dir}',
            f'--python_out={output_dir}',
            f'--grpc_python_out={output_dir}',
            str(proto_file)
        ])

        if result != 0:
            console.print("[red]Failed to compile proto file[/red]")
            return False

        # Fix import in grpc file
        grpc_file = output_dir / "marker_pb2_grpc.py"
        if grpc_file.exists():
            content = grpc_file.read_text()
            content = content.replace(
                "import marker_pb2",
                "from . import marker_pb2"
            )
            grpc_file.write_text(content)

        console.print("[green]Proto files compiled successfully[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Error compiling proto: {e}[/red]")
        return False


class MarkerClient:
    """Client for Marker gRPC service."""

    def __init__(self, host: str = None, port: int = None):
        """Initialize client with server address."""
        self.host = host or os.getenv("MARKER_GRPC_HOST", "localhost")
        self.port = port or int(os.getenv("MARKER_GRPC_PORT", "50051"))
        self.address = f"{self.host}:{self.port}"
        self.channel = None
        self.stub = None

        # Ensure proto is compiled
        _ensure_proto_compiled()

        # Import generated modules
        try:
            from . import marker_pb2
            from . import marker_pb2_grpc
            self._pb2 = marker_pb2
            self._pb2_grpc = marker_pb2_grpc
        except ImportError as e:
            console.print(f"[red]Failed to import proto modules: {e}[/red]")
            console.print("[yellow]Run: python -m grpc_tools.protoc -Iproto --python_out=src/grpc_client --grpc_python_out=src/grpc_client proto/marker.proto[/yellow]")
            raise

    def connect(self) -> bool:
        """Connect to Marker server."""
        try:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = self._pb2_grpc.MarkerServiceStub(self.channel)

            # Test connection with analyze (lightweight call)
            console.print(f"[dim]Connecting to Marker service at {self.address}...[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to connect: {e}[/red]")
            return False

    def disconnect(self):
        """Disconnect from server."""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None

    def run_marker(
        self,
        project_path: str,
        dry_run: bool = False,
        file_filter: str = "",
        target_elements: list = None
    ) -> dict:
        """Run marker on a project."""
        if not self.stub:
            self.connect()

        request = self._pb2.RunMarkerRequest(
            project_path=project_path,
            dry_run=dry_run,
            file_filter=file_filter,
            target_elements=target_elements or []
        )

        try:
            response = self.stub.RunMarker(request)
            return {
                "success": response.success,
                "files_processed": response.files_processed,
                "ids_added": response.ids_added,
                "duplicate_ids": list(response.duplicate_ids),
                "error_message": response.error_message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error_message": f"gRPC error: {e.details()}"
            }

    def preview_changes(self, project_path: str, file_filter: str = "") -> dict:
        """Preview changes without applying."""
        if not self.stub:
            self.connect()

        request = self._pb2.PreviewRequest(
            project_path=project_path,
            file_filter=file_filter
        )

        try:
            response = self.stub.PreviewChanges(request)
            previews = []
            for p in response.previews:
                previews.append({
                    "file_path": p.file_path,
                    "potential_ids": p.potential_ids,
                    "elements": [
                        {"element_type": e.element_type, "test_id": e.test_id, "preview": e.preview}
                        for e in p.elements
                    ]
                })

            return {
                "success": response.success,
                "files_found": response.files_found,
                "potential_ids": response.potential_ids,
                "previews": previews,
                "error_message": response.error_message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error_message": f"gRPC error: {e.details()}"
            }

    def rollback(self, project_path: str) -> dict:
        """Rollback last changes."""
        if not self.stub:
            self.connect()

        request = self._pb2.RollbackRequest(project_path=project_path)

        try:
            response = self.stub.Rollback(request)
            return {
                "success": response.success,
                "files_restored": response.files_restored,
                "restored_files": list(response.restored_files),
                "error_message": response.error_message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error_message": f"gRPC error: {e.details()}"
            }

    def analyze_project(self, project_path: str) -> dict:
        """Analyze project structure."""
        if not self.stub:
            self.connect()

        request = self._pb2.AnalyzeRequest(project_path=project_path)

        try:
            response = self.stub.AnalyzeProject(request)
            files = []
            for f in response.files:
                files.append({
                    "path": f.path,
                    "component_name": f.component_name,
                    "file_type": f.file_type,
                    "existing_ids": f.existing_ids,
                    "elements_without_ids": f.elements_without_ids
                })

            return {
                "success": response.success,
                "total_files": response.total_files,
                "files": files,
                "file_types": dict(response.file_types),
                "error_message": response.error_message
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error_message": f"gRPC error: {e.details()}"
            }

    def run_marker_stream(
        self,
        project_path: str,
        callback: Callable[[dict], None] = None,
        dry_run: bool = False,
        file_filter: str = ""
    ):
        """Run marker with streaming progress updates."""
        if not self.stub:
            self.connect()

        request = self._pb2.RunMarkerRequest(
            project_path=project_path,
            dry_run=dry_run,
            file_filter=file_filter
        )

        try:
            for update in self.stub.RunMarkerStream(request):
                progress = {
                    "file_path": update.file_path,
                    "status": update.status,
                    "ids_added": update.ids_added,
                    "message": update.message,
                    "progress_percent": update.progress_percent
                }

                if callback:
                    callback(progress)
                else:
                    console.print(f"[dim]{progress['progress_percent']:.0f}%[/dim] {progress['file_path']}: {progress['status']}")

        except grpc.RpcError as e:
            console.print(f"[red]Stream error: {e.details()}[/red]")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
