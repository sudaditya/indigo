"""
End-to-end pipeline: PDF bytes → AKN XML → loaded Work.

Refactored from the standalone scripts in scripts/ so it can be called
programmatically (e.g. from a Django view for browser upload).

Public functions:
    extract_text_from_pdf(pdf_bytes)      — PDF → plain text via pymupdf
    generate_akn_from_text(text, meta)    — text → AKN XML via Gemini
    load_akn_into_indigo(akn_xml, meta)   — AKN XML → Work + Document rows
    run_full_pipeline(pdf_bytes, meta)    — all three, returns the Work

The scripts in scripts/ still work — they're now thin wrappers around
these functions. Callers can pick whichever level of granularity they
need.
"""
import io
import os
import re
import logging
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from django.conf import settings
from django.contrib.auth import get_user_model
from lxml import etree

log = logging.getLogger(__name__)


# ============================================================
# Data types
# ============================================================

@dataclass
class MDMetadata:
    """Metadata needed to build FRBR identifiers and Work rows."""
    number: str          # e.g. "290"
    date: str            # ISO format: "2025-11-28"
    title: str           # full RBI title


class PipelineError(Exception):
    """Raised when a pipeline step fails in a way we can report to the user."""


# ============================================================
# Step 1: PDF → plain text
# ============================================================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pymupdf.

    Returns the concatenated text of all pages, separated by page markers.
    Same output format as scripts/extract_pdf.py.
    """
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    except Exception as e:
        raise PipelineError(f"Could not open PDF: {e}")

    pages = []
    for page_num, page in enumerate(doc, start=1):
        pages.append(f"\n\n===== PAGE {page_num} =====\n\n")
        pages.append(page.get_text() or "[EMPTY PAGE]")

    doc.close()
    return "".join(pages)


# ============================================================
# Step 2: text → AKN XML (Gemini)
# ============================================================

def _build_frbr_meta(meta: MDMetadata) -> str:
    """Deterministically construct the <meta> block of the AKN document."""
    frbr_uri = f"/akn/in/act/masterDirection/{meta.date}/{meta.number}"
    return f'''    <meta>
      <identification source="#rbi">
        <FRBRWork>
          <FRBRthis value="{frbr_uri}/!main"/>
          <FRBRuri value="{frbr_uri}"/>
          <FRBRalias value="{meta.title}" name="title"/>
          <FRBRdate date="{meta.date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
          <FRBRcountry value="in"/>
          <FRBRnumber value="{meta.number}"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="{frbr_uri}/eng@{meta.date}/!main"/>
          <FRBRuri value="{frbr_uri}/eng@{meta.date}"/>
          <FRBRdate date="{meta.date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="{frbr_uri}/eng@{meta.date}/!main.xml"/>
          <FRBRuri value="{frbr_uri}/eng@{meta.date}.xml"/>
          <FRBRdate date="{meta.date}" name="Generation"/>
          <FRBRauthor href="#rbi"/>
        </FRBRManifestation>
      </identification>
      <references source="#rbi">
        <TLCOrganization eId="rbi" href="/ontology/organization/in/rbi" showAs="Reserve Bank of India"/>
      </references>
    </meta>'''


def _extract_preface(text: str) -> str:
    """Extract the preface deterministically from source text."""
    match = re.search(
        r"(In (?:exercise|pursuance) of.*?)(?=Chapter [IVX]+)",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ""

    preface_text = match.group(1).strip()
    preface_text = re.sub(r"={3,}\s*PAGE\s+\d+\s*={3,}", " ", preface_text)
    preface_text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", preface_text)
    preface_text = re.sub(r"\n\s*\d{1,3}\s*$", "", preface_text)
    preface_text = re.sub(r"\s+", " ", preface_text).strip()
    preface_text = re.sub(r"\.\s+\d{1,3}\s*$", ".", preface_text)

    return f'''    <preface>
      <p>{preface_text}</p>
    </preface>'''


def _load_prompt() -> str:
    """Load the Gemini prompt from the same file the scripts use."""
    prompt_path = Path(settings.BASE_DIR) / 'scripts' / 'prompts' / 'extract_akn_body.md'
    if not prompt_path.exists():
        raise PipelineError(f"Prompt file not found at {prompt_path}")
    return prompt_path.read_text(encoding='utf-8')


def generate_akn_from_text(text: str, meta: MDMetadata) -> str:
    """Call Gemini to structure the text into AKN, then wrap with meta + preface.

    Returns the complete AKN 3.0 XML document as a string.
    Raises PipelineError with a helpful message if Gemini fails.
    """
    from google import genai
    from dotenv import load_dotenv

    # Load .env from project root — matches the behavior of scripts/ingest_pdf_to_akn.py
    load_dotenv()

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise PipelineError(
            "GEMINI_API_KEY not set in environment. "
            "Check your .env file."
        )

    prompt_template = _load_prompt()
    full_prompt = f"{prompt_template}\n\n---\n\n{text}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=full_prompt,
        )
    except Exception as e:
        # Surface common Gemini errors with user-friendly language
        msg = str(e)
        if '429' in msg or 'RESOURCE_EXHAUSTED' in msg:
            raise PipelineError(
                "Gemini free-tier daily quota exhausted (20 requests/day). "
                "Try again tomorrow, or upgrade to paid tier."
            )
        if '503' in msg or 'UNAVAILABLE' in msg:
            raise PipelineError(
                "Gemini is temporarily unavailable. Please retry in a minute."
            )
        raise PipelineError(f"Gemini call failed: {e}")

    raw_body = response.text.strip()
    # Strip markdown code fences if Gemini included them
    if raw_body.startswith('```'):
        raw_body = re.sub(r'^```(?:xml)?\n?', '', raw_body)
        raw_body = re.sub(r'\n?```$', '', raw_body)

    preface_xml = _extract_preface(text)
    meta_xml = _build_frbr_meta(meta)

    preface_section = f"\n{preface_xml}" if preface_xml else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="masterDirection" contains="originalVersion">
{meta_xml}{preface_section}
    {raw_body}
  </act>
</akomaNtoso>
'''


# ============================================================
# Step 3: AKN XML → Work + Document in DB
# ============================================================

def load_akn_into_indigo(akn_xml: str, meta: MDMetadata):
    """Create Work + Document rows in Indigo from AKN XML.

    Returns the created Work instance.
    Raises PipelineError if a Work with this FRBR URI already exists.
    """
    from indigo_api.models import Work, Document, Country, Language

    # Validate XML structure before touching the DB
    try:
        etree.fromstring(akn_xml.encode('utf-8'))
    except etree.XMLSyntaxError as e:
        raise PipelineError(f"Generated AKN is not valid XML: {e}")

    frbr_uri = f"/akn/in/act/masterDirection/{meta.date}/{meta.number}"

    if Work.objects.filter(frbr_uri=frbr_uri).exists():
        raise PipelineError(
            f"A Master Direction with FRBR URI {frbr_uri} already exists. "
            f"To replace it, delete it first from the admin."
        )

    # Look up the creator user + place metadata
    User = get_user_model()
    creator = User.objects.filter(is_superuser=True).first()
    if not creator:
        raise PipelineError("No superuser found — cannot attribute the Work.")

    country = Country.objects.filter(country__iso='IN').first()
    if not country:
        raise PipelineError("Indigo Country row for India not found. Check fixtures.")

    language = Language.objects.filter(language__iso_639_3='eng').first()
    if not language:
        raise PipelineError("Indigo Language row for English not found. Check fixtures.")

    # Create Work
    work = Work.objects.create(
        frbr_uri=frbr_uri,
        title=meta.title,
        country=country,
        publication_name='RBI Master Direction',
        publication_number=meta.number,
        publication_date=meta.date,
        principal=True,
        stub=False,
        created_by_user=creator,
        updated_by_user=creator,
    )

    # Create Document (the expression at the given date)
    Document.objects.create(
        work=work,
        title=meta.title,
        expression_date=meta.date,
        language=language,
        document_xml=akn_xml,
        created_by_user=creator,
        updated_by_user=creator,
    )

    return work


# ============================================================
# Full pipeline (all three steps chained)
# ============================================================

def run_full_pipeline(pdf_bytes: bytes, meta: MDMetadata):
    """PDF → AKN → Work, all in one call.

    Returns the created Work.
    Raises PipelineError on any step's failure.
    """
    log.info(f"Pipeline: extracting text from PDF ({len(pdf_bytes):,} bytes)")
    text = extract_text_from_pdf(pdf_bytes)
    log.info(f"Pipeline: extracted {len(text):,} chars")

    log.info(f"Pipeline: generating AKN via Gemini for MD {meta.number}")
    akn = generate_akn_from_text(text, meta)
    log.info(f"Pipeline: got {len(akn):,} chars of AKN")

    log.info(f"Pipeline: loading into Indigo")
    work = load_akn_into_indigo(akn, meta)
    log.info(f"Pipeline: created Work id={work.id}")

    return work