"""
LangChain skills pattern: progressive disclosure of specialized prompts.
See: https://docs.langchain.com/oss/python/langchain/multi-agent/skills

Skills are loaded from (in order of precedence):
  1. skills/ at project root (LangChain/Deep Agents convention)
  2. .agent/skills/ (legacy / Cursor agent framework skills)
"""
from __future__ import annotations

import re
from pathlib import Path

from langchain_core.tools import tool

from deep_research.config import PROJECT_ROOT

_SKILLS_ROOT = PROJECT_ROOT / "skills"
_AGENT_SKILLS_ROOT = PROJECT_ROOT / ".agent" / "skills"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _skill_dir(name: str) -> Path | None:
    """Resolve skill name to directory. Prefers skills/ then .agent/skills/."""
    norm = name.strip().lower().replace("_", "-")
    for root in (_SKILLS_ROOT, _AGENT_SKILLS_ROOT):
        path = root / norm
        if path.is_dir() and (path / "SKILL.md").is_file():
            return path
    return None


def _parse_frontmatter(skill_md: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from SKILL.md. Returns (metadata_dict, body)."""
    match = _FRONTMATTER_RE.match(skill_md)
    if not match:
        return {}, skill_md
    yaml_block = match.group(1)
    body = skill_md[match.end() :].lstrip()
    metadata = {}
    for line in yaml_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip().lower()] = v.strip().strip('"').strip("'")
    return metadata, body


def _list_skill_metadata() -> list[tuple[str, str]]:
    """Scan skills/ and .agent/skills/ for SKILL.md; return (name, description)."""
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for root in (_SKILLS_ROOT, _AGENT_SKILLS_ROOT):
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if not path.is_dir():
                continue
            md_file = path / "SKILL.md"
            if not md_file.is_file():
                continue
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                meta, _ = _parse_frontmatter(text)
                name = meta.get("name") or path.name
                if name in seen:
                    continue
                seen.add(name)
                desc = meta.get("description", "(No description)")
                result.append((name, desc))
            except Exception:
                continue
    return sorted(result, key=lambda x: x[0])


@tool
def list_skills() -> str:
    """List available skills (name and short description).

    Use this to see which skills you can load. When a user task matches a skill's
    description, call load_skill(skill_name) to load that skill's full instructions.
    """
    items = _list_skill_metadata()
    if not items:
        return "No skills found. Skills live under skills/<skill_name>/SKILL.md (or .agent/skills/)."
    lines = ["Available skills (use load_skill(skill_name) to load full instructions):"]
    for name, desc in items:
        lines.append(f"- **{name}**: {desc}")
    return "\n".join(lines)


@tool
def load_skill(skill_name: str) -> str:
    """Load a skill's full instructions by name (progressive disclosure).

    Call this when a user request matches a skill you saw in list_skills. You will
    receive the full skill instructions (when to use it, workflow, script usage, etc.).
    Then follow those instructions; they may tell you to use specific tools
    (e.g. generate_research_pdf for the deep-research-pdf skill).

    Args:
        skill_name: The skill identifier, e.g. 'deep-research-pdf'.

    Returns:
        The skill's full markdown instructions, or an error message if not found.
    """
    path = _skill_dir(skill_name)
    if not path:
        available = [n for n, _ in _list_skill_metadata()]
        return (
            f"Skill '{skill_name}' not found. "
            f"Available skills: {', '.join(available) or 'none'}."
        )
    try:
        text = (path / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        _, body = _parse_frontmatter(text)
        return body.strip() or "(Skill has no body content.)"
    except Exception as e:
        return f"Failed to load skill: {e!s}"
