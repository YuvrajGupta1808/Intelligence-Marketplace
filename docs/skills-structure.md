# Agent skills structure (LangChain convention)

This project uses the **LangChain skills pattern** for progressive disclosure: the agent discovers skills via `list_skills` and loads full instructions with `load_skill(skill_name)`.

## Required layout

Skills follow the layout expected by LangChain and the [Agent Skills specification](https://agentskills.io/specification):

```
<project-root>/
└── skills/                    # LangChain-expected location
    └── <skill-name>/
        ├── SKILL.md           # Required: frontmatter + instructions
        └── scripts/           # Optional: scripts referenced in SKILL.md
            └── ...
```

- **`skills/`** at the project root is the standard place for agent skills. The loader in `deep_research.tools.skill_tools` reads from here.
- Each skill is a **directory** whose name is the skill id (e.g. `deep-research-pdf`).
- Every skill directory must contain **`SKILL.md`** with:
  - **YAML frontmatter** (between `---` lines) with at least:
    - `name`: skill identifier (e.g. `deep-research-pdf`)
    - `description`: short description used for matching and listing
  - **Body**: full instructions the agent receives when it calls `load_skill(skill_name)`.

Optional: scripts, templates, or other files referenced in `SKILL.md` can live inside the same skill directory (e.g. `scripts/markdown_report_to_pdf.py`).

## How the agent uses skills

1. **List**: The agent calls the `list_skills` tool and sees (name, description) for each available skill.
2. **Load**: When a task matches a skill, the agent calls `load_skill(skill_name)` and gets the full markdown body of that skill’s `SKILL.md`.
3. **Execute**: The agent follows the skill’s instructions, which may tell it to call specific tools (e.g. `generate_research_pdf`).

References:

- [LangChain multi-agent skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
- [Deep Agents skills](https://docs.langchain.com/oss/python/deepagents/skills) (when using the `skills` parameter with a file backend)

## Skills in this repo

| Location        | Purpose |
|----------------|--------|
| **`skills/`**   | Finance-agent skills (e.g. `deep-research-pdf`). This is the canonical LangChain layout. |
