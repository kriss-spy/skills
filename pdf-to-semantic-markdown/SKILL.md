---
name: pdf-to-semantic-markdown
description: Convert PDF files to semantic Markdown with image extraction. Use when converting PDF documents, slides, or scanned pages to well-structured Markdown format, especially when the PDF contains figures, diagrams, or photos that need to be preserved as image files.
---

# PDF to Semantic Markdown

Convert PDF files to well-structured Markdown. Figures and diagrams are saved as PNG images and referenced in the output Markdown.

## Dependencies

Install before first use:

```bash
sudo pip3 install PyMuPDF
```

Pre-installed: `pdf2image`, `pillow`, `openai`.

## Usage

Run the conversion script:

```bash
python3 /home/ubuntu/skills/pdf-to-semantic-markdown/scripts/pdf_to_markdown.py <input.pdf> [output_dir] [--model MODEL] [--dpi DPI] [--batch BATCH]
```

| Argument       | Default              | Description                                      |
|----------------|----------------------|--------------------------------------------------|
| `input.pdf`    | (required)           | Path to the input PDF file                       |
| `output_dir`   | `<pdf_stem>/`        | Output directory (created automatically)         |
| `--model`      | `gemini-2.5-flash`   | Vision LLM model for page recognition            |
| `--dpi`        | `200`                | DPI for rendered page images                     |
| `--batch`      | `3`                  | Number of pages sent per LLM call                |

## Output Structure

```
output_dir/
├── output.md           # Main Markdown file
└── images/
    ├── page_003.png    # Rendered pages containing figures
    └── page_012.png
```

- Only pages with meaningful figures are saved as images.
- Image references use relative paths: `![alt text](images/page_NNN.png)`.
- Unreferenced images are automatically cleaned up.

## How It Works

1. **Detect figures** via PyMuPDF embedded image analysis.
2. **Render figure pages** to PNG at the specified DPI.
3. **Send page images** to a Vision LLM in batches for Markdown conversion.
4. **Post-process**: deduplicate headings, normalize heading hierarchy, replace special bullet symbols with `-`, fix `---` separators, remove slide/page chrome.
5. **Sync images**: render any additional pages the LLM referenced; remove unreferenced images.

## Cloud Environment Rule

When conversion runs on a cloud environment and the PDF contains images:

1. Upload the extracted images to cloud storage and reference them by URL in the Markdown, **or**
2. Save images to the filesystem and include them in the final archive delivered to the user.

Do not return Markdown with broken relative image paths unless the image files are also provided.

## Tips

- Increase `--batch` (e.g., `5`) for faster processing of large PDFs; decrease for higher accuracy.
- Use `--dpi 300` for PDFs with small text or fine diagrams.
- For very large PDFs (100+ pages), expect several minutes of processing time.
- The script handles Chinese, English, and mixed-language documents.
- Slide-deck PDFs are automatically converted into continuous document structure (repeated section headers merged, page separators removed).
