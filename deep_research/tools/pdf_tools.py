"""
PDF generation tools for the deep finance research agent.
Exposes generate_research_pdf as a LangChain tool so the agent can produce a PDF
from the final report when the user asks for it.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from deep_research.config import PROJECT_ROOT

_CANDIDATE_SCRIPTS = [
    PROJECT_ROOT / "skills" / "deep-research-pdf" / "scripts" / "markdown_report_to_pdf.py",
    PROJECT_ROOT / ".agent" / "skills" / "deep-research-pdf" / "scripts" / "markdown_report_to_pdf.py",
]
_SCRIPT_PATH = next((p for p in _CANDIDATE_SCRIPTS if p.is_file()), _CANDIDATE_SCRIPTS[0])


def _run_md_to_pdf(
    input_path: Path,
    output_path: Path,
    title: str = "Deep Finance Research Report",
    image_paths: list[str] | None = None,
) -> str:
    """Run the markdown-to-PDF script. Returns a message string."""
    if not _SCRIPT_PATH.is_file():
        return (
            f"PDF script not found at {_SCRIPT_PATH}. "
            "Ensure the deep-research-pdf skill is present under skills/ or .agent/skills/."
        )
    cmd = [
        sys.executable,
        str(_SCRIPT_PATH),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--title",
        title,
    ]
    if image_paths:
        cmd += ["--images"] + list(image_paths)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return f"PDF generation failed: {result.stderr or result.stdout or 'unknown error'}"
        return f"PDF written to {output_path}"
    except subprocess.TimeoutExpired:
        return "PDF generation timed out."
    except Exception as e:
        return f"PDF generation error: {e!s}"


@tool
def generate_research_pdf(
    report_content_or_path: str,
    output_path: str = "output/research_report.pdf",
    title: str = "Deep Finance Research Report",
    chart_image_paths: str = "",
) -> str:
    """Generate a PDF from the research report (Markdown).

    Use this when the user asks for a PDF of the research, or to download the report as PDF.
    Call after the full report is ready (e.g. after delegating to the research sub-agent and
    receiving the final report).

    Args:
        report_content_or_path: Either the full Markdown content of the report, or a path to
            a .md file (e.g. /final_report.md or the path where the report was saved).
        output_path: Where to write the PDF. Default: output/research_report.pdf
        title: Document title for the PDF. Default: Deep Finance Research Report
        chart_image_paths: Optional comma-separated paths to chart images (e.g. PNGs) to
            append after the report. Leave empty if no charts.

    Returns:
        A message indicating success (path to PDF) or failure (error description).
    """
    content_or_path = (report_content_or_path or "").strip()
    if not content_or_path:
        return "report_content_or_path is required (Markdown content or path to .md file)."

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    images = [p.strip() for p in (chart_image_paths or "").split(",") if p.strip()]

    as_path = Path(content_or_path)
    if content_or_path.startswith("/") or (len(content_or_path) < 400 and as_path.suffix == ".md"):
        if as_path.is_file():
            return _run_md_to_pdf(as_path, out, title=title, image_paths=images or None)
        cwd = Path.cwd()
        rel = content_or_path.lstrip("/")
        if (cwd / rel).is_file():
            return _run_md_to_pdf(cwd / rel, out, title=title, image_paths=images or None)
        # Resolve /final_report.md to project output so API-written report is used
        for candidate in (
            PROJECT_ROOT / "output" / "final_report.md",
            PROJECT_ROOT / "final_report.md",
        ):
            if candidate.is_file():
                return _run_md_to_pdf(candidate, out, title=title, image_paths=images or None)
        # Path not found: avoid treating path string as content (would produce empty PDF)
        if len(content_or_path) < 500 and content_or_path.endswith(".md"):
            return (
                "File not found: pass the full report markdown content as the first argument, "
                "not a path (e.g. use the complete report text you are presenting to the user)."
            )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content_or_path)
        tmp_path = Path(f.name)
    try:
        return _run_md_to_pdf(tmp_path, out, title=title, image_paths=images or None)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
