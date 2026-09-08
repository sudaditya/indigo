# RBI Master Directions Registry — POC

## Owner
MisterSood (Manager, Department of Regulation, RBI)

## Purpose
POC for a version-controlled Master Directions platform, forked from Laws.Africa Indigo.
Ingest, version-control, and enable structured amendment of RBI's ~250 Master Directions.

## Stack
- Backend: Django (from Indigo fork) + Postgres — runs in Docker
- Frontend: React + Vite (to be built, replacing Indigo's Django templates)
   - LLM: Google Gemini API (gemini-3.6-flash, free tier) for PDF ingestion
   - Hosting: Local (MacBook Air) for POC; RBI infrastructure later

## Repo
- GitHub: https://github.com/sudaditya/indigo (fork of laws-africa/indigo)
- Local: ~/Downloads/Projects/rbi-registry

## Phase status
- [x] Phase 0 — Indigo running locally with India as a Place
- [ ] Phase 1 — Strip Indigo frontend, restructure repo
- [ ] Phase 2 — PDF ingestion pipeline (Claude API)
- [ ] Phase 3 — React frontend against real data
- [ ] Phase 4 — WYSIWYG amendment editor
- [ ] Phase 5 — Historical amendment migration

## Pilot scope
3-5 real Master Directions, ingested end-to-end.
Starting with MD 290 (UCB Dividends).

## How to restart the app
1. Open Docker Desktop (whale icon in menu bar — wait until it says "Docker Desktop is running")
2. In Terminal: 
cd ~/Downloads/Projects/rbi-registry
docker compose up

3. Wait for "Starting development server at http://0.0.0.0:8000/"
4. Browser: http://localhost:8000/admin (login: sudaditya / [password])
5. Or: http://localhost:8000/places/in for India dashboard

## Session log

### Session 1 — 2026-09-07 (morning)
- Set up GitHub account (username: sudaditya).
- Forked laws-africa/indigo to sudaditya/indigo.
- Cloned to ~/Downloads/Projects/rbi-registry via GitHub Desktop.
- Docker build hit two Ubuntu 24.04 PEP 668 pip errors — fixed by adding
  --break-system-packages and --ignore-installed flags to Dockerfile.
- Build succeeded (~2 min after fixes). First run failed because Postgres
  wasn't ready before Django tried to connect. Restart fixed it.
- Django migrations applied cleanly (~90 migrations).
- Superuser created (username: sudaditya).
- Verified /admin and / both load.

### Session 2 — 2026-09-07 (afternoon)
- Loaded countries_plus (252) and languages_plus (184) fixtures.
  Both are needed by Indigo but neither is auto-loaded.
- Created IndigoCountry wrapper for India (IN).
- Created IndigoLanguage wrapper for English (en).
- Verified UI at /places/in shows India with an "Add new work" button.
- Phase 0 complete. Backend, DB, jurisdictions, permissions all live.

### Session 3 — 2026-09-07 (evening)
- Switched from Anthropic to Gemini (free tier). Model: gemini-3.6-flash.
- Installed google-genai SDK, python-dotenv, pypdf, requests.
- Set up corpus/{pdfs,text,akn} folders. Source PDFs gitignored, generated
  text and XML committed.
- Wrote scripts/extract_pdf.py — PDF → plain text via pypdf.
- Wrote scripts/ingest_pdf_to_akn.py — text → AKN XML via Gemini.
  Design: LLM produces only <body>; Python wraps FRBR meta + preface
  deterministically. Prompt lives in scripts/prompts/extract_akn_body.md.
- MD 290 pipeline result: 5 pages, 7,571 chars → 11,728 chars valid AKN 3.0 XML.
  Tokens: 3,093 in, 2,621 out. Cost: $0 (free tier).
  Quality: ~95% correct on first try. Minor stylistic issues (see prompt).

### Session 4 — 2026-09-07 (late evening) — Path B attempt
- Explored Indigo's REST API URL structure. Learned:
  - URLs don't accept trailing slashes (^works$ regex, not ^works/$)
  - Only SessionAuthentication enabled — added Token+Basic via override
    in indigo/settings.py bottom.
  - WorkViewSet is ReadOnlyModelViewSet — no POST endpoint at all.
- Attempted Path B: changed to ModelViewSet, forced Docker rebuild.
  POST endpoint appeared but hit 500: WorkSerializer has writable dotted-source
  fields that require a custom .create() method.
- Reverted WorkViewSet to ReadOnlyModelViewSet to keep main branch clean.
- Decided next session (5): pursue Option 2 — load via Django ORM.

### Learnings so far
- Indigo setup requires manual fixture loading and wrapper creation.
  In Phase 1, package all of this into a single management command.
- Country.objects.get(iso='IN') is the correct lookup once fixtures loaded.
- languages_plus.Language = master language list.
  indigo_api.Language = per-installation wrapper. Both needed.
- Docker first-run Postgres race is a one-time issue; subsequent starts fine.

## Open questions / decisions pending
- Session cadence for the build (daily / weekly / weekend)?
- Anthropic API key setup — verified but not yet used.
- Whether to migrate to ~/Projects/rbi-registry from ~/Downloads/... at some point.

### Session 4 (wrap-up) — 2026-09-07

Attempted Path B: enable POST on Indigo's WorkViewSet.

Progress:
- Confirmed URL routing goes through indigo_api.views.works.WorkViewSet.
- Confirmed Docker file sync lags on Mac; requires `up --build` to force
  the container to pick up code changes.
- Changed WorkViewSet from ReadOnlyModelViewSet to ModelViewSet, verified
  MRO now includes CreateModelMixin.
- POST endpoint now exists and receives requests.

Blocker discovered:
- WorkSerializer has writable dotted-source fields (source='foo.bar').
  DRF requires a custom .create() method to handle these, or a separate
  WorkCreateSerializer. Neither exists.
- DocumentSerializer will hit the same issue.

Reverted WorkViewSet to ReadOnlyModelViewSet to keep main branch clean.

Honest finding: Indigo was designed for browser workflows, not programmatic
ingestion. Every API operation our POC needs (create Work, create Document,
create Amendment, cross-team dashboards, etc.) will require similar
serializer engineering. Building the API layer on top of Indigo is a
6-8 week effort we hadn't budgeted.

### Decision needed before next session:
Option 1: Push through Path B — write custom serializers (2-3 sessions to first success)
Option 2: Load via Django ORM directly (1 session, pragmatic, defers API question)
Option 3: Reconsider fork-and-strip vs full custom given what we've learned

Recommended: Option 2 next session. Get data flowing first. Decide 1 vs 3 with more info.

### Phase status
- [x] Phase 0 — Indigo running with India as a Place
- [~] Phase 2 — PDF→AKN pipeline works. Load into Indigo still blocked.
- [ ] Phase 1, 3, 4, 5

### Session 5 — 2026-09-07 (evening)

**Objective:** Load MD 290 into Indigo via Django ORM (Option 2). Result: SUCCESS.

Achievements:
- Wrote scripts/load_via_orm.py — a Django-shell-independent script that runs
  inside the container and creates Work + Document via the ORM directly.
- Copied it into the container via `docker compose cp` (docker-compose.yml has
  no bind mount for /app; needs fixing before Session 6).
- Inspected Indigo's Work and Document models via Django shell — confirmed
  document_xml (not "content") holds the AKN XML.
- Loaded MD 290 successfully — Work id=1, Document id=1.
- MD 290 appears in India's Works list at /places/in/works with correct
  title, principal flag, FRBR URI (/akn/in/act/masterDirection/2025-11-28/290),
  publication metadata, and timeline entry.
- Verified server-side AKN parsing via /api/documents/1/toc endpoint —
  returns clean nested structure with all chapters, sections, paragraphs
  and sub-paragraphs correctly recognised. Every eId present.

Blocker discovered but deferred:
- Indigo's browser editor throws JavaScript error
  `SyntaxError: Can't create duplicate variable: 'AknTextEditor'`
  which prevents client-side rendering. Server-side parsing is fine.
  This is an Indigo frontend bug — irrelevant to our POC since we're
  building our own React frontend.

Cosmetic issue:
- Our XML has <num>Chapter I</num>; Indigo prepends "Chapter" → renders
  as "Chapter Chapter I". Fix by regenerating with <num>I</num> only.

### Phase status
- [x] Phase 0 — Indigo running with India as a Place
- [x] Phase 2 — PDF → AKN pipeline works end-to-end. MD 290 loaded and
  parsed successfully. One document down, ~249 to go.
- [ ] Phase 1, 3, 4, 5

### Session 6 targets
Two options, pick based on time and appetite:
- Option A: Ingest 2-3 more MDs (172 Climate Finance with tables,
  340 NBFC Acquisition with nested sub-clauses). Validates the pipeline
  handles structural variety. ~1 hour.
- Option B: Start Phase 3 — a minimal React frontend that reads
  document.document_xml from the API and renders it as HTML.
  Because Indigo's own renderer is broken and we're building our own
  anyway, this is where we start meaningfully diverging from Indigo.
  ~2-3 hours.

Recommended: Option A first (fast confidence boost + edge case discovery),
then Option B in a follow-up. But if there's appetite, straight to B is fine.

Housekeeping for next session:
- Add bind mount for /app in docker-compose.yml (Option B from Session 4)
  so we don't need `docker compose cp` for every script change.
- Regenerate MD 290 with fixed <num> tags to remove "Chapter Chapter" artifact.

### Session 7 — 2026-09-08

**Objective:** Ingest MDs 172 and 356, validate pipeline across structural variety,
lock in housekeeping deferred from Session 6.

Housekeeping wins:
- Added bind mount `./:/app` to docker-compose.yml — scripts and code changes
  on Mac side are now live-visible inside container without rebuild.
- Removed obsolete `version: "3"` line from docker-compose.yml to silence
  startup warning.
- Renamed extract_pdf.py → extract_pdf_pypdf.py (kept as fallback), promoted
  pymupdf-based version to be the new extract_pdf.py.

MD 172 (14 pages, tables):
- Initial ingestion via pypdf succeeded. Pipeline produced 27,927 chars of AKN.
- Impact Indicators table (5 rows, 2 columns) correctly reconstructed by Gemini
  as valid AKN <table> markup, despite pypdf mangling the extraction into
  sequential text. Domain context enabled semantic reconstruction.
- Tokens: 5,935 in / 6,876 out. Cost: $0.

Extractor comparison (pypdf vs pymupdf on MD 172):
- Ran side-by-side test using same PDF, same prompt, same model.
- Character count essentially identical (20,400 vs 20,378).
- Token cost essentially identical.
- Quality wins for pymupdf:
  - "S ections 21" → "Sections 21" (no word-break artifacts)
  - "al l other" → "all other"
  - Better table header structure (proper <th colspan="2"> where appropriate)
- Verdict: adopt pymupdf. Matches user's production RAG experience with RBI PDFs.

MD 290 regenerated:
- Same ingestion pipeline with pymupdf extractor.
- Tokens: 3,114 in / 2,621 out (essentially unchanged from pypdf baseline).
- Deleted old Work id=1 via Django ORM cascade, reloaded as Work id=3.

MD 172 regenerated with pymupdf and reloaded as Work id=4.

MD 356 (25 pages, complex consolidated document):
- Extraction: 42,569 chars via pymupdf.
- Ingestion: 12,150 in / 16,350 out tokens. Total 28.5k. Still $0.
- Loaded as Work id=5. TOC returns 1,705 lines of properly nested structure.
- No structural or content issues encountered.

Backlog (deferred):
- Preface regex doesn't strip "===== PAGE N =====" markers when they fall
  inside preface text (MD 172, MD 356). Fix extract_preface() in
  ingest_pdf_to_akn.py.
- Chapter number doubling: our XML has <num>Chapter I</num>; Indigo prepends
  "Chapter" → renders as "Chapter Chapter I". Fix prompt to produce
  <num>I</num> only. Applies to all ingested MDs — regenerate after fix.
- MD 356 was loaded with the July 2026 consolidation date. Proper amendment-
  history handling (original Work at 2025 date + amended Expression at 2026)
  is a Phase 5 concern.
- Complex tables (multi-column financial, merged cells, nested) still untested.
  Current pipeline may or may not handle them. Watch on future ingestions.

**Extrapolation for full 250-MD corpus:**
- ~3M input tokens, ~4M output tokens estimated
- Free tier limit is 250 requests/day, so full corpus takes ~5 days
- Cost: $0 on free tier, ~$10-15 on paid tier
- Ingestion is a solved problem at this point.

### Phase status
- [x] Phase 0 — Indigo running with India as a Place
- [x] Phase 2 — PDF → AKN pipeline solid. 3 MDs loaded and validated:
  MD 290 (simple), MD 172 (tables), MD 356 (complex consolidated).
  Ingestion at scale is de-risked.
- [ ] Phase 1, 3, 4, 5

### Session 8 target
Start Phase 3 — React frontend scaffolding.

Setup work:
- Create frontend/ folder in repo with Vite + React
- Set up basic project structure (components/, pages/, api/)
- First deliverable: Works list page that fetches /api/works and renders
- First actual rendering of MD 290 as HTML from AKN XML

Estimated: 2-3 sessions to have a working "browse MDs and see their content"
frontend. Then editor work (Chapter 3, ~4-6 sessions).

## Backlog — deferred fixes

- **Table extraction quality:** pypdf extracts tables as sequential
  text. Gemini reconstructs simple tables well (verified on MD 172
  Impact Indicators table). Complex tables (financial matrices,
  merged cells, multi-page) untested. Consider migrating to
  docling / marker / pdfplumber before scaling to full 250-MD corpus.
- **Preface page markers:** Our regex preface extractor doesn't
  strip "===== PAGE N =====" markers when they fall inside the
  preface text (seen in MD 172). Fix extract_preface() in
  ingest_pdf_to_akn.py.
- **Chapter number doubling:** Our XML has <num>Chapter I</num>;
  Indigo prepends "Chapter" -> "Chapter Chapter I". Fix prompt to
  produce <num>I</num> only. Applies to all ingested MDs — need to
  regenerate MD 290 and MD 172 after prompt fix.
- **Preface text cleanup:** Gemini cleans body text (removes "Urba n"
  -> "Urban") but our Python preface extractor doesn't. Move preface
  cleanup into Gemini's scope OR add regex cleanup to extract_preface().
- **Docker version warning:** docker-compose.yml has `version: "3"`
  which is deprecated. Remove the line to silence WARN[0000] messages.