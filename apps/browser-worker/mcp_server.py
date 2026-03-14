#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.browser.runner import BrowserRunner
from app.storage.local import LocalArtifactStorage


ROOT = Path(__file__).resolve().parent


async def open_page(url: str) -> dict[str, str]:
    storage = LocalArtifactStorage(ROOT / "artifacts", "http://localhost:8002/artifacts")
    runner = BrowserRunner()
    result = await runner.capture(url, "mcp-preview", storage)
    return {"final_url": result["final_url"]}


async def take_screenshot(url: str, output_path: str) -> dict[str, str]:
    storage = LocalArtifactStorage(Path(output_path).parent, "file://artifacts")
    runner = BrowserRunner()
    await runner.capture(url, Path(output_path).stem, storage)
    return {"output_path": output_path}


async def extract_visible_text(url: str) -> dict[str, str]:
    storage = LocalArtifactStorage(ROOT / "artifacts", "http://localhost:8002/artifacts")
    runner = BrowserRunner()
    result = await runner.capture(url, "mcp-text", storage)
    return {"text": result["visible_text"]}


async def save_html(url: str, output_path: str) -> dict[str, str]:
    storage = LocalArtifactStorage(Path(output_path).parent, "file://artifacts")
    runner = BrowserRunner()
    result = await runner.capture(url, Path(output_path).stem, storage)
    Path(output_path).write_text(result["html"])
    return {"output_path": output_path}


async def run_fixture_task(task_json: dict) -> dict:
    return {"received": task_json}


async def handle(request: dict) -> dict:
    method = request.get("method")
    params = request.get("params", {})
    if method == "tools/list":
        return {
            "tools": [
                {"name": "open_page", "description": "Open a page and report final URL."},
                {"name": "take_screenshot", "description": "Take a screenshot into an output path."},
                {"name": "extract_visible_text", "description": "Extract visible body text."},
                {"name": "save_html", "description": "Save page HTML to disk."},
                {"name": "run_fixture_task", "description": "Return a deterministic fixture task payload."},
            ]
        }
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        func = globals()[name]
        result = await func(**arguments)
        return {"content": [{"type": "text", "text": json.dumps(result)}]}
    return {"error": {"message": f"Unsupported request: {method}"}}


def main() -> None:
    for raw in iter(input, ""):
        request = json.loads(raw)
        print(json.dumps(asyncio.run(handle(request))), flush=True)


if __name__ == "__main__":
    main()

