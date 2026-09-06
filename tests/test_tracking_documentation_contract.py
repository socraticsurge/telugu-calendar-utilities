"""Keep active maintenance tracking distinct from historical artifacts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_URL = 'https://github.com/users/socraticsurge/projects/2'
ISSUES_URL = 'https://github.com/socraticsurge/telugu-calendar-utilities/issues'


def test_contributor_entry_points_link_current_work():
    for relative_path in ('README.md', 'CONTRIBUTING.md'):
        text = (ROOT / relative_path).read_text()
        assert PROJECT_URL in text
        assert ISSUES_URL in text


def test_retired_tracker_cannot_be_mistaken_for_active_backlog():
    tracker_readme = (ROOT / 'docs/tracking/README.md').read_text().lower()
    improvement_plan = (ROOT / 'docs/tracking/improvement-plan.md').read_text()
    guidelines = (ROOT / 'docs/GUIDELINES.md').read_text()

    assert 'historical' in tracker_readme
    assert 'do not add current work' in tracker_readme
    assert PROJECT_URL in tracker_readme
    assert 'Persist plans, decisions, and progress in this file as we work.' not in improvement_plan
    assert PROJECT_URL in guidelines
    assert "status only becomes `done` in `STORIES.csv`" not in guidelines
