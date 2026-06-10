# Spec-Driven Development Harness

A reusable Claude Code template for **greenfield** projects. It forces a
roles → user stories → guidelines → spec → plan sequence before any source
code is written, then keeps human-readable trackers in sync while
implementation proceeds largely hands-free.

Full design rationale: see
[`docs/specs/`](docs/specs/) once a project's spec has been written from this
template (the design doc for the harness itself lives in the project that
built it, not here — this repo is the *output* template).

## What's in here

```
docs/
  GUIDELINES.md            # stack & conventions (filled in during Phase 2)
  NOW.md                    # single "front door" status file
  specs/INDEX.md            # which spec is "active"
  specs/                    # living specs (Phase 3)
  plans/                    # narrative plans + HANDOFF.md / AWAITING_REVIEW.md
  tracking/
    STORIES.csv             # id, role, user_story, status, spec_ref, notes
    TASKS.csv               # task_id, story_id, phase, description, status, estimate, depends_on, notes
    SESSION_LOG.md          # append-only checkpoint log
    DECISIONS.md            # append-only deviations/decisions log
    .checkpoint-snapshot/   # internal, used by the checkpoint hook
.claude/
  settings.json             # hook registrations + pre-approved permissions
  HARNESS_VERSION           # version string this project was scaffolded from
  hooks/                    # Python hooks (see below)
new-project.sh              # one-command scaffolding script
```

## The workflow

1. **Phase 1 — Roles & User Stories.** Conversational; every role/actor is
   captured as `As a [role], I want [goal], so that [benefit]` rows in
   `docs/tracking/STORIES.csv`.
2. **Phase 2 — Tech Stack & Guidelines.** Captured in `docs/GUIDELINES.md`
   (stack, architecture conventions, testing approach, hard rules, venv setup).
3. **Phase 3 — Spec.** `docs/specs/<topic>-design.md`, referencing story IDs.
4. **Phase 4 — Plan.** `docs/plans/<topic>-plan.md` plus a granular
   `docs/tracking/TASKS.csv` (~5 minutes per task, with `depends_on`).
5. **Phase 5 — Autonomous Implementation.** Subagent-driven, hooks active:
   - A **gate hook** blocks source edits until a spec + stories exist (and
     pauses the next phase while a phase is awaiting review).
   - A **sync hook** rolls up `TASKS.csv` → `STORIES.csv` status as work
     completes, and writes `docs/plans/AWAITING_REVIEW.md` when a phase finishes.
   - A **checkpoint hook** (on context compaction or session end) refreshes
     `docs/NOW.md` and `docs/plans/HANDOFF.md`, appends `SESSION_LOG.md`, and
     commits trackers — so context survives compaction and session restarts.
   - A **session-start hook** re-injects `HANDOFF.md` / `NOW.md` / the latest
     `SESSION_LOG.md` entry at the start of every session.

`docs/NOW.md` is the single file to check: it always answers "where are we
and what do you need from me?"

## Hooks (`.claude/hooks/`)

| Hook | Event | Purpose |
|---|---|---|
| `gate_spec_required.py` | PreToolUse (Edit/Write) | Blocks source edits without spec + stories; respects `AWAITING_REVIEW.md` and `.claude/harness-override` |
| `sync_tracker_on_task.py` | PostToolUse (TaskUpdate completed) | Updates `TASKS.csv`/`STORIES.csv` under a file lock, writes `AWAITING_REVIEW.md` on phase completion |
| `session_start_context.py` | SessionStart | Injects `HANDOFF.md` + `NOW.md` + latest session log entry |
| `checkpoint.py` | PreCompact, Stop | Diffs trackers, appends `SESSION_LOG.md`, refreshes `HANDOFF.md`/`NOW.md`, commits |

All hooks are pure-stdlib Python (`csv`, `json`, `pathlib`, `subprocess`,
`re`, `os`, `time`) so CSV trackers stay Excel-compatible. Tests live in
`tests/` (run with `python3 -m pytest tests/`).

## Starting a new project from this template

```bash
./new-project.sh "/path/to/new-project"
```

This copies the template (including `.claude/`), re-initializes git, creates
a `.venv`, and makes the first commit. Then `cd` into the new project, open
Claude Code, and describe what you're building — Phase 1 (roles & user
stories) starts automatically.

## Versioning

Each scaffolded project gets its own copy of `.claude/` + `docs/`, recorded
via `.claude/HARNESS_VERSION`. There is no live sync back to existing
projects — backporting harness improvements is a manual, deliberate copy.

## Out of scope

- Existing/legacy codebase support (a separate harness, future work).
- Multi-machine/distributed agent coordination (single-machine file locking only).
- Automatic harness updates across projects.
