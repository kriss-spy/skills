#!/usr/bin/env python3
"""
pdf_to_markdown.py - Convert PDF files to Markdown with image extraction.

Usage:
    python3 pdf_to_markdown.py <input.pdf> [output_dir] [--model MODEL] [--dpi DPI] [--batch BATCH_SIZE]

Arguments:
    input.pdf       Path to the input PDF file
    output_dir      Output directory (default: same dir as input, named after PDF)
    --model MODEL   Vision LLM model name (default: gemini-2.5-flash)
    --dpi DPI       DPI for page rendering (default: 200)
    --batch BATCH   Number of pages per LLM batch (default: 3)

Output:
    output_dir/
    ├── output.md           Main Markdown file
    └── images/
        ├── page_001.png    Rendered page images (only for pages with figures)
        └── ...
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Error: PyMuPDF not installed. Run: pip3 install PyMuPDF")

try:
    from pdf2image import convert_from_path
except ImportError:
    sys.exit("Error: pdf2image not installed. Run: pip3 install pdf2image")

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Error: openai not installed. Run: pip3 install openai")

from PIL import Image
import io

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_DPI = 200
DEFAULT_BATCH = 3
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

SYSTEM_PROMPT = """\
You are a document conversion expert. Convert the provided PDF page image(s) into clean, well-structured Markdown.

Your goal is to produce a **readable document**, NOT a page-by-page replica of the PDF.

## Rules

1. **Faithfully reproduce ALL text content**. Do not summarize or omit anything.
2. **Content over format**: Focus on the actual content. The output should read like a coherent document, not a slideshow.
3. **Merge and deduplicate**: If the PDF is a slide deck, multiple pages often share the same section heading. Use each heading ONLY ONCE. Merge content from consecutive pages under the same heading into a continuous flow.
4. **Strip slide/page chrome**: Ignore page numbers, repeated headers/footers, decorative backgrounds, navigation icons, slide template elements, and section title bars that repeat on every page.
5. **Heading hierarchy**: Use proper Markdown heading levels (`#`, `##`, `###`, etc.) to reflect the logical document outline. Do NOT repeat the same heading for every page.
6. **For images/figures/diagrams/photos** on the page:
   - Insert a Markdown image reference: `![description](images/page_NNN.png)`
   - Replace NNN with the zero-padded 3-digit page number provided.
   - Write a concise but descriptive alt-text.
   - Do NOT insert image references for purely decorative elements, backgrounds, or icons.
7. **Tables**: Convert to Markdown pipe tables when possible. If too complex, use an image reference.
8. **Math formulas**: Use LaTeX `$...$` (inline) or `$$...$$` (block).
9. **Code**: Use fenced code blocks with language identifiers.
10. **Lists**: Use `-` for unordered lists. Convert bullet symbols (□, ■, ●, ○, ◆, ▪, etc.) to `-`.
11. **Page boundaries**: Do NOT insert `---` horizontal rules between pages. The output is a continuous document, not page-separated.
12. **Language**: Keep the original language. Do not translate.
13. Output ONLY the Markdown content. No explanations, no wrapping in code fences.
"""


def encode_image_to_base64(image_path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_has_figure(pdf_path: str, page_num: int) -> bool:
    """Use PyMuPDF to detect if a page contains embedded images of meaningful size."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    image_list = page.get_images(full=True)
    doc.close()

    if not image_list:
        return False

    # Filter out tiny images (likely icons or bullets)
    for img in image_list:
        xref = img[0]
        try:
            doc2 = fitz.open(pdf_path)
            pix = fitz.Pixmap(doc2, xref)
            w, h = pix.width, pix.height
            doc2.close()
            if w > 80 and h > 80:
                return True
        except Exception:
            return True
    return False


def render_pages(pdf_path: str, output_dir: str, dpi: int, pages_with_figures: set) -> dict:
    """Render specific PDF pages to PNG images. Returns {page_num: image_path}."""
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    rendered = {}
    for page_num in sorted(pages_with_figures):
        img_name = f"page_{page_num + 1:03d}.png"
        img_path = os.path.join(images_dir, img_name)
        if not os.path.exists(img_path):
            pages = convert_from_path(
                pdf_path, dpi=dpi, first_page=page_num + 1, last_page=page_num + 1
            )
            if pages:
                pages[0].save(img_path, "PNG")
        rendered[page_num] = img_path

    return rendered


