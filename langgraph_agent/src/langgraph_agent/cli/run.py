"""CLI entrypoint: load env, build graph, invoke with query and print final answer."""

import argparse
import os
import sys
from pathlib import Path

# Load .env from current dir or repo root
try:
    from dotenv import load_dotenv
    load_dotenv()
    _cwd = Path.cwd()
    if (_cwd / ".env").exists():
        load_dotenv(_cwd / ".env")
    for d in (Path(__file__).resolve().parents[3], Path(__file__).resolve().parents[4]):
        if (d / ".env").exists():
            load_dotenv(d / ".env")
            break
except ImportError:
    pass

from langgraph_agent import create_plan_execute_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan-and-execute agent with web search")
    parser.add_argument("query", nargs="*", help="User goal (one string). If omitted, read from stdin.")
    parser.add_argument("--model", default=None, help="OpenAI model (default: gpt-4o-mini)")
    parser.add_argument("--stream", action="store_true", help="Stream final answer (future)")
    args = parser.parse_args()

    query = " ".join(args.query).strip() if args.query else sys.stdin.read().strip()
    if not query:
        print("Usage: python -m langgraph_agent.run 'Your question or goal'", file=sys.stderr)
        return 1

    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in the environment or in .env", file=sys.stderr)
        return 1

    graph = create_plan_execute_graph(model=args.model or os.getenv("OPENAI_MODEL"))
    result = graph.invoke({"query": query})
    answer = result.get("final_answer", "")
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
