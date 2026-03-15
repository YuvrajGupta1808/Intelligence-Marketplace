# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in the **`deep_research`** package (production-style layout). Root `agent.py`, `api.py`, and `app.py` are thin entry points that delegate to `deep_research.agent`, `deep_research.api`, and the same Streamlit app (which imports the agent from `deep_research.agent`). The package contains:

- **`deep_research/agent.py`** — Research graph (create_deep_agent, sub-agents, tools).
- **`deep_research/api.py`** — FastAPI app: `/health`, `POST /research_report`.
- **`deep_research/prompts.py`** — Orchestrator and sub-agent system prompts.
- **`deep_research/tools/`** — Chart, researcher (Yahoo), think, Unbrowse, EXA, PDF, skills, Yahoo MCP tools.

Supporting docs are in `docs/`, generated artifacts in `output/`.

## Build, Test, and Development Commands
Use `uv` for local setup and execution.

- `uv sync`: install project dependencies from [`pyproject.toml`](/Users/pramodthebe/Desktop/deep-finance-research/pyproject.toml).
- `./run.sh --unbrowse`: start the LangGraph backend with Unbrowse, which this app requires at startup.
- `uv run --group dev langgraph dev`: run the `research` graph from [`langgraph.json`](/Users/pramodthebe/Desktop/deep-finance-research/langgraph.json).
- `uv run uvicorn api:app --reload --port 8000`: run the FastAPI research-report API locally.

## Coding Style & Naming Conventions
Target Python 3.11+ with 4-space indentation and explicit, small modules in `deep_research/`. Follow existing naming: `snake_case` for functions and variables, `PascalCase` for classes, and concise docstrings in Google style. Run `uv run ruff check .` before opening a PR; Ruff enforces imports, pycodestyle, pyflakes, and pydocstyle rules. Keep new files ASCII unless the file already uses Unicode.

## Commit & Pull Request Guidelines
Recent history uses short, lowercase summaries such as `added uv deps` and `updated readme`. Keep commits focused, imperative or action-oriented, and scoped to one change. PRs should describe the behavior change, list verification commands you ran, link related issues, and include screenshots or sample responses when modifying `app.py`, API output, or report rendering.

## Security & Configuration Tips
Store secrets in `.env`; do not commit API keys or generated credentials. Unbrowse must be running before backend startup.
