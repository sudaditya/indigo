"""
Ingest a plain-text Master Direction and produce AKN 3.0 XML using Gemini.

Usage:
    python scripts/ingest_pdf_to_akn.py corpus/text/md-290.txt \
        --number 290 --date 2025-11-28 \
        --title "Reserve Bank of India (Urban Co-operative Banks – Prudential Norms on Declaration of Dividends) Directions, 2025"

Output:
    corpus/akn/md-290.xml

Design:
- Gemini generates ONLY the <body> element (structural conversion — the hard part).
- Python wraps it in a deterministic FRBR meta and preface (the mechanical part).
- Prompt lives in scripts/prompts/extract_akn_body.md — kept separate so we can
  iterate on it without editing code.
"""
import os
import sys
import argparse
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai


PROMPT_PATH = Path("scripts/prompts/extract_akn_body.md")
MODEL = "gemini-3.6-flash"


def build_frbr_meta(number: str, date: str, title: str) -> str:
    """Build the FRBR identification block deterministically.

    We do not ask the LLM to do this because:
    - It's a mechanical function of (number, date, title)
    - Wrong FRBR data would break the whole system silently
    """
    frbr_uri = f"/akn/in/act/masterDirection/{date}/{number}"
    return f'''    <meta>
      <identification source="#rbi">
        <FRBRWork>
          <FRBRthis value="{frbr_uri}/!main"/>
          <FRBRuri value="{frbr_uri}"/>
          <FRBRalias value="{title}" name="title"/>
          <FRBRdate date="{date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
          <FRBRcountry value="in"/>
          <FRBRnumber value="{number}"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="{frbr_uri}/eng@{date}/!main"/>
          <FRBRuri value="{frbr_uri}/eng@{date}"/>
          <FRBRdate date="{date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="{frbr_uri}/eng@{date}/!main.xml"/>
          <FRBRuri value="{frbr_uri}/eng@{date}.xml"/>
          <FRBRdate date="{date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
        </FRBRManifestation>
      </identification>
      <references source="#rbi">
        <TLCOrganization eId="rbi" href="/ontology/organization/in/rbi" showAs="Reserve Bank of India"/>
      </references>
    </meta>'''


def extract_preface(text: str) -> str:
    """Extract the 'In exercise of powers...' preface from the plain text.

    Convention: the preface is the paragraph starting with 'In exercise' or
    'In pursuance' and running until the first 'Chapter' heading.

    Cleanup steps applied:
    - Strip ===== PAGE N ===== markers (from PDF extraction)
    - Strip standalone page numbers (short numeric-only lines)
    - Normalize whitespace
    """
    # Find preface start
    match = re.search(r"(In (?:exercise|pursuance) of.*?)(?=Chapter [IVX]+)",
                      text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        # No preface found — some MDs don't have one
        return ""

    preface_text = match.group(1).strip()

    # Strip page markers like "===== PAGE 3 ====="
    preface_text = re.sub(r"={3,}\s*PAGE\s+\d+\s*={3,}", " ", preface_text)

        # Strip standalone page numbers on their own lines (e.g. line with just "3")
    # Match short numeric-only lines. Handles both mid-text (\n N \n) and
    # trailing (\n N at end) cases.
    preface_text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", preface_text)
    preface_text = re.sub(r"\n\s*\d{1,3}\s*$", "", preface_text)
    # Also strip trailing digits that got merged onto a text line after
    # whitespace normalization (e.g. "specified. 3" at the very end)
    preface_text = re.sub(r"\.\s+\d{1,3}\s*$", ".", preface_text)

    # Normalize whitespace (collapse multiple spaces/newlines into single spaces)
    preface_text = re.sub(r"\s+", " ", preface_text).strip()

    return f'''    <preface>
      <p>{preface_text}</p>
    </preface>'''


def call_gemini(source_text: str, prompt_template: str) -> str:
    """Send the source text to Gemini with our AKN extraction prompt.
    Returns the raw response text.
    """
    load_dotenv()
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Combine prompt and source text
    full_prompt = prompt_template + "\n\n" + source_text

    print(f"  Sending {len(source_text):,} chars of source to {MODEL}...")
    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt,
    )
    print(f"  Received {len(response.text):,} chars of XML")
    print(f"  Tokens: {response.usage_metadata.prompt_token_count} in, "
          f"{response.usage_metadata.candidates_token_count} out")

    return response.text


def clean_llm_output(raw: str) -> str:
    """Strip any accidental markdown fences or preamble the LLM added despite instructions."""
    # Remove ```xml or ``` at start
    raw = re.sub(r"^```(?:xml)?\s*\n?", "", raw.strip())
    # Remove trailing ```
    raw = re.sub(r"\n?```\s*$", "", raw)
    return raw.strip()


def assemble_akn_document(body_xml: str, meta_xml: str, preface_xml: str) -> str:
    """Wrap the body in the AKN root elements."""
    preface_section = f"\n{preface_xml}" if preface_xml else ""

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="masterDirection" contains="originalVersion">
{meta_xml}{preface_section}
    {body_xml}
  </act>
</akomaNtoso>
'''


def main():
    parser = argparse.ArgumentParser(description="Convert MD plain text to AKN XML")
    parser.add_argument("text_file", type=Path, help="Path to extracted plain text file")
    parser.add_argument("--number", required=True, help="MD number (e.g. 290)")
    parser.add_argument("--date", required=True, help="Publication date (YYYY-MM-DD)")
    parser.add_argument("--title", required=True, help="Full title of the Master Direction")
    args = parser.parse_args()

    if not args.text_file.exists():
        print(f"Error: {args.text_file} not found")
        sys.exit(1)

    # Read source text
    print(f"Reading {args.text_file}...")
    source_text = args.text_file.read_text(encoding="utf-8")

    # Extract deterministic parts
    print("Extracting preface deterministically...")
    preface_xml = extract_preface(source_text)
    print(f"  Preface: {'found' if preface_xml else 'not found'}")

    print("Building FRBR metadata...")
    meta_xml = build_frbr_meta(args.number, args.date, args.title)

    # Read prompt template
    print(f"Loading prompt from {PROMPT_PATH}...")
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    # Call Gemini for the body
    print("Calling Gemini for structural analysis...")
    raw_body = call_gemini(source_text, prompt_template)
    body_xml = clean_llm_output(raw_body)

    # Assemble the full AKN document
    print("Assembling full AKN document...")
    full_akn = assemble_akn_document(body_xml, meta_xml, preface_xml)

    # Save output
    output_dir = Path("corpus/akn")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (args.text_file.stem + ".xml")
    output_path.write_text(full_akn, encoding="utf-8")
    print(f"Saved to {output_path}")
    print()
    print(f"Total: {len(full_akn):,} chars of AKN XML")


if __name__ == "__main__":
    main()