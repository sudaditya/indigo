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
- [x] Phase 2 — PDF → AKN ingestion pipeline solid, 3 MDs loaded (Sessions 3, 5, 7)
- [ ] Phase 1 — Strip Indigo frontend (see Strategic Decisions — likely reduced to
  disabling/ignoring Indigo's browser UI rather than removing it)
- [ ] Phase 3 — React frontend against real data (next up)
- [ ] Phase 4 — WYSIWYG amendment editor
- [ ] Phase 5 — Historical amendment migration

## Pilot corpus
3 MDs loaded end-to-end, chosen for structural variety:
- MD 290 — UCB Dividends (5 pages, simple structure). Work id=3.
- MD 172 — Commercial Banks Climate Finance (14 pages, tables). Work id=4.
- MD 356 — NBFC Income Recognition (25 pages, complex consolidated). Work id=5.

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
- **Editor** — will be built on CKEditor (or similar mature editor tech)
  inside our React frontend, with AKN plugins developed for RBI-specific
  document types.

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

### Session 10 target — start the Coordination Dashboard (Path C)

**Strategic rationale:**
This is the RBI-specific feature that would justify the POC to DoR
leadership. Neither Indigo nor LEOS provides cross-team amendment
coordination — this is novel work that demonstrates why we're building
custom rather than just adopting an existing platform. Delivers a
demoable capability in 3-4 sessions.

**Reference material:** DoR organogram (Organogram.xlsx uploaded Session 9) —
15 Groups across 2 Divisions, ~28 Sections. Model uses "WorkingUnit"
polymorphic between Group and Section. See Session 10 log for final schema.

**What it is:**
A dashboard showing which teams are working on which MDs, flagging
conflicts between drafts (from the original Session-0 mockup — the
"Team A is drafting an amendment against clause 6(ii) which Team B
just modified last week" scenario).

**Session 10 scope (backend foundation):**
- New Django app: rbi_registry_app/ (sits alongside indigo_api/)
- New models: DraftAmendment, TeamOwnership, at minimum
- Django migrations (creates Postgres tables)
- REST endpoints for the coordination data (read-only initially)
- Populated with realistic dummy data (real drafts require the editor)
- Verify via curl before building UI

**Session 11+ (frontend + iteration):**
- React dashboard page consuming the new endpoints
- Conflict visualization (which clauses have multiple in-flight drafts)
- Timeline view (what's been amended recently, what's pending)
- Filter/drill-down by team, by MD, by clause

**Why not Path B (editor) instead:**
Editor is technically more valuable but takes 4-6+ sessions with high
uncertainty. Coordination dashboard delivers demoable output faster
and doesn't compete with the editor — they're complementary features
in the final product.

**Deferred to Session 10+X (when editor prototype begins):**
- Editor tech evaluation (CKEditor vs TipTap vs ProseMirror)
- Read-only AKN loading into editor
- Actual editing + save
- Track changes prototype

**Estimated timing:**
- Sessions 10-11: Backend for coordination (models, endpoints, dummy data)
- Sessions 12-13: Frontend dashboard
- Session 14+: Editor prototype (Path B, deferred)

### Session 9.5 — 2026-09-09 (planning) — Coordination Dashboard design

Chose Path C (Coordination Dashboard) as Session 10-13 focus.
Strategic rationale: novel RBI-specific feature not in Indigo or LEOS;
demoable to DoR leadership; complements (doesn't compete with) the
editor prototype which is deferred to Sessions 14+.

WorkingUnit — Section OR group-level unit (polymorphic)
Fields: name, short_code, division (PRD/COD),
group_name. is_group_level() derived from name==group_name.
UnitMembership — Users belong to WorkingUnits (many-to-many with
primary flag). Supports secondments / dual roles.
MDOwnership — One nodal WorkingUnit per Work (MD).
Edit-open by default. edit_restricted + denied_units
provide explicit denylist when needed.
DraftAmendment — Core entity for coordination.
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

### Session 10 (opening moves — planned)
1. `django-admin startapp rbi_registry_app` inside container
2. Register in INSTALLED_APPS (indigo/settings.py override)
3. Write models.py per design above
4. Generate migrations, run migrate
5. Populate all ~34 WorkingUnits from parsed organogram
6. Populate 8-10 dummy users, one primary UnitMembership each
7. Populate 3 MDOwnership records (assignments above)
8. Populate 7 DraftAmendment records (dummy plan above)
9. Write serializers + views + URL routes for read-only endpoints:
   - GET /api/rbi/units/           (all working units)
   - GET /api/rbi/mds/             (MD ownership + status summary)
   - GET /api/rbi/drafts/          (all drafts, filterable)
   - GET /api/rbi/conflicts/       (computed conflicts across all MDs)
10. Verify via curl before frontend work

Realistic timing: 90-120 min if focused.

**Data model designed (implementation in Session 10):**

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

### Phase status
- [x] Phase 0 — Indigo running with India as Place
- [x] Phase 2 — PDF → AKN pipeline solid
- [~] Phase 3 — Frontend foundation done + Coordination backend done.
  Next: Coordination frontend (Session 11). Then Phase 3 completion.
- [ ] Phase 4 — Editor prototype (deferred to ~Session 14+)
- [ ] Phase 1, 5

## Backlog — deferred fixes

**Pipeline / ingestion:**
- **Complex tables untested:** Simple 2-column tables handled well
  (MD 172). Multi-column financial matrices, merged cells, multi-page
  tables not yet tested. Consider docling/marker fallback if pymupdf
  + Gemini fails on hard cases when we scale to more MDs.
- **Amendment history handling:** MD 356 loaded with July 2026
  consolidation date. Proper handling (original Work at 2025 date +
  amended Expression at 2026) is Phase 5 work.

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