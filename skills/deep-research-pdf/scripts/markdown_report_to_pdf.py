#!/usr/bin/env python3
"""
Convert the deep finance research agent's Markdown report to PDF.
Accepts a .md file (or stdin) and optional chart images to append.
Uses markdown (md→HTML) and pymupdf (HTML→PDF). Install: uv pip install markdown
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

try:
    import markdown
except ImportError:
    markdown = None

try:
    import pymupdf
except ImportError:
    pymupdf = None


DEFAULT_CSS = """
body { font-family: serif; font-size: 11pt; line-height: 1.4; margin: 0; padding: 0; }
h1 { font-size: 18pt; margin-top: 12pt; margin-bottom: 6pt; }
h2 { font-size: 14pt; margin-top: 10pt; margin-bottom: 4pt; }
h3 { font-size: 12pt; margin-top: 8pt; margin-bottom: 4pt; }
p { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 6pt 0; padding-left: 24pt; }
strong { font-weight: bold; }
"""

PAGE_MARGIN = 50


def md_to_html(text: str) -> str:
    if markdown is None:
        raise RuntimeError("Install the markdown package: uv pip install markdown")
    html_body = markdown.markdown(text, extensions=["extra", "nl2br"])
    return f"<html><head></head><body>{html_body}</body></html>"


def write_story_to_pdf(html: str, output_path: Path, title: str, user_css: str) -> None:
    if pymupdf is None:
        raise RuntimeError("pymupdf is required; it should be in the project pyproject.toml")
    mediabox = pymupdf.paper_rect("a4")
    where = pymupdf.Rect(
        PAGE_MARGIN,
        PAGE_MARGIN,
        mediabox.width - PAGE_MARGIN,
        mediabox.height - PAGE_MARGIN,
    )
    story = pymupdf.Story(html=html, user_css=user_css)
    writer = pymupdf.DocumentWriter(str(output_path))
    pno = 0

    while True:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        pno += 1
        if not more:
            break

    writer.close()

    # Set metadata (title): open written file, save to final path (avoid incremental save)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    os.rename(str(output_path), tmp_path)
    doc = pymupdf.open(tmp_path)
    doc.set_metadata({"title": title or "Deep Finance Research Report"})
    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def append_image_pages(pdf_path: Path, image_paths: list[Path]) -> None:
    if not image_paths or pymupdf is None:
        return
    mediabox = pymupdf.paper_rect("a4")
    doc = pymupdf.open(str(pdf_path))
    for img_path in image_paths:
        if not img_path.is_file():
            continue
        try:
            img = pymupdf.Pixmap(img_path)
        except Exception:
            continue
        w, h = img.width, img.height
        if w <= 0 or h <= 0:
            continue
        # Scale to fit A4 with margin
        max_w = mediabox.width - 2 * PAGE_MARGIN
        max_h = mediabox.height - 2 * PAGE_MARGIN
        scale = min(max_w / w, max_h / h, 1.0)
        r = pymupdf.Rect(0, 0, w * scale, h * scale)
        r = r + (PAGE_MARGIN, PAGE_MARGIN)
        page = doc.new_page(width=mediabox.width, height=mediabox.height)
        page.insert_image(r, pixmap=img)
    doc.save(str(pdf_path), garbage=4, deflate=True)
    doc.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert deep research Markdown report to PDF."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to .md file or '-' for stdin",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output PDF path",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="Deep Finance Research Report",
        help="PDF document title",
    )
    parser.add_argument(
        "--images",
        "-I",
        nargs="*",
        default=[],
        help="Optional image paths to append after the report (e.g. chart PNGs)",
    )
    args = parser.parse_args()

    if args.input == "-":
        md_text = sys.stdin.read()
    else:
        p = Path(args.input)
        if not p.is_file():
            print(f"Error: input file not found: {p}", file=sys.stderr)
            return 1
        md_text = p.read_text(encoding="utf-8", errors="replace")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = md_to_html(md_text)
    write_story_to_pdf(html, out_path, args.title, DEFAULT_CSS)
    append_image_pages(out_path, [Path(x) for x in args.images])

    print(f"Wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
