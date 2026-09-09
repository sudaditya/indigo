"""
Rewrap existing AKN XML files: strip the old <preface> and regenerate it
from source text using the current extract_preface() logic. Also refresh
the FRBR meta block from CLI arguments.

Useful when you've updated the preface cleanup regex (or the FRBR wrapper)
and want to re-apply it to already-generated XML WITHOUT re-calling Gemini.

The <body> element (which Gemini produced) is preserved unchanged.

Usage:
    python scripts/rewrap_akn.py corpus/akn/md-172.xml corpus/text/md-172.txt \
        --number 172 --date 2025-11-28 \
        --title "Reserve Bank of India (Commercial Banks - Climate Finance...) Directions, 2025"
"""
import sys
import argparse
import re
from pathlib import Path

# Reuse the same helpers from the main ingest script by importing them
# We can't just `from ingest_pdf_to_akn import ...` cleanly because that
# script runs main() on import in some setups. Simplest: duplicate the
# two small helper functions here.


def build_frbr_meta(number: str, date: str, title: str) -> str:
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
    """Extract and clean the preface from raw source text.

    Applies:
    - Regex match on "In exercise/pursuance of ... up to first Chapter"
    - Strip ===== PAGE N ===== markers
    - Strip standalone page-number lines
    - Strip trailing page numbers at the very end
    - Normalize whitespace
    """
    match = re.search(r"(In (?:exercise|pursuance) of.*?)(?=Chapter [IVX]+)",
                      text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    preface_text = match.group(1).strip()

    # Strip page markers
    preface_text = re.sub(r"={3,}\s*PAGE\s+\d+\s*={3,}", " ", preface_text)
    # Standalone page numbers on their own lines
    preface_text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", preface_text)
    # Trailing page number on its own line at end
    preface_text = re.sub(r"\n\s*\d{1,3}\s*$", "", preface_text)
    # Normalize whitespace
    preface_text = re.sub(r"\s+", " ", preface_text).strip()
    # Safety net: sentence-terminating period + spaces + short number at end
    preface_text = re.sub(r"\.\s+\d{1,3}\s*$", ".", preface_text)

    return f'''    <preface>
      <p>{preface_text}</p>
    </preface>'''


def extract_body_from_xml(xml_content: str) -> str:
    """Extract the <body>...</body> block (with indentation) from existing AKN XML."""
    match = re.search(r'(\s*<body>.*?</body>)', xml_content, flags=re.DOTALL)
    if not match:
        raise ValueError("Could not find <body> element in existing XML")
    return match.group(1).strip()


def assemble_akn_document(body_xml: str, meta_xml: str, preface_xml: str) -> str:
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
    parser = argparse.ArgumentParser(description='Rewrap existing AKN XML with updated meta + preface')
    parser.add_argument('xml_file', type=Path, help='Existing AKN XML file (will be overwritten)')
    parser.add_argument('text_file', type=Path, help='Source plain text (for preface extraction)')
    parser.add_argument('--number', required=True)
    parser.add_argument('--date', required=True, help='YYYY-MM-DD')
    parser.add_argument('--title', required=True)
    args = parser.parse_args()

    if not args.xml_file.exists():
        print(f"Error: {args.xml_file} not found")
        sys.exit(1)
    if not args.text_file.exists():
        print(f"Error: {args.text_file} not found")
        sys.exit(1)

    print(f"Reading existing XML from {args.xml_file}")
    xml_content = args.xml_file.read_text(encoding='utf-8')

    print(f"Extracting <body> element (preserving Gemini's structural analysis)")
    body_xml = extract_body_from_xml(xml_content)
    print(f"  Body: {len(body_xml):,} chars")

    print(f"Reading source text from {args.text_file}")
    source_text = args.text_file.read_text(encoding='utf-8')

    print("Extracting cleaned preface...")
    preface_xml = extract_preface(source_text)
    print(f"  Preface: {'found and cleaned' if preface_xml else 'not found'}")

    print("Building FRBR metadata...")
    meta_xml = build_frbr_meta(args.number, args.date, args.title)

    print("Assembling full AKN document...")
    full_akn = assemble_akn_document(body_xml, meta_xml, preface_xml)

    args.xml_file.write_text(full_akn, encoding='utf-8')
    print(f"Overwrote {args.xml_file} ({len(full_akn):,} chars total)")


if __name__ == '__main__':
    main()