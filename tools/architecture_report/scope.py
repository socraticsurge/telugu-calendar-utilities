"""Production scope and ordered layer classification."""
from __future__ import annotations

from pathlib import PurePosixPath

_ADDITIVE_FEATURE_SOURCES = frozenset({
    'src/lib/calendar-data.ts',
    'src/lib/calendar-loader.ts',
    'src/scorer/ranking.ts',
    'src/scorer/search-contract.ts',
    'src/scorer/tara-chandra.ts',
    'telugu_panchangam/generators/calendar_data.py',
    'telugu_panchangam/mcp/muhurta_request.py',
    'telugu_panchangam/mcp/muhurta_response.py',
    'telugu_panchangam/mcp/calendar_response.py',
    'telugu_panchangam/personal/muhurta_search.py',
    'telugu_panchangam/personal/muhurta_eligibility.py',
    'telugu_panchangam/personal/muhurta_slot_scoring.py',
    'telugu_panchangam/personal/muhurta_explanations.py',
    'telugu_panchangam/personal/search_contract.py',
    'src/lib/birth-profile-api.ts',
    'src/lib/election-chart-api.ts',
    'src/lib/chart-contracts.ts',
    'src/lib/local-chart-time.ts',
    'src/lib/remote-api/contracts.ts',
    'src/lib/remote-api/base.ts',
    'src/lib/remote-api/http.ts',
    'src/lib/remote-api/values.ts',
    'src/lib/remote-api/birth-response.ts',
    'src/lib/remote-api/places-response.ts',
    'src/lib/remote-api/election-response.ts',
    'src/lib/guest-profile-store.ts',
    'src/lib/guest-profile/types.ts',
    'src/lib/guest-profile/values.ts',
    'src/lib/guest-profile/birth-normalization.ts',
    'src/lib/guest-profile/birth-ownership.ts',
    'src/lib/guest-profile/profiles.ts',
    'src/lib/guest-profile/legacy.ts',
    'src/lib/guest-profile/migration.ts',
    'src/lib/guest-profile/orphan-recovery.ts',
    'src/lib/profile-selection.ts',
    'src/lib/remote-calculation-activation.ts',
    'src/panels/profiles.ts',
    'src/panels/profiles/birth-form.ts',
    'src/panels/profiles/birth-form-view.ts',
    'src/panels/profiles/birth-validation.ts',
    'src/panels/profiles/contracts.ts',
    'src/panels/profiles/detail-sections.ts',
    'src/panels/profiles/detail-view.ts',
    'src/panels/profiles/elements.ts',
    'src/panels/profiles/form-view.ts',
    'src/panels/profiles/list-view.ts',
    'src/panels/profiles/manual-form.ts',
    'src/panels/profiles/manual-form-view.ts',
    'src/panels/profiles/natal-view.ts',
    'src/panels/profiles/navigation.ts',
    'src/panels/profiles/notices.ts',
    'src/panels/profiles/profile-save.ts',
    'src/scorer/election-assessors/primitives.ts',
    'src/scorer/election-assessors/benefic-patterns.ts',
    'src/scorer/election-assessors/benefic-rasi.ts',
    'src/scorer/election-assessors/chart-geometry.ts',
    'src/scorer/election-assessors/conjunction.ts',
    'src/scorer/election-assessors/contracts.ts',
    'src/scorer/election-assessors/event-admission.ts',
    'src/scorer/election-assessors/graha-nature.ts',
    'src/scorer/election-assessors/karnavedha-daylight.ts',
    'src/scorer/election-assessors/lordship.ts',
    'src/scorer/borrowing-context.ts',
    'src/scorer/election-chart-enrichment.ts',
    'src/scorer/election-chart-screening.ts',
    'src/scorer/personal-election-screening.ts',
    'telugu_panchangam/personal/activity_check_contract.py',
    'telugu_panchangam/personal/borrowing.py',
    'telugu_panchangam/personal/election_assessors/__init__.py',
    'telugu_panchangam/personal/election_assessors/conventions.py',
    'telugu_panchangam/personal/election_assessors/chart_geometry.py',
    'telugu_panchangam/personal/election_assessors/conjunction.py',
    'telugu_panchangam/personal/election_assessors/contracts.py',
    'telugu_panchangam/personal/election_assessors/event_admission.py',
    'telugu_panchangam/personal/election_assessors/facts.py',
    'telugu_panchangam/personal/election_assessors/graha_nature.py',
    'telugu_panchangam/personal/election_assessors/karnavedha.py',
    'telugu_panchangam/personal/election_assessors/lordship.py',
    'telugu_panchangam/personal/election_assessors/primitives.py',
    'telugu_panchangam/personal/election_assessors/benefic_patterns.py',
    'telugu_panchangam/personal/election_assessors/benefic_rasi.py',
    'telugu_panchangam/personal/election_chart.py',
    'telugu_panchangam/personal/election_chart_rules.py',
    'telugu_panchangam/personal/personal_election.py',
})


def source_scope_class(path: str) -> str:
    """Classify a production module without hiding it from report evidence."""
    return 'additive-feature' if path in _ADDITIVE_FEATURE_SOURCES else 'established'


def _is_source(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if '__tests__' in parts or path.endswith('.d.ts'):
        return False
    return (
        path.startswith('telugu_panchangam/') and path.endswith('.py')
        or path.startswith('scripts/') and path.endswith('.py')
        or path.startswith('src/') and path.endswith('.ts')
    )


def _is_test(path: str) -> bool:
    return (
        path.startswith('tests/') and path.endswith('.py')
        or '__tests__' in PurePosixPath(path).parts and path.endswith('.ts')
    )


_LAYERS_BY_EXACT_PATH = {
    'telugu_panchangam/personal/muhurta.py': 'scoring',
    'telugu_panchangam/personal/muhurta_eligibility.py': 'scoring',
    'telugu_panchangam/personal/muhurta_slot_scoring.py': 'scoring',
    'telugu_panchangam/personal/muhurta_explanations.py': 'scoring',
    'telugu_panchangam/personal/slot_scorers.py': 'scoring',
    'telugu_panchangam/generate.py': 'build',
}


_LAYERS_BY_PREFIX = (
    ('telugu_panchangam/models/', 'models'),
    ('telugu_panchangam/engines/', 'engines'),
    ('telugu_panchangam/personal/activity_', 'activity-rules'),
    ('telugu_panchangam/personal/', 'personal'),
    ('telugu_panchangam/gochara/', 'gochara'),
    ('telugu_panchangam/mcp/', 'mcp'),
    ('telugu_panchangam/generators/', 'generators'),
    ('scripts/', 'build'),
    ('telugu_panchangam/', 'derived-calendar'),
    ('src/data/', 'browser-data'),
    ('src/panels/', 'browser-panels'),
    ('src/', 'browser-core'),
)


def _layer(path: str) -> str:
    exact_layer = _LAYERS_BY_EXACT_PATH.get(path)
    if exact_layer is not None:
        return exact_layer
    for prefix, layer in _LAYERS_BY_PREFIX:
        if path.startswith(prefix):
            return layer
    return 'other'