def render_page_for_llm(pdf_path: str, page_num: int, dpi: int = 150) -> str:
    """Render a single page to a temporary PNG and return base64 string."""
    pages = convert_from_path(
        pdf_path, dpi=dpi, first_page=page_num + 1, last_page=page_num + 1
    )
    if not pages:
        return ""
    buf = io.BytesIO()
    pages[0].save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def call_vision_llm(
    client: OpenAI,
    model: str,
    page_images_b64: list[tuple[int, str]],
) -> str:
    """Send page images to the vision LLM and get Markdown output."""
    user_content = []

    for page_num, b64_img in page_images_b64:
        user_content.append({
            "type": "text",
            "text": f"[Page {page_num + 1} — use page_{page_num + 1:03d}.png for image references]",
        })
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64_img}",
            },
        })

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=16000,
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [Retry {attempt + 1}/{MAX_RETRIES}] LLM call failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    return f"<!-- LLM conversion failed for pages {[p+1 for p,_ in page_images_b64]} -->"


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------
def postprocess_markdown(md: str) -> str:
    """Clean up and improve the raw LLM Markdown output."""

    # 1. Strip code fence wrappers the LLM might have added
    md = re.sub(r"^```(?:markdown|md)?\s*\n", "", md)
    md = re.sub(r"\n```\s*$", "", md)

    # 2. Replace special bullet symbols with standard Markdown `-`
    #    Match lines starting with optional whitespace + a bullet symbol
    bullet_chars = r"[□■●○◆◇▪▫►▸▹▻•·–—]"
    md = re.sub(r"^(\s*)" + bullet_chars + r"\s+", r"\1- ", md, flags=re.MULTILINE)

    # 3. Fix --- horizontal rules: ensure blank lines before and after
    #    This prevents accidental setext heading triggers.
    #    Match a line that is exactly `---` (or more dashes) with possible whitespace.
    md = re.sub(r"\n*^([ \t]*-{3,}[ \t]*)$\n*", r"\n\n\1\n\n", md, flags=re.MULTILINE)

    # 4. Deduplicate headings globally (not just consecutive)
    #    Slide PDFs repeat the same section heading on every page.
    #    Keep only the FIRST occurrence of each heading text.
    def dedup_headings(text: str) -> str:
        lines = text.split("\n")
        result = []
        seen_headings = set()  # normalized heading text
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith("#"):
                # Normalize: strip leading #s and whitespace for comparison
                heading_text = re.sub(r"^#+\s*", "", stripped).strip()
                if heading_text in seen_headings:
                    # Skip this duplicate heading and any immediately following blank lines
                    i += 1
                    while i < len(lines) and lines[i].strip() == "":
                        i += 1
                    continue
                seen_headings.add(heading_text)
            result.append(lines[i])
            i += 1
        return "\n".join(result)

    md = dedup_headings(md)

    # 4b. Normalize heading levels: ensure consistent hierarchy
    #     Numbered sections like "2.1" → ##, "2.1.1" → ###
    #     Non-numbered headings under a section inherit parent level + 1
    def normalize_heading_levels(text: str) -> str:
        lines = text.split("\n")
        result = []
        first_heading_seen = False
        current_section_level = 1  # tracks the level of the most recent numbered section
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#include") and not stripped.startswith("#define") and not stripped.startswith("#pragma"):
                m = re.match(r"^(#+)\s+(.*)", stripped)
                if m:
                    content = m.group(2)
                    # Detect numbered sections like "2.1", "2.1.1" etc.
                    sec_match = re.match(r"^(\d+(?:\.\d+)*)\s", content)
                    if sec_match:
                        dots = sec_match.group(1).count(".")
                        # "2" → #, "2.1" → ##, "2.1.1" → ###
                        target_level = 1 + dots
                        current_section_level = target_level
                        first_heading_seen = True
                        line = "#" * target_level + " " + content
                    elif not first_heading_seen:
                        # Before any numbered section: keep original level (title, TOC, etc.)
                        # Just preserve what the LLM gave us
                        pass
                    else:
                        # Non-numbered heading after a numbered section: one level below
                        target_level = current_section_level + 1
                        line = "#" * target_level + " " + content
            result.append(line)
        return "\n".join(result)

    md = normalize_heading_levels(md)

    # 5. Remove excessive blank lines (more than 2 consecutive → 2)
    md = re.sub(r"\n{3,}", "\n\n", md)

    # 6. Ensure file ends with single newline
    md = md.strip() + "\n"

    return md


