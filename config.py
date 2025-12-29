"""
Synapse Configuration
Voice Commander for Test Automation Pipeline
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-exp"

    # gRPC Services
    scout_grpc_host: str = "localhost:50051"
    golem_grpc_host: str = "localhost:50052"
    marker_grpc_host: str = "localhost:50053"

    # Voice settings
    voice_language: str = "sk-SK"  # Slovak by default
    voice_timeout: int = 5  # seconds

    # Output
    output_dir: str = "result"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment"""
        config = cls()
        config.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        config.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        config.scout_grpc_host = os.getenv("SCOUT_GRPC_HOST", "localhost:50051")
        config.golem_grpc_host = os.getenv("GOLEM_GRPC_HOST", "localhost:50052")
        config.marker_grpc_host = os.getenv("MARKER_GRPC_HOST", "localhost:50053")
        config.voice_language = os.getenv("VOICE_LANGUAGE", "sk-SK")
        config.output_dir = os.getenv("OUTPUT_DIR", "result")
        return config

    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


config = Config.load()
