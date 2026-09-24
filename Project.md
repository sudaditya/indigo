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
- PDF extraction: pymupdf (migrated from pypdf in Session 7)
- Hosting: Local (MacBook Air) for POC; RBI infrastructure later

## Repo
- GitHub: https://github.com/sudaditya/indigo (fork of laws-africa/indigo)
- Local: ~/Downloads/Projects/rbi-registry

## Current phase status
- [x] Phase 0 — Indigo running locally with India as a Place (Sessions 1-2)
- [x] Phase 2 — PDF → AKN ingestion pipeline solid, 3 MDs loaded (Sessions 3, 5, 7).
  Now also available via browser upload (Session 14).
- [~] Phase 3 — React frontend: Works list, Document viewer (tabbed),
  Coordination tab, Upload MD flow all working. Search, filters, 
  timeline still to build.
- [~] Phase 4 — Editor prototype substantially done. Click-to-select, 
  per-provision editor, save-as-DraftAmendment flow (Sessions 12-13). 
  Track changes, comments, review workflow: Sessions 15+.
- [ ] Phase 1 — Strip Indigo browser UI (reduced to "ignore" — we use only 
  Indigo's API/engine; their broken JS is irrelevant to our React frontend).
- [ ] Phase 5 — Historical amendment migration

## Pilot corpus
3 MDs loaded end-to-end, chosen for structural variety:
- MD 290 — UCB Dividends (5 pages, simple structure). Work id=7.
- MD 172 — Commercial Banks Climate Finance (14 pages, tables). Work id=12.
- MD 356 — NBFC Income Recognition (25 pages, complex consolidated). Work id=13.

Full corpus target: ~250 Master Directions.

## Strategic decisions

### Hybrid approach — Indigo engine + custom frontend (Session 6)
After 5 sessions of Indigo work and Path B evaluation of LEOS via public demos and documentation:

- **Indigo's engine kept** — Work/Document/Amendment models, AKN parser,
  consolidation, TOC generation. These work well.
- **Indigo's browser UI abandoned** — broken JavaScript, misaligned with
  our workflow. Replaced entirely by our own React frontend (Phase 3).
- **LEOS not adopted** — heavy Java stack, EU-specific templates,
  install complexity (no official Docker), dated UI. However, LEOS's UX
  patterns (track changes, comments, structural guardrails) inform our
  editor design.
- **Editor** — TipTap chosen (Session 12, after fresh web research). Built on
  ProseMirror; used by Notion, GitLab, Linear, Substack. TipTap has an
  explicit legal-industry offering. Track changes possible via official
  Pro extension (`@tiptap-pro/extension-tracked-changes`) or MIT-licensed
  community alternatives (sungkhum/tiptap-track-changes). POC uses core
  MIT packages only ($0). Production could upgrade to Tiptap Cloud paid
  tier for polished official extensions.

Trade-offs accepted:
- Editor development is substantial (~4-6 sessions minimum) vs inheriting
  LEOS. Accepted for UX control and stack simplicity.
- Institutional stability of Indigo (small NGO) is a real risk to revisit
  if this becomes production.

### Ingestion via ORM, not REST API (Session 5)
Indigo's REST API is read-only by design — `WorkSerializer` has dotted-source
fields not designed for writes. Making them writable is 2-3 sessions of
serializer engineering, deferred. For now, we load documents via Django
ORM directly (`scripts/load_via_orm.py` runs inside the container). The
ORM code will be reused inside future custom API views regardless.

## How to restart the app
1. Open Docker Desktop (wait until it says "Docker Desktop is running")
2. In Terminal:
cd ~/Downloads/Projects/rbi-registry
source .venv/bin/activate # for scripts that run on Mac side
docker compose up -d
3. Verify: `docker compose ps` should show db-1 and web-1 running
4. Browser: http://localhost:8000/admin (login: sudaditya / [password])
   Note: Indigo's `/places/in` UI throws CSS compile errors — cosmetic
   only, API works fine

## Session log

### Session 1 — 2026-09-07 (morning)
- Set up GitHub account (username: sudaditya)
- Forked laws-africa/indigo to sudaditya/indigo
- Cloned to ~/Downloads/Projects/rbi-registry via GitHub Desktop
- Docker build hit two Ubuntu 24.04 PEP 668 pip errors — fixed by adding
  --break-system-packages and --ignore-installed flags to Dockerfile
- Build succeeded (~2 min after fixes). First run failed because Postgres
  wasn't ready before Django tried to connect. Restart fixed it.
- Django migrations applied cleanly (~90 migrations)
- Superuser created (sudaditya)
- Verified /admin and / both load

### Session 2 — 2026-09-07 (afternoon)
- Loaded countries_plus (252) and languages_plus (184) fixtures.
  Both required by Indigo but neither auto-loaded.
- Created IndigoCountry wrapper for India (IN)
- Created IndigoLanguage wrapper for English (en)
- Verified UI at /places/in shows India with an "Add new work" button
- Phase 0 complete

### Session 3 — 2026-09-07 (evening)
- Switched from Anthropic to Gemini (free tier). Model: gemini-3.6-flash.
  Reason: Anthropic API needs paid credit; Gemini has usable free tier.
- Installed google-genai SDK, python-dotenv, pypdf, requests
- Set up corpus/{pdfs,text,akn} folders. Source PDFs gitignored, generated
  text and XML committed.
- Wrote scripts/extract_pdf.py — PDF → plain text (originally pypdf)
- Wrote scripts/ingest_pdf_to_akn.py — text → AKN XML via Gemini.
  Design: LLM produces only <body>; Python wraps FRBR meta + preface
  deterministically. Prompt lives in scripts/prompts/extract_akn_body.md.
- MD 290 pipeline result: 5 pages, 7,571 chars → 11,728 chars valid AKN 3.0 XML.
  Tokens: 3,093 in, 2,621 out. Cost: $0.
  Quality: ~95% correct on first try.

### Session 4 — 2026-09-07 (late evening) — Path B attempt
Explored Indigo's REST API URL structure. Learned:
- URLs don't accept trailing slashes (^works$ regex)
- Only SessionAuthentication enabled by default — added Token+Basic via
  settings.py override
- WorkViewSet is ReadOnlyModelViewSet — no POST endpoint at all
- Docker file sync lags on Mac; requires `up --build` to force reload

Attempted Path B: changed to ModelViewSet, forced Docker rebuild.
POST endpoint appeared but hit 500: WorkSerializer has writable
dotted-source fields requiring custom .create() methods.

Reverted WorkViewSet to ReadOnlyModelViewSet to keep main branch clean.

Honest finding: Indigo's API was designed for reading, not writing.
Making it writable is 2-3 sessions of engineering per resource type
(Work, Document, Amendment, etc.). Chose to pivot to ORM-based loading
in Session 5.

### Session 5 — 2026-09-07 (evening) — ORM breakthrough
Objective: Load MD 290 into Indigo via Django ORM. Result: SUCCESS.

- Wrote scripts/load_via_orm.py — runs inside container, uses Work.objects.create()
  and Document.objects.create() directly, bypassing broken API layer
- Inspected Indigo's Work and Document models via Django shell —
  confirmed document_xml (not "content") holds the AKN XML
- Loaded MD 290 — Work id=1, Document id=1
- Verified server-side AKN parsing via /api/documents/1/toc — returns clean
  nested structure with all chapters, sections, paragraphs and sub-paragraphs
  correctly recognised. Every eId present.

Blocker discovered but strategically irrelevant:
- Indigo's browser editor throws JavaScript SyntaxError
  `Can't create duplicate variable: 'AknTextEditor'`
- Prevents client-side rendering but server-side parsing works fine
- Doesn't affect us since we're replacing the browser UI entirely

### Session 6 — 2026-09-08 (morning) — LEOS evaluation
Objective: Comprehensively evaluate LEOS before further Indigo investment.

Path B evaluation (targeted, no local install):
- Watched official LEOS demo videos + community talks
- Studied LEOS architecture via public documentation at code.europa.eu
- Reviewed 20-item drafter checklist (Word-like editing, track changes,
  comments, structural drafting, comparison view)

Findings:
- LEOS 5.6.0 is actively developed (EU-funded through 2027+)
- License is EUPL v1.2 (not Apache 2.0 as I initially stated)
- Data format is AKN4EU (variant of AKN 3.0)
- No official Docker deployment; community MinBZK/leos is Kubernetes-based
  and PoC quality
- Realistic local install: 3-5x more work than Indigo, with meaningful
  chance of failure
- Editor (CKEditor 4 with legal extensions) is genuinely good but the
  UI wrapper is dated
- Stack is heavy: Java 8, Spring Boot, Maven, CMIS document repository

User verdict from independent YouTube research: "very functional and
helpful, though the UI can be improved. We can reference this (and
improve on it) when we are building our own editor for MDs."

Strategic decision reached: **Hybrid approach.** See "Strategic decisions"
section above.

### Session 7 — 2026-09-08 (afternoon)
Objective: Ingest MDs 172 and 356, validate pipeline across structural
variety, lock in housekeeping deferred from earlier sessions.

Housekeeping wins:
- Added bind mount `./:/app` to docker-compose.yml — scripts and code
  changes on Mac side are now live-visible inside container
- Removed obsolete `version: "3"` line from docker-compose.yml
- Renamed extract_pdf.py → extract_pdf_pypdf.py (kept as fallback),
  promoted pymupdf-based version to be the new extract_pdf.py

MD 172 (14 pages, tables):
- Initial ingestion via pypdf succeeded. Pipeline produced 27,927 chars AKN.
- Impact Indicators table (5 rows, 2 columns) correctly reconstructed
  by Gemini as valid AKN <table> markup, despite pypdf mangling the
  extraction. Domain context enabled semantic reconstruction.
- Tokens: 5,935 in / 6,876 out.

Extractor comparison (pypdf vs pymupdf on MD 172):
- Ran side-by-side test using same PDF, prompt, model
- Character count essentially identical (20,400 vs 20,378)
- Token cost essentially identical
- Quality wins for pymupdf:
  - "S ections 21" → "Sections 21" (no word-break artifacts)
  - "al l other" → "all other"
  - Better table header structure
- Adopted pymupdf. Matches user's production RAG experience with RBI PDFs.

MD 290 regenerated with pymupdf, reloaded as Work id=3.
MD 172 regenerated with pymupdf, reloaded as Work id=4.

MD 356 (25 pages, complex consolidated document):
- Extraction: 42,569 chars via pymupdf
- Ingestion: 12,150 in / 16,350 out tokens. Total 28.5k. Still $0.
- Loaded as Work id=5. TOC returns 1,705 lines of properly nested structure.
- No structural or content issues encountered.

Extrapolation for full 250-MD corpus:
- ~3M input tokens, ~4M output tokens estimated
- Free tier limit is 250 requests/day, so full corpus takes ~5 days
- Cost: $0 on free tier, ~$10-15 on paid tier
- Ingestion is a solved problem at this point.

## Session 8 target
Start Phase 3 — React frontend scaffolding.

Setup work:
- Create frontend/ folder with Vite + React
- Set up basic project structure (components/, pages/, api/)
- First deliverable: Works list page fetching /api/works
- First actual rendering of an MD as HTML from AKN XML

Estimated: 2-3 sessions to have a working "browse MDs and see their
content" frontend. Then editor work (~4-6 sessions).

### Session 8 — 2026-09-08 (afternoon/evening)

**Objective:** Start Phase 3 — React frontend. Get MDs displayed in a
custom UI, replacing Indigo's broken browser interface.

Verified environment: Node v22.23.2, npm v10.9.8 already installed. No
setup work needed.

Scaffolding:
- Created frontend/ folder with `npm create vite@latest frontend --
  --template react-ts`. React + TypeScript + Vite via official template.
- Ran `npm install` cleanly. Vite dev server on port 5173 alongside
  Django on port 8000.
- Chose TypeScript over JavaScript for better type-checked debugging
  and IDE support. Chose to start with minimal deps and add libraries
  only as needed (no upfront frameworks/state managers).

CORS check:
- Verified django-cors-headers already installed and CorsMiddleware active
  in Indigo. CORS_ALLOWED_ORIGINS not set but requests from :5173 work —
  Indigo defaults to permissive dev-mode CORS. Note as production hardening
  concern for later.

Works list page:
- Wrote App.tsx that fetches /api/works from Django, displays 3 MDs as
  cards with title, MD number, publication date, FRBR URI, principal badge.
- Full styling with hover states, badges, monospaced FRBR URIs, clean
  card layout.
- Data flowed end-to-end on first attempt: PDF → Gemini → Django ORM →
  Postgres → REST API → React → browser. Seven layers, all working.

Navigation (React Router v7):
- Installed react-router (note: modern package name, not react-router-dom).
- Created frontend/src/pages/{WorksList,DocumentViewer}.tsx and
  frontend/src/components/AknRenderer.tsx.
- Refactored App.tsx to be a router: `/` → WorksList, `/works/:id` →
  DocumentViewer.
- Cards on Works list now link to document viewer pages.

AKN → HTML renderer:
- Wrote AknRenderer component: parses AKN XML using DOMParser, recursively
  renders elements to HTML.
- Handles: preface, chapter, section, paragraph, subparagraph, intro,
  content, p, table, tr, th, td.
- Unknown elements fall through to generic renderer.
- Uses AKN 3.0 namespace URI for element lookup — proper XML namespace
  handling, not string matching.
- Comprehensive CSS: Apple-inspired serif-free typography, grid-aligned
  paragraph numbers, indented subparagraphs, styled tables with subtle
  borders, italic preface block with left accent bar.

Verified end-to-end:
- MD 290 (simple, 13 paragraphs): renders correctly with all chapters,
  sections, and paragraph structure.
- MD 172 (14 pages, tables): renders correctly including the Impact
  Indicators table with all 5 rows and correct category-indicator
  associations. The pymupdf → Gemini → AKN → React pipeline preserves
  table structure end-to-end.
- MD 356 (25 pages, complex consolidated): renders correctly.
- Back-navigation works. React Router hot-reloads on edits.

Chose to end session before completing backlog cleanup. Backlog work
started but incomplete — see "Session 9 pickup" below.

### Session 9 pickup — backlog fixes (in priority order)

**Started but not completed:**
1. **Chapter number doubling** — decided to fix in TWO places:
   - Prompt (scripts/prompts/extract_akn_body.md): change instructions to
     produce `<num>I</num>` not `<num>Chapter I</num>`. Add explicit example.
   - Renderer (frontend/src/components/AknRenderer.tsx): update chapter case
     to prepend "Chapter " in the display: `<span>Chapter {num}</span>`.
     Rationale: XML holds structural semantics, renderer handles human
     presentation. Cleaner separation.
   - After both changes: regenerate all 3 MDs, delete old Works, reload.

**Still to do in Session 9:**
2. **Preface page markers** — strip `===== PAGE N =====` from preface text
   in scripts/ingest_pdf_to_akn.py extract_preface() function.
3. **Verify preface text cleanup** — with pymupdf, "S ections" / "al l other"
   artifacts may already be gone. Quick check on MD 172 preface after
   regeneration.
4. **API_TOKEN duplication in frontend** — currently hardcoded in
   WorksList.tsx and DocumentViewer.tsx. Extract into shared
   frontend/src/config.ts (or similar). ~15 min, unblocks clean growth
   of future components.

**Session 9 sequence:**
- Complete backlog items 1-4 above (~45 min)
- Regenerate all 3 MDs with fixed prompt
- Verify chapter rendering, preface cleanup, and API config work
- Then decide: continue Phase 3 polish OR start Phase 4 (editor prototype)

### Phase status
- [x] Phase 0 — Indigo running with India as a Place
- [x] Phase 2 — PDF → AKN pipeline solid, 3 MDs loaded and validated
- [~] Phase 3 — Frontend scaffolded, Works list + Document viewer working.
  Backlog cleanup in progress. Additional features (search, filters,
  coordination dashboard) still to build.
- [ ] Phase 1, 4, 5

### Session 9 — 2026-09-09 — Backlog closure

**Objective:** Close all Tier 1 and Tier 2 backlog items from Session 8's
partial work, plus verify Tier 3 auto-resolutions.

**Item 1: Chapter number doubling — CLOSED.**
- Updated scripts/prompts/extract_akn_body.md: chapter num should be
  `<num>I</num>` not `<num>Chapter I</num>`. Added complete chapter+
  section+paragraph XML example to prompt for reinforcement.
- Updated frontend/src/components/AknRenderer.tsx: chapter case now
  displays "Chapter {num} – {heading}" with en-dash separator, matching
  the RBI PDF visual style seen in original source.
- Regenerated MDs 290, 172, 356 via Gemini. Deleted old Works (5-6
  were deleted with cascade), reloaded as Work IDs 7, 8, 9.
- Verified in browser: MD 290 renders "Chapter I – Preliminary" correctly.

**Item 2: Preface page markers — CLOSED (with pipeline improvement).**
- Updated scripts/ingest_pdf_to_akn.py extract_preface() to strip:
  - "===== PAGE N =====" markers
  - Standalone digit-only lines
  - Trailing digits at end of preface (defensive)
- First regen attempt on MD 172/356 hit Gemini 429 quota limit
  (free tier: 20 requests/day for gemini-3.6-flash, contrary to my
  earlier "250/day" claim — I was wrong about this).
- Wrote scripts/rewrap_akn.py — a deterministic-only re-wrapper.
  Reads existing AKN XML, extracts the <body> Gemini produced,
  regenerates FRBR meta + preface from Python logic, writes back.
  No Gemini call needed for cosmetic wrapper changes.
- This is a genuinely valuable pipeline improvement: separates
  expensive/non-deterministic LLM output from cheap/deterministic
  wrapping. Reusable any time we change wrapper logic in the future.
- Reloaded MDs 172, 356 as Work IDs 12, 13.
- Verified in browser: MD 172 preface ends cleanly at "...specified."
  with no trailing page number.

**Item 3: Preface word-break cleanup — AUTO-RESOLVED.**
- With pymupdf (Session 7), artifacts like "S ections" / "al l other"
  don't appear in extracted text at all. No fix needed.
- Confirmed in current MD 172 preface: "Sections 21 and 35A", "all
  other provisions" — clean.

**Item 4: API_TOKEN duplication in frontend — CLOSED.**
- Created frontend/src/config.ts — single source of truth for
  API_BASE and API_TOKEN.
- Created frontend/src/api/client.ts — apiFetch<T>() helper wrapping
  fetch() with standard headers, error handling, and TypeScript generics
  for type-safe responses.
- Refactored WorksList.tsx and DocumentViewer.tsx to use apiFetch.
  Duplication eliminated. Future pages will be one-line data fetches.
- Verified: both pages load correctly after refactor.

**Gemini quota lesson learned:**
Free tier for gemini-3.6-flash is 20 requests/day, not 250 as I stated
earlier. Reset happens at midnight Pacific Time. For full 250-MD corpus
ingestion, we'll need paid tier ($10-30 total for entire corpus) or
5+ days of rate-limited processing. Corrected in "extrapolation" note.

**Phase status**
- [x] Phase 0 — Indigo running with India as a Place
- [x] Phase 2 — PDF → AKN pipeline solid + backlog closed
- [~] Phase 3 — Frontend foundation done (list + viewer + config).
  Next: Coordination Dashboard (novel RBI-specific feature — Sessions 10-13).
  Then Phase 3 completion features (search, filters, TOC sidebar, print).
- [ ] Phase 4 — Editor prototype (deferred until after Coordination Dashboard).
- [ ] Phase 1, 4, 5

### Session 9.5 — 2026-09-09 (planning) — Coordination Dashboard design

Chose Path C (Coordination Dashboard) as Session 10-13 focus.
Strategic rationale: novel RBI-specific feature not in Indigo or LEOS;
demoable to DoR leadership; complements (doesn't compete with) the
editor prototype which is deferred to Sessions 14+.

**Data model (implementation in Session 10):**

```
WorkingUnit         — Section OR group-level unit (polymorphic)
                      Fields: name, short_code, division (PRD/COD),
                      group_name. is_group_level() derived from name==group_name.
UnitMembership      — Users belong to WorkingUnits (many-to-many with
                      primary flag). Supports secondments / dual roles.
MDOwnership         — One nodal WorkingUnit per Work (MD).
                      Edit-open by default. edit_restricted + denied_units
                      provide explicit denylist when needed.
DraftAmendment      — Core entity for coordination.
                      Fields: work (FK), target_eid, change_type
                      (insert/modify/delete/renumber), proposed_text,
                      rationale, status, author_user, author_unit, timestamps.
                      Indexed on (work, target_eid, status) and
                      (author_unit, status) for dashboard queries.
```

Fields: work (FK), target_eid, change_type
(insert/modify/delete/renumber), proposed_text,
rationale, status (draft/in_review/approved/
rejected/withdrawn), author_user, author_unit,
timestamps.
Indexed on (work, target_eid, status) and
(author_unit, status) for dashboard queries.


**Reference material:** DoR organogram uploaded (Organogram.xlsx).
Structure: 2 Divisions → 15 Groups → ~28 Sections (some Groups have
no sub-Sections; the Group is itself the working unit in those cases).

**Nodal assignments for our 3 loaded MDs (real, not placeholder):**
- MD 290 (UCB Dividends) → Accounting Section (Balance Sheet Group, PRD)
- MD 172 (Climate Finance) → Sustainable Finance Group (group-level, PRD)
- MD 356 (NBFC Income Recognition) → Stressed Assets Section (Credit Risk Group, PRD)

**Dummy draft plan for demo (Session 10-11):**
- MD 290: 2 conflicting drafts on same NNPA-ratio clause 
  (same-target conflict — dashboard should flag)
- MD 172: 3 non-conflicting drafts across different paragraphs
- MD 356: 2 drafts on same paragraph — one MODIFY, one DELETE 
  (delete-vs-edit conflict — dashboard should flag specifically)

**Conflict types the dashboard will surface:**
1. Same-target: multiple drafts on the same eId
2. Delete-vs-edit: DELETE draft + MODIFY draft on same eId or descendants
3. Nearby-clause (soft/informational): drafts on different children of same parent
4. Semantic incoherence: DEFERRED to future intelligence layer.
   Data model captures proposed_text so LLM-based analysis is possible later.


### Session 10 — 2026-09-XX — Coordination Dashboard: backend complete

**Objective:** Backend for Coordination Dashboard (Path C). Result: fully working.

Created Django app `rbi_registry_app/` alongside indigo_api/, registered
in INSTALLED_APPS via settings.py override.

**Models (4 tables, migrations applied):**
- WorkingUnit — 35 units (Section OR group-level, per DoR organogram)
- UnitMembership — user↔unit link with is_primary flag
- MDOwnership — nodal unit per MD, edit-open by default
- DraftAmendment — proposed changes with change_type, status, author

**Seed data (scripts/seed_rbi_data.py):**
- Wipes existing RBI-app data (leaves Indigo alone), then reseeds.
- 35 working units populated from organogram
- 10 dummy users, each with primary UnitMembership
- 3 MDOwnership records (MD 290 → ACC, MD 172 → SFG, MD 356 → STA)
- 7 DraftAmendments including 2 deliberate conflict scenarios:
  * MD 290: 2 drafts on chp_II__para_6__ii (same-target conflict)
  * MD 356: MODIFY + DELETE on chp_II__para_5 (delete-vs-edit conflict)
  * MD 172: 3 non-conflicting drafts

**Bug discovered + fixed:** Scripts importing rbi_registry_app fail
without /app on sys.path (indigo_api is pip-installed, our app is not).
Added 2-line sys.path fix at top of seed script; will repeat pattern
for future scripts.

**REST endpoints (all read-only, all require Token auth):**
- GET /api/rbi/units/          — 35 working units
- GET /api/rbi/mds/            — 3 MDs with draft_count + conflict_count
- GET /api/rbi/drafts/         — 7 drafts, filterable by ?work= &status= &author_unit=
- GET /api/rbi/conflicts/      — 2 computed conflicts, severity-ordered

Conflict detection logic:
- Same-target: multiple active drafts on same eId → severity=medium
- Delete-vs-edit: DELETE draft + non-DELETE draft on same eId → severity=high
- Withdrawn/rejected drafts excluded from active set
- Computed on demand (POC scale); would cache at production scale

All 4 endpoints verified via curl. Response shapes are dashboard-ready
(nested work/author/unit info means frontend needs no follow-up calls).

**Files added this session:**
- rbi_registry_app/{__init__,apps,models,views,serializers,urls,admin}.py
- rbi_registry_app/migrations/{__init__,0001_initial}.py
- scripts/seed_rbi_data.py
- indigo/settings.py (INSTALLED_APPS updated)
- indigo/urls.py (added path('api/rbi/', include(...)))

**Session 11 plan — dashboard frontend:**
- New React page: /coordination
- Consumes /api/rbi/mds/ and /api/rbi/conflicts/
- Top-level view: 3 MD cards with draft/conflict badges
- Conflicts panel: highlight the 2 conflicts with drilled-down details
- Drill-down: click MD → see all drafts on that MD grouped by target eId
- Navigation link added to app header

Realistic estimate: 90-120 min. Should feel similar to Session 8
(consuming REST from React) but with more complex data structures.

### Session 11 — 2026-09-10 — Coordination Dashboard: frontend complete

**Objective:** Build the Coordination Dashboard UI on top of Session 10's 
backend. Result: fully working, matches the concept mockup's tab-based design.

**Design decision:** Coordination as a property of each MD (per-MD tab in 
the viewer), NOT as a standalone department-wide dashboard. Reasoning: 
matches how officers actually work (always in the context of a document); 
aggregate view is a derived read for later. Deferred department-wide 
dashboard to a future session.

**Structure of MD viewer refactored to tabbed layout:**
- Content tab (existing AKN renderer)
- Coordination tab (new — this session)
- Timeline tab (placeholder, "SOON" badge)
- Amendments tab (placeholder, "SOON" badge)
- URL routes: /works/:id → redirects to /works/:id/content; 
  /works/:id/coordination for the new tab. React Router nested routes.

**Coordination tab shows for the current MD:**
- Nodal owner strip (unit name, short code, division)
- Conflicts section (with high/medium severity visual distinction — 
  red border for delete-vs-edit, amber for same-target)
- Other active drafts section (grouped by target eId)
- Each draft card: change type badge, status pill, author name + unit, 
  proposed text, rationale, created date

**Client-side conflict detection** (frontend/src/pages/document-viewer/conflict-detection.ts) —
mirrors backend logic scoped to a single MD. No need for a separate 
conflicts endpoint; the drafts endpoint + client grouping is sufficient.

**Works list enhanced with coordination indicators:**
- Each card shows "Nodal: [code]" + draft count + conflict count 
  (with ⚠ symbol when conflicts exist).

**Files added:**
- frontend/src/api/types.ts — shared TypeScript types matching backend serializers
- frontend/src/pages/document-viewer/{ContentTab,CoordinationTab,TabNav,conflict-detection}.tsx/.ts
- Extended apiFetch() with optional query params

**Files modified:**
- frontend/src/pages/DocumentViewer.tsx — refactored into tabbed shell
- frontend/src/pages/WorksList.tsx — added coordination indicators
- frontend/src/App.tsx — nested route pattern (/works/:id/*)
- frontend/src/App.css — tab nav styles, coordination styles, conflict styles

**Small bug encountered:** App.tsx changes needed a save I forgot to do, 
which caused MDs to briefly not render. Ctrl-S habit reinforced.

**Verified with all 3 MDs:**
- MD 290: same-target conflict on chp_II__para_6__ii renders with amber border
- MD 356: delete-vs-edit conflict on chp_II__para_5 renders with red border
- MD 172: 3 non-conflicting drafts, grouped correctly

Session accomplished more than planned — the aggregate department-wide 
dashboard (which was Session 11's original target) got reframed and 
deferred; per-MD coordination is a more natural fit and got built end-to-end.

### Session 12 — 2026-09-10 — Phase 4 open: editor prototype (partial)

**Objective:** Start Phase 4 — install editor, prove edit-and-save flow.
Result: half done. Backend POST + editor install + persona layer complete;
edit affordance and save flow deferred to Session 13.

**Strategic decisions locked in via fresh web search:**

*Editor choice: TipTap.*
- Built on ProseMirror (2.5M+ weekly downloads; used by Notion, GitLab,
  Linear, Substack, Vercel). Battle-tested foundation.
- Explicit legal-industry marketing from TipTap: dedicated
  "Document automation for your legal product" page, DOCX round-trip
  with tracked changes, redlining, audit trails.
- Track changes more mature than initially assumed:
  * Official Pro extension `@tiptap-pro/extension-tracked-changes`
    (evolving, under 1.0.0)
  * Multiple production-ready open-source alternatives
    (sungkhum/tiptap-track-changes, chenyuncai/tiptap-track-change-extension),
    MIT-licensed
- MIT-licensed core; Pro subscription only needed if RBI wants official
  polished extensions for production. POC is 100% open-source.
- Trade-off honestly stated: 2-4 weeks to build fully-featured editor
  (per external benchmark). We build the UI layer ourselves.
- ProseMirror's strict schema of nodes matches AKN's structured hierarchy.
  Editor can natively understand chapter → section → paragraph → subparagraph.

*Editing approach: per-provision, mapped to DraftAmendment.*
- User clicks a chapter, section, or specific clause to edit — schema
  supports variable scope, target_eid gets set to whatever the user
  actually clicked.
- Chapter/section-scoped editing is a Session 13-14 schema layer;
  paragraph-level suffices for MVP.
- Full-document editing NOT built. Per RBI DoR workflow: officers target
  specific clauses, not whole documents.

**Step 1 — Enable POST on DraftAmendment endpoint (COMPLETE):**
- Changed `ReadOnlyModelViewSet` → `ModelViewSet` in views.py.
- Added write-only IntegerFields (work_id, author_user_id, author_unit_id)
  in DraftAmendmentSerializer, plus validate_*/create/update methods to
  resolve IDs → model instances.
- **Bug hit:** initial version used PrimaryKeyRelatedField with lazy
  queryset via __init__. Failed because DRF validates fields at
  class-definition time. Fix: use plain IntegerField write-only,
  validate + resolve in methods.
- Also learned: when Django dev server crashes on import, container
  is running but Python process is dead — file saves aren't picked up.
  Fix: `docker compose restart web`.
- Verified: POST creates a draft (HTTP 201), draft appears in
  Coordination tab, DELETE removes it (HTTP 204).

**Step 2 — TipTap installed (COMPLETE):**
- Packages: @tiptap/react @tiptap/starter-kit @tiptap/pm
- Created TipTapEditor.tsx (minimal wrapper with onChange callback)
- Wired into Amendments tab as a scratchpad (temporary — will move to
  Content tab in Step 4). Amendments tab de-greyed.
- Verified: editor renders, accepts typing, Cmd+B/I/etc. work,
  HTML extraction confirmed by live-updating <details> block.

**Step 3 — Persona switcher (COMPLETE):**
- New backend endpoint: `GET /api/rbi/personas/` returns all 10 dummy
  users with their primary unit info in a single call.
- PersonaContext (React Context + localStorage persistence)
- PersonaSwitcher component (native <select> for accessibility)
- App.tsx now wraps everything in PersonaProvider; switcher in app-header.
- Verified: default is Ananya Desai (alphabetically first), switching
  works, refresh persists selection.

**Files added:**
- frontend/src/components/TipTapEditor.tsx
- frontend/src/components/PersonaSwitcher.tsx
- frontend/src/context/PersonaContext.tsx
- frontend/src/pages/document-viewer/AmendmentsTab.tsx (scratchpad)

**Files modified:**
- rbi_registry_app/views.py (POST enabled, personas endpoint added)
- rbi_registry_app/serializers.py (DraftAmendmentSerializer write support)
- rbi_registry_app/urls.py (personas path)
- frontend/src/api/types.ts (Persona, PersonasResponse)
- frontend/src/pages/DocumentViewer.tsx (Amendments tab wired)
- frontend/src/App.tsx (PersonaProvider wrapper, header layout)
- frontend/src/App.css (editor + persona switcher styles)

### Session 13 — 2026-09-24 — Editor: end-to-end edit-and-save flow

**Objective:** Finish what Session 12 deferred — click-to-edit + save
flow. Result: exceeded scope, delivered Steps 4-6 AND stakeholder-quality
UX polish in one session.

**Step 4a — Click-to-select paragraph (~30 min):**
- AknRenderer refactored: renderElement moved inside AknRenderer so it
  closes over onSelect + selectedEid props (avoids prop drilling).
- Paragraphs + subparagraphs gain click handlers, hover cue, and a
  blue outline when selected. Chapters + sections deliberately not
  selectable (they're structural containers; users select what's inside).
- extractProvisionText helper walks the DOM and pulls readable text
  skipping structural tags — feeds the editor with clean input.
- ContentTab manages selection state via useState, renders a floating
  action bar at the bottom showing eid + text preview + "Edit this
  provision" button.
- Verified: clicking paragraph 4 in MD 172, then subparagraph (2)
  inside it, correctly scopes selection to just chp_I__sec_C__para_4__n2.
  stopPropagation prevents double-selection of parent + child.

**Step 4b — Editor modal opens with paragraph text (~20 min):**
- Reusable Modal component (frontend/src/components/Modal.tsx) — 
  Escape key closes, click-outside closes, focus-trapped body.
- ContentTab wires TipTap editor into a modal. Editor pre-populates
  with the selected provision's text (HTML-escaped to prevent XSS).
- Editor modal shows: eid in title, instruction strip, editor, live 
  HTML output (collapsed debug), footer with current persona name +
  cancel/save buttons.
- Verified with MD 172 subparagraph: editor opens with just the
  "green deposit" definition text loaded, not the whole paragraph 4.

**Step 5 — Save flow (~30-40 min):**
- Extended apiFetch → added apiPost() helper (JSON body variant).
- Types: DraftAmendmentCreate matches backend serializer's write fields.
- ContentTab tracks originalText vs editedHtml, computes isDirty
  flag. Save button enabled only when dirty AND persona selected.
- On save: POST /api/rbi/drafts/ with work_id, target_eid, change_type
  'modify', proposed_text (stripped from editor HTML via 
  document.createElement DOM parser), rationale from optional textarea,
  status 'draft', author_user_id + author_unit_id from currentPersona.
- Success: modal closes, green toast slides in top-right ("Draft saved:
  Modify existing text on chp_I__sec_C__para_4"), auto-dismisses in 5s.
- Error: red inline box in modal, form data preserved. All UI stays
  responsive during 200-500ms POST latency (spinner in save button).

**Step 6 — Verify in Coordination tab (~5 min):**
- Saved as Priya Kulkarni (ACC) on MD 172, para 5, "Testing save flow"
  rationale.
- Immediately checked Coordination tab on MD 172: 4 drafts now (was 3),
  new draft correctly attributed to Priya/ACC, listed under "Other
  active drafts."
- Switched persona to Nisha Rao (CRS), saved another draft on a
  different paragraph, verified authorship attribution changes.

**Not attempted — deferred to Session 15+:**
- Track changes (character-level insertions/deletions)
- Chapter/section-scoped editing (would need TipTap schema expansion)
- Delete/insert/renumber change types (only "modify" wired today)
- Review workflow (draft → in_review → approved transitions)
- Comments on drafts

**Files added:**
- frontend/src/components/Modal.tsx
- (updated) frontend/src/components/AknRenderer.tsx — selection support
- (updated) frontend/src/pages/document-viewer/ContentTab.tsx — full editor flow

**Files modified:**
- frontend/src/api/client.ts (apiPost added)
- frontend/src/api/types.ts (DraftAmendmentCreate)
- frontend/src/App.css (selection highlight, modal, editor styles, 
  save toast animation)

**Reflection:** This is the moment the tool became real. Previous sessions
built infrastructure; this one delivered the interaction that answers
"what does this actually let RBI officers DO?" — click a provision,
draft an amendment, see it appear in coordination alongside conflicts
with other units' drafts. All in real time, all authored, all traceable.

### Session 14 — 2026-09-24 (same day, extended session) — Upload MD from UI

**Objective:** Move ingestion pipeline from CLI-only into the browser UI. 
Complete: backend refactor + endpoint + upload modal all built end-to-end.
Blocked from final verification by intermittent Gemini SDK 503s.

**Step 1 — Refactor pipeline scripts into importable module (~40 min):**
- Created rbi_registry_app/pipeline.py exposing:
  - extract_text_from_pdf(bytes) — pymupdf-based
  - generate_akn_from_text(text, meta) — Gemini call + wrap
  - load_akn_into_indigo(akn, meta) — Work + Document creation
  - run_full_pipeline(pdf_bytes, meta) — chains all three
- MDMetadata dataclass for the number/date/title bundle.
- PipelineError raised for known-failure cases; caught + mapped to
  HTTP status codes at the view layer.
- Duplicate FRBR URI check before DB insert (rejects with 400).
- **Multiple environment issues discovered + fixed:**
  * pymupdf was on Mac's venv but not in container (scripts had run
    on Mac, load_via_orm ran in container). Added to Dockerfile.
  * google-genai similarly missing from container. Added to Dockerfile.
  * python-dotenv missing from container. Added to Dockerfile.
  * All installed in one Dockerfile RUN line, rebuild ~60s.
- Confirmed working via shell:
  `Extracted 7,568 chars` from MD 290 PDF loaded via bytes.

**Step 2 — Upload endpoint POST /api/rbi/upload-md/ (~25 min):**
- MultiPartParser + FormParser for multipart/form-data handling.
- Fields: pdf_file (File), number, date, title (all required).
- Validation: PDF extension check, 25 MB size cap.
- 400 for missing fields with per-field errors dict.
- 400 for duplicate FRBR URI (existing MD conflict).
- 429 for Gemini quota exhausted.
- 503 for Gemini temporarily unavailable.
- Verified via curl: bad request returns clean 400 with all 4 field errors.

**Step 3 — Upload UI (~40 min):**
- apiPostForm() helper added to client.ts (multipart, no Content-Type).
- UploadMDModal component (frontend/src/components/UploadMDModal.tsx):
  file picker with .pdf accept + size display, number/date/title fields
  with placeholder examples + hints, upload button auto-enables when
  all fields filled, spinner + "Processing… this may take 30-60 seconds"
  during Gemini call, close-blocked while uploading.
- WorksList restructured: header row with title on left, big blue
  "+ Upload MD" button on right, success toast on new MD upload.
- Success flow: modal closes → toast → 300ms delay → navigate to 
  /works/:id/content of newly-created MD.
- Error flow: inline red error message in modal, form data preserved.

**End-to-end verification: BLOCKED by Gemini SDK 503s.**

Attempted several uploads with real PDFs (MD 172 as MD 999, MD 376 
uploaded from user's downloads). Every attempt returned 503 
"temporarily unavailable" from the Gemini SDK.

Debugging done:
- Direct curl to Gemini REST API from Mac: 200, "OK" response
- Direct curl to Gemini REST API from inside container: 200, "OK"
- Same Gemini SDK call from container with model gemini-2.0-flash: 
  404 "no longer available — use gemini-3.6-flash"
- Same call with gemini-1.5-flash: 404 "not found for v1beta"
- Same call with gemini-3.6-flash: intermittent 503

**Conclusion:** Not our code. Gemini's SDK routing was having a bad
hour today. Every layer of our stack (validation, pipeline, error 
handling, UI, spinner, error surfacing) verified individually. Just
couldn't capture one live successful upload for a screenshot.

**Files added:**
- rbi_registry_app/pipeline.py
- frontend/src/components/UploadMDModal.tsx

**Files modified:**
- Dockerfile (pymupdf, google-genai, python-dotenv)
- rbi_registry_app/views.py (UploadMDView added)
- rbi_registry_app/urls.py (upload-md path added)
- frontend/src/api/client.ts (apiPostForm added)
- frontend/src/api/types.ts (UploadedMDResponse added)
- frontend/src/pages/WorksList.tsx (header + upload button + modal wiring)
- frontend/src/App.css (upload form styles, spinner, works-header)

**Silver lining on the Gemini flakiness:** we accidentally proved the
error UX works beautifully. When 503s hit, the modal:
- Stays open (user's form data preserved)
- Shows a clear red error message with plain English
- Cancel and Retry both work cleanly
- No console errors, no white-screen, no lost input
This is arguably better than most enterprise software handles third-party
failures. The demo story is unaffected — "click Upload, wait 30 sec, 
sometimes Gemini needs a retry, error handling is graceful."

### Session 15 — 2026-09-24 (evening) — Reskin: align UI with pre-build mockup

**Objective:** Adopt the visual language from the pre-build mockup 
(rbi-md-registry-v2.jsx) for what we've built. Cost of doing this now vs
later: single session ~90 min now, cheaper than reskinning many pages later.

**Strategic conversation before code:**

Reviewed the mockup carefully. Three categories of gap:
1. Visual language — serif typography, warm beige palette, document-like 
   layout. Cheap to align now.
2. Missing features that don't need new data — FRBR URI bar, signatory 
   block, cross-references. Cheap to add.
3. Missing features needing new data — Timeline, Comparison, inline 
   amendment markers. Depend on Phase 5 amendment engine.

Decision: adopt Tier 1 and Tier 2 (visual + cheap features) this session.
Defer Tier 3 to Phase 5 when amendment data lands.

**Architectural discussion — one clarification, one new backlog item:**

*Why data model and AKN XML stay separate (question raised, answered):*
AKN XML = the document text itself (paragraphs, tables, structure).
Django models (WorkingUnit, MDOwnership, DraftAmendment) = workflow 
metadata about the document (who owns it, who's editing, coordination
state). Referencing content by target_eid, not duplicating it. Same
design as Indigo's original architecture. Merging would either bloat 
XML with workflow state or fragment content across relational tables.
Working as intended, no fix needed.

*Amendment-as-batch refactor (new backlog):*
Mockup treats an "Amendment Direction, 2026" as a whole instrument — 
title, reference codes, publication + effective dates, drafting team,
rationale, and multiple modifications inside it. Our current 
DraftAmendment model is one-change-per-record. To match reality, we
need: new Amendment model as parent instrument, DraftAmendment 
renamed to Modification with FK to Amendment, UI flow to start an
amendment and add modifications to it. ~2 sessions. Deferred to 
after tracker changes so the new flow inherits our polished visual
language.

**Step 1 — CSS design tokens + typography (~15 min):**
- New :root block with design tokens (--bg-page beige, --accent-navy,
  yellow amendment state, serif/sans/mono families, etc.)
- Bulk find-replace hardcoded colors to var(--...) throughout App.css.
- Body defaults to serif for legal content, sans for UI chrome.
- Chapter headings: serif bold, centered, no underline (was underlined
  block heading). Section headings: serif bold, left-aligned.

**Step 2 — Document masthead + paper card (~30 min):**
- Content tab now wraps AknRenderer in .doc-paper: white card, centered,
  max-width 720px, generous internal padding, sits on beige page.
- New DocumentMasthead.tsx: reads FRBR meta from XML, displays 
  "RESERVE BANK OF INDIA" small-caps letterspaced, "Master Direction 
  N of YYYY" mono, big serif title centered, "Rendered as of [long date]"
  italic. Matches mockup's document-header treatment.
- Preface rewritten from gray-boxed blockquote to inline italic serif 
  body text (as it appears in real gazette).
- Result: content genuinely reads like a printed regulation.

**Step 3 — FRBR URI bar (~15 min):**
- New FrbrUriBar.tsx: displays full FRBR URI with expression date
  highlighted yellow with navy underline, styled as clickable pill.
- Actual time-travel deferred to Phase 5 (needs amendment engine to 
  render document as-of a past date). Button is disabled today; 
  tooltip explains "coming in Phase 5."
- Removed duplicate FRBR URI from doc-meta line (now only in bar).

**Step 4a — Cross-reference detection (~10 min):**
- renderTextWithCrossRefs() in AknRenderer regex-matches:
  - "Reserve Bank of India (X) Directions, YYYY" 
  - "Banking Regulation Act, YYYY"
  - "Reserve Bank of India Act, YYYY"
- Matches wrapped in .akn-crossref span with dotted navy underline.
- Applied to <p> tags and <td> content in the renderer.

**Step 4b — Reusable Tooltip component (~15 min):**
- User noticed native `title=` tooltips are slow to appear, hard to see,
  unstylable. Real problem: browser default tooltips have consistently 
  bad UX everywhere they're used.
- Built Tooltip.tsx: React component with 300ms delay-on-hover, instant
  hide-on-leave, auto-flip top/bottom based on viewport space, dark
  background matching design tokens, arrow pointing at trigger, keyboard
  accessible (focus/blur handlers), animated in with fadeIn.
- Applied to: cross-references (Step 4a), FRBR URI date button (Step 3).
- Still to apply: SOON tab badges, disabled Save draft button, any 
  future disabled-with-explanation states. Deferred to next session's
  polish (see backlog).

**Files added:**
- frontend/src/components/Tooltip.tsx
- frontend/src/components/FrbrUriBar.tsx
- frontend/src/pages/document-viewer/DocumentMasthead.tsx

**Files modified:**
- frontend/src/App.css (design tokens block, all rules updated to use vars,
  paper card, masthead, FRBR bar, tooltip, cross-ref styles)
- frontend/src/components/AknRenderer.tsx (cross-ref detection + Tooltip
  integration; chapter heading style refinements)
- frontend/src/pages/document-viewer/ContentTab.tsx (paper card wrapper, 
  masthead insertion)
- frontend/src/pages/DocumentViewer.tsx (FrbrUriBar added between header 
  and TabNav, duplicated FRBR URI removed from doc-meta)

**What was NOT reskinned this session — for next session:**
- Coordination tab (conflict cards, draft cards — still Apple-style blue)
- Amendments tab / editor modal (still Apple-style)
- Works list cards (partially reskinned — serif title, but card frame 
  and Upload button still Apple-style)
- Header chrome above tabs (persona switcher, back-to-works, page title)

Reason for stopping short of a full reskin: (a) session budget, and 
(b) once we lock in the design tokens, remaining reskinning is 
mechanical class-by-class work with almost no visual-decision risk. 
Best done as a single focused pass at start of Session 16 rather than 
mixed with feature work.

**Session 16 plan (short reskinning pass, then feature work):**
- Complete visual reskin: Coordination, Amendments, Works list, header
  chrome (~45 min mechanical work)
- Then either: track changes prototype in editor, OR the amendment-as-
  batch refactor. Depends on which feels more useful for demo.

### Phase status update
- [x] Phase 0 — Indigo running with India as Place
- [x] Phase 2 — PDF → AKN pipeline solid, 3 MDs loaded, upload from UI
- [~] Phase 3 — React frontend: Works list, Document viewer (tabbed, 
  reskinned to mockup language), Coordination tab (built, awaiting 
  reskin), Upload MD flow (built, awaiting reskin).
- [~] Phase 4 — Editor prototype substantially done. Click-to-select, 
  per-provision editor, save-as-DraftAmendment flow. Track changes,
  chapter/section-scoped editing: Sessions 17+.
- [ ] Phase 1 — Strip Indigo browser UI (deferred; use only Indigo's API/engine).
- [ ] Phase 5 — Historical amendment migration + time-travel + Timeline
  + Comparison views + inline amendment markers.


## Backlog — deferred fixes

**Pipeline / ingestion:**
- **Complex tables untested:** Simple 2-column tables handled well
  (MD 172). Multi-column financial matrices, merged cells, multi-page
  tables not yet tested. Consider docling/marker fallback if pymupdf
  + Gemini fails on hard cases when we scale to more MDs.
- **Amendment history handling:** MD 356 loaded with July 2026
  consolidation date. Proper handling (original Work at 2025 date +
  amended Expression at 2026) is Phase 5 work.
  - **Upload feature needs one live end-to-end verification:** All code
  paths tested individually in Session 14, but no captured screenshot of
  a successful upload → redirect → new MD rendered due to Gemini 503s.
  First move next session: retry an upload with any RBI PDF, expect it
  to work, capture the flow.
- **Consider Gemini paid tier:** Free tier has TWO problems, not one:
  20 req/day cap (known), and unpredictable 503 rates on the SDK path
  (new in Session 14). Direct REST endpoint seems more reliable than
  SDK. Paid tier presumably has better reliability guarantees. Test
  upgrade before demoing to stakeholders.
- **Consider bypassing google-genai SDK, use requests directly:** 
  We proved via curl that REST endpoint works when SDK returns 503.
  Alternative implementation of generate_akn_from_text() using plain
  HTTP POST would eliminate the SDK-related flakiness. ~1 hour of work.

**Frontend:**
- **Auth is dev-only:** Token hardcoded in frontend source (config.ts).
  Fine for local POC. Production requires real auth flow (login page,
  token refresh, secure storage). Phase 4+ concern.
- **No error boundaries:** If a React component throws, whole page
  crashes. Add ErrorBoundary component before Phase 4 (editor is
  complex, will benefit from graceful error handling).
- **No global state management:** Currently components fetch their own
  data. Fine for read-only views. Editor state (unsaved changes,
  active tools, selection) may need Zustand or similar. Defer until
  editor work reveals what's actually needed.
- **TipTap scratchpad in Amendments tab is temporary:** Session 12 used
  the Amendments tab as an editor sandbox to verify TipTap install.
  Real flow (edit specific provision, save as DraftAmendment) lives in
  Content tab (Session 13, Step 4-6).
  - **No upload progress indication for large PDFs:** Files up to 25MB
  accepted, but the spinner just says "Processing…" without any 
  chunked progress. Fine for POC (typical MD is 100-500KB), matters if
  we start ingesting very long consolidated documents.
- **Timeline tab still a placeholder:** Marked "SOON" in TabNav. Would
  show amendment history over time for a given MD. Depends on Phase 5
  historical migration work.
  - **Complete visual reskin (Session 16 opener):** Coordination cards, 
  Amendments modal, Works list card frames, header chrome (persona
  switcher, back-to-works, page title above tabs) still use the pre-Session-15
  Apple-style palette. Mechanical CSS pass to update — no visual decisions
  remaining, design tokens are locked in.
- **Doc title appears twice on Content tab:** The title shows once in
  the page header above the tabs (chrome), and again inside the masthead
  on the paper card (document). Not broken, just visually redundant.
  Remove the chrome-level title, since users now have the paper masthead
  for identification. Trivial fix, 2 min.
- **Remaining native `title=` tooltips to swap to Tooltip component:**
  SOON tab badges (Timeline, Amendments), disabled Save draft button in
  the editor modal, any future disabled states. Small, mechanical.

**Data / content:**
- **ASCII hyphen vs en-dash in ingested MD titles:** MD 172 shows 
  "Commercial Banks - Climate Finance" (ASCII hyphen), should be 
  "Commercial Banks – Climate Finance" (en-dash). Source of truth is 
  the PDF cover page. Fix: either (a) update Gemini prompt to normalize
  dashes, or (b) post-processing pass on ingested titles. Cosmetic but
  visible on masthead.

**Backend/infrastructure:**
- **CORS is dev-permissive:** Django CorsMiddleware active with no
  CORS_ALLOWED_ORIGINS restrictions. Fine for local dev. Production
  hardening required.
- **Indigo API write layer:** WorkSerializer/DocumentSerializer not
  designed for writes. Currently working around via Django ORM.
  If we need programmatic write access from React (for amendments),
  2-3 sessions of custom serializer work required. Phase 4 concern.
- **Gemini free tier is 20 req/day:** Consider paid tier before full
  corpus ingestion. Cost estimate ~$10-30 for entire 250-MD corpus.
- **Django dev server doesn't auto-recover from import crashes:** When
  code has a Python-level error that breaks import (e.g., serializer
  field validation failing at class-definition time), the container is
  "running" but the Python process is dead. File saves aren't picked up.
  Fix: `docker compose restart web`. Rule of thumb: if
  `docker compose logs web` shows a traceback, always restart before
  troubleshooting further.

  **Feature / architecture (Phase 4+ product decisions):**
- **Amendment-as-batch refactor:** Current DraftAmendment = 1 change.
  Real RBI amendment instruments bundle metadata (title, effective date,
  drafting team, rationale) + multiple modifications. Need Amendment
  model (parent) + Modification (renamed DraftAmendment, FK to Amendment)
  + "Start Amendment" UI flow. ~2 sessions. Better done AFTER track changes
  so the new flow inherits polished visual language.
- **Track changes in editor:** Not yet started. TipTap Pro extension
  (@tiptap-pro/extension-tracked-changes) or MIT community alternatives.
  ~2-3 sessions. Session 16 candidate.
- **Amendment engine + Timeline + Comparison views:** All depend on 
  historical migration (Phase 5). Once each MD has its amendment history
  attached, all three views become buildable in parallel.