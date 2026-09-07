# RBI Master Directions Registry — POC

## Owner
MisterSood (Manager, Department of Regulation, RBI)

## Purpose
POC for a version-controlled Master Directions platform, forked from Laws.Africa Indigo.
Ingest, version-control, and enable structured amendment of RBI's ~250 Master Directions.

## Stack
- Backend: Django (from Indigo fork) + Postgres — runs in Docker
- Frontend: React + Vite (to be built, replacing Indigo's Django templates)
- LLM: Anthropic API (Claude) for PDF ingestion
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