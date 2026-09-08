"""
Extract text from a PDF file, page by page, and save to a .txt file.

Usage:
    python scripts/extract_pdf.py corpus/pdfs/md-290.pdf

Output:
    corpus/text/md-290.txt

We do this as a separate step (not inline with Gemini call) because:
- We want to inspect the extracted text before sending to the LLM
- If Gemini's structural analysis is wrong, we need to know whether the
  text extraction was clean or garbage went in
- Text extraction is deterministic; LLM calls are not. Separating them
  makes debugging much easier.
"""
import sys
from pathlib import Path
from pypdf import PdfReader


def extract_pdf_to_text(pdf_path: Path) -> str:
    """Extract all text from a PDF, one page at a time, joined with page markers."""
    reader = PdfReader(pdf_path)
    pages_text = []

    for page_num, page in enumerate(reader.pages, start=1):
        # Insert a marker between pages so we can see page boundaries
        # in the output. Useful for debugging what came from where.
        pages_text.append(f"\n\n===== PAGE {page_num} =====\n\n")
        pages_text.append(page.extract_text() or "[EMPTY PAGE]")

    return "".join(pages_text)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/extract_pdf.py <path-to-pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    # Extract text
    print(f"Reading {pdf_path}...")
    reader = PdfReader(pdf_path)
    print(f"  Pages: {len(reader.pages)}")

    text = extract_pdf_to_text(pdf_path)
    print(f"  Extracted {len(text):,} characters")

    # Save output to corpus/text/ with the same base name
    output_dir = Path("corpus/text")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / (pdf_path.stem + ".txt")
    output_path.write_text(text, encoding="utf-8")
    print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()