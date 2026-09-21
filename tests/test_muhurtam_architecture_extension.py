"""Architecture evidence for the additive Muhurtam chart-screen feature."""

from tools.analyze_computation_architecture import build_report


def test_chart_screen_helpers_are_visible_without_reclassifying_the_core():
    report = build_report('HEAD', commit_limit=20)
    additive = {
        module['path']
        for module in report['modules']
        if module['scope_class'] == 'additive-feature'
    }

    assert report['scope']['source_files'] == report['scope']['total_source_files']
    assert report['scope']['total_source_files'] == (
        report['scope']['established_source_files']
        + report['scope']['additive_feature_source_files']
    )
    assert report['scope']['additive_feature_source_files'] == len(additive)
    assert additive
    # Owner-approved boundary adapters; engine ownership remains unchanged.
    boundary_adapters = {
        'telugu_panchangam/generators/calendar_data.py',
        'telugu_panchangam/generators/slot_facts.py',
        'telugu_panchangam/mcp/calendar_response.py',
        'telugu_panchangam/mcp/muhurta_request.py',
        'telugu_panchangam/mcp/muhurta_response.py',
    }
    assert boundary_adapters <= additive
    assert all(
        path.startswith(('src/', 'telugu_panchangam/personal/'))
        or path in boundary_adapters
        for path in additive
    )
