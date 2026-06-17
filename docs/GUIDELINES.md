# Project Guidelines

> Filled in during Phase 2 (Tech Stack & Guidelines) of the spec-driven harness workflow.

## Tech Stack
- TBD during Phase 2 brainstorming.

## Environment Setup
- This project uses its own virtual environment at `.venv/` (created via
  `python3 -m venv .venv`), kept out of git via `.gitignore`.
- Install/update dependencies with `.venv/bin/pip install -r requirements.txt`.
- Run tests with `.venv/bin/pytest`. These commands are pre-approved in
  `.claude/settings.json` so they run without a permission prompt.
- Add new dependencies to `requirements.txt` and log the addition in
  `docs/tracking/DECISIONS.md` per the Hard Rules below.

## Architecture Conventions
- TBD.

## Testing Approach
- TDD per `superpowers:test-driven-development`. Every source file has a corresponding test file.
- A story's status only becomes `done` in `STORIES.csv` after its tasks' tests pass.

## Hard Rules
- No new dependencies without a `docs/tracking/DECISIONS.md` entry explaining why.
