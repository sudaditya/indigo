"""
Extract text from PDF using pymupdf (fitz), for comparison against pypdf.

Usage:
    python scripts/extract_pdf_mupdf.py corpus/pdfs/md-172.pdf

Output:
    corpus/text/md-172-mupdf.txt

pymupdf preserves layout information that pypdf discards, so it tends to
handle tables and multi-column layouts better.
"""
import sys
from pathlib import Path
import pymupdf  # imported as pymupdf; older code sometimes uses `import fitz`


def extract_pdf_to_text(pdf_path: Path) -> str:
    """Extract text page-by-page, joined with page markers."""
    doc = pymupdf.open(pdf_path)
    pages_text = []

    for page_num, page in enumerate(doc, start=1):
        pages_text.append(f"\n\n===== PAGE {page_num} =====\n\n")
        # get_text() with no args gives you the default text extraction
        # (which uses layout info). Could also try "text", "blocks", or "dict"
        # for different quality/structure tradeoffs.
        pages_text.append(page.get_text() or "[EMPTY PAGE]")

    doc.close()
    return "".join(pages_text)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/extract_pdf_mupdf.py <path-to-pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)

    print(f"Reading {pdf_path} with pymupdf...")
    doc = pymupdf.open(pdf_path)
    print(f"  Pages: {len(doc)}")
    doc.close()

    text = extract_pdf_to_text(pdf_path)
    print(f"  Extracted {len(text):,} characters")

    # Save with -mupdf suffix so we can compare against pypdf's output
    output_dir = Path("corpus/text")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (pdf_path.stem + ".txt")
    output_path.write_text(text, encoding="utf-8")
    print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()