def convert_pdf_to_markdown(
    pdf_path: str,
    output_dir: str | None = None,
    model: str = DEFAULT_MODEL,
    dpi: int = DEFAULT_DPI,
    batch_size: int = DEFAULT_BATCH,
) -> str:
    """Main conversion function. Returns path to the output Markdown file."""
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.isfile(pdf_path):
        sys.exit(f"Error: File not found: {pdf_path}")

    pdf_name = Path(pdf_path).stem
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(pdf_path), pdf_name)
    os.makedirs(output_dir, exist_ok=True)

    # Get page count
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    print(f"PDF: {pdf_path}")
    print(f"Pages: {total_pages}")
    print(f"Output: {output_dir}")
    print(f"Model: {model}")
    print()

    # Step 1: Detect pages with figures
    print("Step 1: Detecting pages with figures...")
    pages_with_figures = set()
    for i in range(total_pages):
        if detect_has_figure(pdf_path, i):
            pages_with_figures.add(i)
    print(f"  Pages with figures: {len(pages_with_figures)} / {total_pages}")

    # Step 2: Render figure pages as PNG
    print("Step 2: Rendering figure pages as PNG...")
    rendered = render_pages(pdf_path, output_dir, dpi, pages_with_figures)
    print(f"  Rendered {len(rendered)} page images")

    # Step 3: Convert pages via Vision LLM in batches
    print(f"Step 3: Converting pages via LLM (batch size: {batch_size})...")
    client = OpenAI()
    md_parts = []

    for batch_start in range(0, total_pages, batch_size):
        batch_end = min(batch_start + batch_size, total_pages)
        batch_pages = list(range(batch_start, batch_end))
        print(f"  Processing pages {batch_start + 1}-{batch_end}...")

        # Render pages for LLM (lower DPI for faster transfer)
        page_images = []
        for p in batch_pages:
            b64 = render_page_for_llm(pdf_path, p, dpi=150)
            if b64:
                page_images.append((p, b64))

        if page_images:
            md_text = call_vision_llm(client, model, page_images)
            md_parts.append(md_text)

    # Step 4: Assemble and post-process
    print("Step 4: Assembling and post-processing Markdown...")
    raw_md = "\n\n".join(md_parts)
    final_md = postprocess_markdown(raw_md)

    output_md = os.path.join(output_dir, "output.md")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(final_md)

    # Step 5: Sync images - render any LLM-referenced pages not yet rendered, remove unreferenced
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    referenced = set()
    for line in final_md.split("\n"):
        if "images/" in line:
            for m in re.finditer(r"images/(page_(\d+)\.png)", line):
                referenced.add(m.group(1))
                page_idx = int(m.group(2)) - 1  # 0-indexed
                img_path = os.path.join(images_dir, m.group(1))
                if not os.path.exists(img_path) and 0 <= page_idx < total_pages:
                    print(f"  Rendering missing referenced page: {m.group(1)}")
                    extra_pages = convert_from_path(
                        pdf_path, dpi=dpi, first_page=page_idx + 1, last_page=page_idx + 1
                    )
                    if extra_pages:
                        extra_pages[0].save(img_path, "PNG")

    for fname in os.listdir(images_dir):
        if fname.endswith(".png") and fname not in referenced:
            os.remove(os.path.join(images_dir, fname))
            print(f"  Removed unreferenced image: {fname}")

    remaining_images = len([f for f in os.listdir(images_dir) if f.endswith(".png")])

    print()
    print(f"Done! Output: {output_md}")
    print(f"  Markdown size: {os.path.getsize(output_md):,} bytes")
    print(f"  Images kept: {remaining_images}")

    return output_md


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown with image extraction"
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("output_dir", nargs="?", default=None, help="Output directory")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Vision LLM model (default: {DEFAULT_MODEL})")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"DPI for image rendering (default: {DEFAULT_DPI})")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH, help=f"Pages per LLM batch (default: {DEFAULT_BATCH})")

    args = parser.parse_args()

    convert_pdf_to_markdown(
        pdf_path=args.input_pdf,
        output_dir=args.output_dir,
        model=args.model,
        dpi=args.dpi,
        batch_size=args.batch,
    )


if __name__ == "__main__":
    main()
