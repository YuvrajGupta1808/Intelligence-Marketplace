"""Thin Python wrapper for Metaplex Agent Registry scripts (8004-solana)."""

import os
import subprocess
import sys
from pathlib import Path


def _metaplex_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "metaplex-scripts"


def _run(cmd: list[str]) -> int:
    env = os.environ.copy()
    env.setdefault("PATH", os.defpath)
    return subprocess.call(
        ["npm", "run", cmd[0]],
        cwd=_metaplex_dir(),
        env=env,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m langgraph_agent.metaplex register|verify")
        print("  register - Register agent on 8004 Agent Registry")
        print("  verify   - Verify registration (requires AGENT_ASSET)")
        sys.exit(1)
    action = sys.argv[1].lower()
    if action == "register":
        sys.exit(_run(["register"]))
    if action == "verify":
        sys.exit(_run(["verify"]))
    print(f"Unknown action: {action}")
    sys.exit(1)


if __name__ == "__main__":
    main()
