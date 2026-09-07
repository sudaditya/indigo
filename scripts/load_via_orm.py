"""
Load an AKN XML Master Direction into Indigo's database via Django ORM.

Runs INSIDE the Docker container (needs Django models):
    docker compose exec web python scripts/load_via_orm.py \
        corpus/akn/md-290.xml \
        --number 290 --date 2025-11-28 \
        --title "Reserve Bank of India (Urban Co-operative Banks – Prudential Norms on Declaration of Dividends) Directions, 2025"

Why ORM instead of REST API:
- Indigo's WorkSerializer/DocumentSerializer weren't designed for writes.
- Making them writable is a 2-3 session engineering task (custom .create() methods
  or separate WriteSerializers) that we're deferring.
- The ORM code here will be reused inside future custom API views anyway.

What this does:
1. Reads the AKN XML.
2. Creates a Work (metadata about the MD) via Work.objects.create().
3. Creates a Document (Expression with the XML content) via Document.objects.create().
4. Prints URLs to view them.
"""
import os
import sys
import argparse
from pathlib import Path

# ---- Django bootstrapping ----
# Since we're running as a plain script (not manage.py shell), we have to
# tell Django where its settings live before importing any models.
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.settings')
django.setup()

# Now safe to import models
from django.contrib.auth import get_user_model
from indigo_api.models import Work, Document, Language as IndigoLanguage
from indigo_api.models import Country as IndigoCountry


def load_master_direction(
    xml_path: Path,
    number: str,
    publication_date: str,
    title: str,
    creator_username: str = 'sudaditya',
):
    # ---- Sanity checks ----
    if not xml_path.exists():
        print(f"ERROR: XML file not found at {xml_path}")
        sys.exit(1)

    xml_content = xml_path.read_text(encoding='utf-8')
    print(f"Loaded {len(xml_content):,} chars from {xml_path}")

    # Find the creator user (needs to be a real user for audit fields)
    User = get_user_model()
    try:
        creator = User.objects.get(username=creator_username)
    except User.DoesNotExist:
        print(f"ERROR: User '{creator_username}' not found. "
              f"Available users: {[u.username for u in User.objects.all()]}")
        sys.exit(1)
    print(f"Creator: {creator.username}")

    # Find India (Country) and English (Language)
    india = IndigoCountry.objects.get(country__iso='IN')
    english = IndigoLanguage.objects.get(language__iso_639_1='en')
    print(f"Place: {india}, Language: {english}")

    # ---- FRBR URI construction ----
    # Format: /akn/{country}/act/{doctype}/{date}/{number}
    # (Indigo's convention. Doctype 'act' is the AKN default.)
    frbr_uri = f"/akn/in/act/masterDirection/{publication_date}/{number}"

    # ---- Check for existing Work with this URI (avoid duplicates) ----
    existing = Work.objects.filter(frbr_uri=frbr_uri).first()
    if existing:
        print(f"WARNING: Work already exists with frbr_uri={frbr_uri} (id={existing.id})")
        print("Delete it first if you want to re-create:")
        print(f"  Work.objects.get(id={existing.id}).delete()")
        sys.exit(1)

    # ---- Create the Work ----
    # Populating all the fields Indigo needs, not just the 3 strictly-required.
    print(f"\nCreating Work at {frbr_uri}...")
    work = Work.objects.create(
        frbr_uri=frbr_uri,
        title=title,
        country=india,
        doctype='act',
        subtype='masterDirection',
        date=publication_date,
        number=number,
        publication_date=publication_date,
        publication_number=number,
        publication_name='RBI Master Direction',
        principal=True,     # This is a principal (not subsidiary) regulation
        stub=False,          # Has actual content, not a placeholder
        created_by_user=creator,
        updated_by_user=creator,
    )
    print(f"  Created Work id={work.id}")
    print(f"  FRBR URI: {work.frbr_uri}")

    # ---- Create the Document (Expression) ----
    print(f"\nCreating Document (Expression at {publication_date})...")
    document = Document.objects.create(
        work=work,
        frbr_uri=frbr_uri,  # Same as the Work at initial publication
        title=title,
        language=english,
        expression_date=publication_date,
        document_xml=xml_content,
        draft=False,         # Published, not a working draft
        deleted=False,
        created_by_user=creator,
        updated_by_user=creator,
    )
    print(f"  Created Document id={document.id}")

    # ---- Success ----
    print(f"\n{'='*60}")
    print(f"SUCCESS")
    print(f"{'='*60}")
    print(f"Work id:     {work.id}")
    print(f"Document id: {document.id}")
    print(f"\nView in browser:")
    print(f"  Work overview:  http://localhost:8000/places/in/works/detail/{work.id}")
    print(f"  Document edit:  http://localhost:8000/places/in/works/detail/{work.id}/documents")
    print(f"  All Works:      http://localhost:8000/places/in/works")


def main():
    parser = argparse.ArgumentParser(description='Load an AKN XML into Indigo via ORM')
    parser.add_argument('xml_file', type=Path)
    parser.add_argument('--number', required=True, help='MD number, e.g. 290')
    parser.add_argument('--date', required=True, help='Publication date YYYY-MM-DD')
    parser.add_argument('--title', required=True, help='Full title of the Master Direction')
    parser.add_argument('--user', default='sudaditya', help='Creator username (default: sudaditya)')
    args = parser.parse_args()

    load_master_direction(
        xml_path=args.xml_file,
        number=args.number,
        publication_date=args.date,
        title=args.title,
        creator_username=args.user,
    )


if __name__ == '__main__':
    main()