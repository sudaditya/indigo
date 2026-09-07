"""
Load an AKN XML document into Indigo via its REST API.

Usage:
    python scripts/load_into_indigo.py corpus/akn/md-290.xml \
        --number 290 --date 2025-11-28 \
        --title "Reserve Bank of India (Urban Co-operative Banks – Prudential Norms on Declaration of Dividends) Directions, 2025"

Two-step process:
1. Create a Work (metadata about the MD)
2. Create a Document (dated Expression with actual XML content)

The Work's FRBR URI must match the FRBR URI baked into the XML by our
ingest_pdf_to_akn.py — Indigo validates this.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import requests


def load_env():
    load_dotenv()
    token = os.environ.get("INDIGO_API_TOKEN")
    api_url = os.environ.get("INDIGO_API_URL", "http://localhost:8000/api")
    if not token:
        print("Error: INDIGO_API_TOKEN not set in .env")
        sys.exit(1)
    return token, api_url


def create_work(api_url: str, token: str, work_data: dict) -> dict:
    """POST to /api/works/ to create a new Work."""
    print(f"Creating Work at {api_url}/works...")
    response = requests.post(
        f"{api_url}/works",
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        json=work_data,
    )
    #if response.status_code == 400:
        # Show validation errors clearly
     #   print(f"  Status: 400 Bad Request")
     #   print(f"  Body: {response.text}")
     #   response.raise_for_status()
    #response.raise_for_status()
    if not response.ok:
        # Show error details clearly for any non-success response
        print(f"  Status: {response.status_code} {response.reason}")
        print(f"  Response headers: {dict(response.headers)}")
        print(f"  Body: {response.text}")
        response.raise_for_status()
    result = response.json()
    print(f"  Created Work id={result['id']}, frbr_uri={result['frbr_uri']}")
    return result


def create_document(api_url: str, token: str, work: dict, xml_content: str, expression_date: str) -> dict:
    """POST to /api/documents/ to create a Document (Expression) attached to a Work."""
    print(f"Creating Document at {api_url}/documents...")
    doc_data = {
        "work": work["frbr_uri"],
        "expression_date": expression_date,
        "language": "eng",
        "content": xml_content,
    }
    response = requests.post(
        f"{api_url}/documents",
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        json=doc_data,
    )
    #if response.status_code == 400:
    #    print(f"  Status: 400 Bad Request")
    #    print(f"  Body: {response.text}")
    #    response.raise_for_status()
    #response.raise_for_status()
    if not response.ok:
        # Show error details clearly for any non-success response
        print(f"  Status: {response.status_code} {response.reason}")
        print(f"  Response headers: {dict(response.headers)}")
        print(f"  Body: {response.text}")
        response.raise_for_status()
    result = response.json()
    print(f"  Created Document id={result['id']}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Load an AKN XML into Indigo")
    parser.add_argument("xml_file", type=Path)
    parser.add_argument("--number", required=True)
    parser.add_argument("--date", required=True, help="Publication date YYYY-MM-DD")
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    if not args.xml_file.exists():
        print(f"Error: {args.xml_file} not found")
        sys.exit(1)

    xml_content = args.xml_file.read_text(encoding="utf-8")
    print(f"Loaded {args.xml_file} ({len(xml_content):,} chars)")

    token, api_url = load_env()

    # Step 1: Create the Work
    work_data = {
        "frbr_uri": f"/akn/in/act/masterDirection/{args.date}/{args.number}",
        "title": args.title,
        "country": "in",
        "locality": None,
        "publication_date": args.date,
        "publication_number": args.number,
        "publication_name": "RBI Master Direction",
    }
    work = create_work(api_url, token, work_data)

    # Step 2: Create the Document (Expression)
    doc = create_document(api_url, token, work, xml_content, args.date)

    print()
    print(f"Success! View at:")
    print(f"  Work:     http://localhost:8000/places/in/works/{work['id']}/")
    print(f"  Document: http://localhost:8000/places/in/works/{work['id']}/documents/{doc['id']}/")


if __name__ == "__main__":
    main()