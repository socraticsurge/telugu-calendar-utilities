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
    assert all(
        path.startswith(('src/', 'telugu_panchangam/personal/'))
        for path in additive
    )
