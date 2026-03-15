"""
Thin entry point for FastAPI: app is defined in deep_research.api.
Run: uv run uvicorn api:app --reload --port 8000
"""
from deep_research.api import app

__all__ = ["app"]
