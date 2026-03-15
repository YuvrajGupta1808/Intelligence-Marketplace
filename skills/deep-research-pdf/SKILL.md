---
name: deep-research-pdf
description: "Generate a PDF from the deep finance research agent's output. Use when research is complete and the user wants a downloadable PDF report—e.g. from /final_report.md, from the last assistant message content, or from a Markdown string. Handles Morningstar-style sections (Overview, Key Metrics, SEC/External Insights, Price Chart, Valuation & Risks, Sources) and optional chart images."
---

# Deep Research PDF

Generate a PDF from the deep agent's research report (Markdown). Use **after** the financial research agent has produced a full report.

**Integration:** This skill is loaded via the LangChain skills pattern. The orchestrator has **list_skills** and **load_skill** tools; when the user asks for a PDF, the agent calls **load_skill("deep-research-pdf")** to get these instructions, then follows them. The actual PDF is produced by the **generate_research_pdf** tool (report content or path, output path, optional chart images). See: https://docs.langchain.com/oss/python/langchain/multi-agent/skills

## When to use

- The orchestrator **always** invokes this skill at the end of every full company/ticker report (after presenting the 17-section report).
- User asks for a PDF of the research, or to "download the report as PDF".
- Research is done and output exists as Markdown (e.g. `/final_report.md`, last response content, or a saved `.md` file).
- You need a single, shareable PDF with the report sections and optional chart images.

## Inputs

1. **Markdown content**: Path to a `.md` file (e.g. `/final_report.md`) or the report text as a string.
2. **Optional**: Paths to chart images (e.g. exported Plotly charts) to embed in order after the "Price Chart" section or at the end.

## Workflow

1. **Obtain report Markdown**
   - Prefer passing the **full report markdown string** (the same text you are presenting to the user) as report_content_or_path, so the PDF is generated from the exact report content without relying on a file path.
   - If the agent wrote to `/final_report.md`, you may use that path (or the workspace path where it was saved).
   - If the report is in the chat/last response, use that Markdown string as the report content.

2. **Call the generate_research_pdf tool**
   - Use the **generate_research_pdf** tool with: report_content_or_path (the Markdown string or path to the .md file), output_path (e.g. `output/research_report.pdf` or `output/MSFT_research.pdf`), title (optional), and chart_image_paths (optional comma-separated PNG paths if you have chart images).

3. **Return the PDF**
   - Tell the user where the PDF was written and offer to open or attach it.

**Alternative (script):** If you need to run the script directly (e.g. from execute), use: `python skills/deep-research-pdf/scripts/markdown_report_to_pdf.py --input <path_or_stdin> --output <path.pdf> [--title "Title"] [--images img1.png ...]`

## Script usage

```
python skills/deep-research-pdf/scripts/markdown_report_to_pdf.py --input <file.md | -> --output <out.pdf> [--title "Report Title"] [--images img1.png [img2.png ...]]
```

- `--input`: Path to Markdown file, or `-` for stdin.
- `--output`: Path for the generated PDF.
- `--title`: Optional title for the PDF document (default: "Deep Finance Research Report").
- `--images`: Optional list of image paths to append after the body (e.g. price charts).

## Output conventions

- Write PDFs under `output/` in the project (e.g. `output/research_report.pdf`) or a path the user specifies.
- Use a descriptive filename (e.g. `MSFT_research_2025-03-14.pdf`).

## Dependencies

The script uses:

- `markdown` (md→HTML): `uv pip install markdown` if missing.
- `pymupdf` (HTML→PDF): already in project `pyproject.toml`.

Install markdown if needed:

```bash
uv pip install markdown
```

## Quality

- Preserve section hierarchy (## Overview, ## Key Metrics, etc.) with clear headings in the PDF.
- Keep sources and citations readable; no placeholder tokens.
- If chart images are provided, place them in order and add a short caption (e.g. "Price chart") when appropriate.
