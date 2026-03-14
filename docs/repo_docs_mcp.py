#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def list_architecture_docs() -> list[str]:
    return sorted(str(path.relative_to(ROOT.parent)) for path in ROOT.glob("*.md"))


def read_section(path: Path, heading: str | None = None) -> str:
    content = path.read_text()
    if heading is None:
        return content
    marker = f"## {heading}"
    if marker not in content:
        return ""
    _, tail = content.split(marker, 1)
    next_heading = tail.find("\n## ")
    return tail[:next_heading].strip() if next_heading != -1 else tail.strip()


def handle(request: dict) -> dict:
    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {
            "tools": [
                {"name": "list_architecture_docs", "description": "List markdown docs in docs/."},
                {"name": "read_prd_section", "description": "Read a section from docs/prd.md."},
                {"name": "read_api_contract", "description": "Read docs/api-contracts.md."},
                {"name": "read_demo_script", "description": "Read docs/demo-script.md."},
            ]
        }

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name == "list_architecture_docs":
            return {"content": [{"type": "text", "text": json.dumps(list_architecture_docs())}]}
        if name == "read_prd_section":
            section = arguments.get("section")
            text = read_section(ROOT / "prd.md", section)
            return {"content": [{"type": "text", "text": text}]}
        if name == "read_api_contract":
            text = (ROOT / "api-contracts.md").read_text()
            return {"content": [{"type": "text", "text": text}]}
        if name == "read_demo_script":
            text = (ROOT / "demo-script.md").read_text()
            return {"content": [{"type": "text", "text": text}]}
    return {"error": {"message": f"Unsupported request: {method}"}}


def main() -> None:
    for raw in iter(input, ""):
        request = json.loads(raw)
        print(json.dumps(handle(request)), flush=True)


if __name__ == "__main__":
    main()

