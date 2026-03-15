"""Thin entrypoint so 'python -m langgraph_agent.run' invokes the CLI."""

from langgraph_agent.cli.run import main

if __name__ == "__main__":
    raise SystemExit(main())
