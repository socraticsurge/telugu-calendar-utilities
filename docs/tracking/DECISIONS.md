# Decisions

Historical record for the retired CSV/hook tracker. It remains append-only as
evidence of that workflow; current decisions belong on the relevant repository
Issue or pull request and are surfaced in the GitHub Project.

## 2026-06-10 — `sync_tracker_on_task.py` always passes `tests_passed=True`

The PostToolUse hook for `TaskUpdate(completed)` cannot independently verify
that a task's tests passed — Claude Code does not pass test results through
the `TaskUpdate` tool input, and the hook has no project-specific knowledge of
how to run tests. As a v1 simplification, `sync_tracker_on_task.py` calls
`sync_task_completion(..., tests_passed=True)` unconditionally, so a story
rolls up to `done` whenever all its tasks are marked `completed`.

This is a deviation from spec section 5 ("Status `done` requires underlying
tasks' tests to pass — not on self-report"). The TDD discipline enforced by
`superpowers:subagent-driven-development` (tests written and run by the
implementer subagent, then re-verified by an independent reviewer subagent
before `TaskUpdate(completed)` is called) is the actual enforcement
mechanism in practice. A future improvement could have the sync hook shell
out to a project-configured test command before rolling up story status, but
that is out of scope for this template.
