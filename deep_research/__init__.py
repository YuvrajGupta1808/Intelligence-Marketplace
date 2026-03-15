"""
Deep Finance Research — production package for the research agent, API, and tools.
"""
from pathlib import Path

# Project (repository) root for skills, output, chroma paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

__all__ = ["PROJECT_ROOT"]
