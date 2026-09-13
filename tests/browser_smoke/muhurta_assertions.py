"""Browser smoke muhurta assertions; no automatic test collection."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from tests.browser_smoke.accessibility import _assert_no_horizontal_overflow


def _muhurta_share_text(page, result):
    page.evaluate(
        """() => {
            window.__muhurtaShareOpen = null;
            window.open = (url, target) => {
                window.__muhurtaShareOpen = { url, target };
                return null;
            };
        }"""
    )
    result.locator('button[aria-label="Share on WhatsApp"]').click()
    opened = page.evaluate('window.__muhurtaShareOpen')
    return parse_qs(urlparse(opened['url']).query)['text'][0]

def _assert_positive_muhurta_result(_page, result, status, calls, _scenario):
    assert 'Exact chart screening applied' in status.inner_text()
    assert result.locator('.mu-slot').count() > 0, result.inner_text()
    assert result.locator('.mu-rg-computed').count() > 0
    assert result.locator('.mu-chart-rule--pass').count() > 0
    assert calls

def _assert_gold_disposition(result, status, computed_text, scenario):
    if scenario == 'gold-cap':
        assert result.locator('.mu-chart-disposition--capped').count() > 0
        assert result.locator('.mu-chart-status--screened-capped').is_visible()
        assert (
            'Condition not met · slot retained · raw score unchanged '
            '· maximum rating Good'
        ) in computed_text
        assert 'Gold event-specific chart clauses resolved' in status.inner_text()
        assert 'general election-chart baseline is not assessed' in (
            status.inner_text()
        )
        assert result.locator('.mu-chart-disposition--review').count() == 0
    elif scenario == 'gold-unknown':
        assert result.locator('.mu-chart-disposition--review').count() > 0
        assert result.locator('.mu-chart-status--screened-review').is_visible()
        assert 'Indeterminate at calculation boundary · review needed' in (
            computed_text
        )
        assert 'all four Gold v1 event-specific clauses attempted' in (
            status.inner_text()
        )
        assert result.locator('.mu-chart-disposition--capped').count() == 0
    else:
        assert 'Gold event-specific chart clauses resolved' in status.inner_text()
        assert 'general election-chart baseline is not assessed' in (
            status.inner_text()
        )
        assert result.locator('.mu-chart-disposition--capped').count() == 0
        assert result.locator('.mu-chart-disposition--review').count() == 0
        assert result.locator('.mu-chart-rule--fail').count() == 0
        assert result.locator('.mu-chart-rule--unknown').count() == 0

def _assert_gold_share_text(share_text, result):
    assert 'general election-chart baseline is not assessed' in share_text
    if result.locator('.mu-chart-status--screened-review').count():
        assert (
            'All disclosed event chart clauses were attempted; '
            'unresolved facts still require review.'
        ) in share_text
    elif result.locator('.mu-chart-status--screened-capped').count():
        assert (
            'All disclosed event chart clauses were evaluated; '
            'one or more qualifications were not met'
        ) in share_text
    else:
        assert (
            'All disclosed event chart clauses were evaluated and resolved'
        ) in share_text
    assert 'Method: https://panchangam.astrochaganti.com/docs/' in share_text
    assert (
        'Qualitative chart or ritual checks still require practitioner review'
    ) not in share_text

def _assert_gold_muhurta_result(page, result, status, calls, scenario):
    assert 'chart review remains manual' not in status.inner_text()
    assert result.locator('.mu-slot').count() > 0, result.inner_text()
    computed = result.locator('.mu-rg-computed').first
    assert computed.count() == 1
    computed_text = computed.text_content()
    assert 'Product ranking policy' in computed_text
    assert 'election_chart.gold_qualification_policy_v1' in computed_text
    assert 'Event source' in computed_text
    assert 'Interpretation convention' in computed_text
    assert result.locator('.mu-rg-validation').count() == 0
    assert calls
    assert 'general election-chart baseline is not assessed' in (
        status.inner_text()
    )
    _assert_gold_disposition(result, status, computed_text, scenario)
    _assert_gold_share_text(_muhurta_share_text(page, result), result)

def _assert_annaprasana_muhurta_result(page, result, status, calls, scenario):
    assert calls
    if scenario == 'annaprasana-hard-fail':
        assert 'failed an exact chart requirement' in result.inner_text()
        assert 'No clear slots found' in result.inner_text()
        assert result.locator('.mu-slot').count() == 0
        failed_rules = result.locator('.mu-chart-removals')
        assert failed_rules.is_visible()
        failed_rules.locator(':scope > summary').click()
        assert 'No natural malefic occupies Lagna' in failed_rules.inner_text()
        assert 'Natural malefics in Lagna: Surya.' in failed_rules.inner_text()
        return

    assert result.locator('.mu-slot').count() > 0
    computed = result.locator('.mu-rg-computed').first
    assert computed.count() == 1
    assert computed.locator('.mu-chart-rule').count() == 6
    computed_text = computed.text_content()
    assert 'muhurta.annaprasana.raman_transcription_chart' in computed_text
    assert 'election_chart.annaprasana.raman_transcription_policy_v1' in (
        computed_text
    )
    assert 'printed p. 22' in computed_text
    assert 'physical PDF p. 25' in computed_text
    assert 'Annaprasana natural-malefic Lagna convention v1' in computed_text
    assert result.locator('.mu-rg-validation').count() == 0
    assert 'general election-chart baseline #284 remains open' in (
        status.inner_text()
    )
    if scenario == 'annaprasana-pass':
        assert 'Annaprasana event-specific chart assessment complete' in (
            status.inner_text()
        )
        assert result.locator('.mu-chart-rule--pass').count() >= 6
        assert result.locator('.mu-chart-disposition--review').count() == 0
    elif scenario == 'annaprasana-preference-miss':
        assert 'Annaprasana event-specific chart assessment complete' in (
            status.inner_text()
        )
        assert result.locator(
            '.mu-chart-rule--prefer.mu-chart-rule--fail'
        ).count() > 0
        assert 'Preference not present · no penalty' in computed_text
        assert result.locator('.mu-chart-disposition--review').count() == 0
    else:
        assert 'unresolved facts' in status.inner_text()
        assert result.locator('.mu-chart-rule--unknown').count() > 0
        assert result.locator('.mu-chart-disposition--review').count() > 0

    share_text = _muhurta_share_text(page, result)
    assert 'general election-chart baseline #284 remains open' in share_text
    if scenario == 'annaprasana-unknown':
        assert (
            'All six Annaprasana event-specific chart clauses were attempted; '
            'unresolved facts still require review.'
        ) in share_text
    else:
        assert (
            'All six Annaprasana event-specific chart clauses were evaluated '
            'and resolved.'
        ) in share_text
        assert 'practitioner review' not in share_text

def _assert_court_muhurta_result(page, result, status, calls, scenario):
    assert calls
    if scenario == 'court-hard-fail':
        assert 'failed an exact chart requirement' in result.inner_text()
        assert result.locator('.mu-slot').count() == 0
        assert 'No clear slots found' in result.inner_text()
        return

    assert result.locator('.mu-slot').count() > 0, result.inner_text()
    computed = result.locator('.mu-rg-computed').first
    assert computed.count() == 1
    assert computed.locator('.mu-chart-rule').count() == 5
    computed_text = computed.text_content()
    assert 'physical PDF p. 71' in computed_text
    assert 'Product ranking policy' in computed_text
    assert result.locator('.mu-rg-validation').count() == 0
    if scenario == 'court-pass':
        assert 'Court filing chart assessment complete' in status.inner_text()
        assert 'Information pattern present · no ranking effect' in computed_text
        assert result.locator('.mu-chart-disposition--review').count() == 0
    elif scenario == 'court-preference-miss':
        assert 'Preference not present · no penalty' in computed_text
        assert 'Information pattern not continuous · no adverse inference' in (
            computed_text
        )
        assert result.locator('.mu-chart-disposition--review').count() == 0
    else:
        assert 'unresolved' in status.inner_text()
        assert 'Required check could not be verified' in computed_text
        assert result.locator('.mu-chart-disposition--review').count() > 0

    share_text = _muhurta_share_text(page, result)
    assert 'Court filing v1 assesses five Raman clauses' in share_text
    assert 'It does not predict a legal outcome.' in share_text
    assert 'Private' not in share_text

def _assert_failure_muhurta_result(_page, result, _status, calls, _scenario):
    assert 'failed an exact chart requirement' in result.inner_text()
    assert 'No clear slots found' in result.inner_text()
    assert result.locator('.mu-slot').count() == 0
    assert calls

def _assert_mixed_muhurta_result(_page, result, _status, calls, _scenario):
    assert result.locator('.mu-slot').count() > 0
    assert result.locator('.mu-chart-rule--unknown').count() > 0
    assert 'changed within this window' in result.locator(
        '.mu-chart-boundary'
    ).first.text_content()
    assert result.locator('.mu-tier-excellent').count() == 0
    assert calls

def _assert_unsupported_muhurta_result(
    _page, result, status, calls, _scenario,
):
    assert 'Selected system kept separate' in status.inner_text()
    assert 'was not blended into this result' in status.inner_text()
    assert result.locator('.mu-slot').count() > 0
    assert calls == []
    assert 'assessment complete' not in status.inner_text()

def _assert_manual_only_muhurta_result(
    _page, result, status, calls, _scenario,
):
    assert 'Panchangam shortlist complete' in status.inner_text()
    assert 'chart review remains manual' not in status.inner_text()
    assert 'no exact chart request was needed' in status.inner_text()
    assert result.locator('.mu-slot').count() > 0
    assert calls == []

def _assert_not_run_muhurta_result(_page, result, status, calls, _scenario):
    assert 'Chart screening not run' in status.inner_text()
    assert 'No clear slots found' in result.inner_text()
    assert result.locator('.mu-slot').count() == 0
    assert calls == []

def _assert_unavailable_muhurta_result(
    _page, result, status, calls, scenario,
):
    assert 'Panchangam shortlist shown' in status.inner_text()
    assert 'no slot is presented as chart-screened' in status.inner_text()
    assert result.locator('.mu-slot').count() > 0
    assert result.locator('.mu-tier-excellent').count() == 0
    assert 'assessment complete' not in status.inner_text()
    if scenario == 'malformed':
        assert calls

_MUHURTA_SCENARIO_ASSERTIONS = {
    'positive': _assert_positive_muhurta_result,
    'gold-pass': _assert_gold_muhurta_result,
    'gold-cap': _assert_gold_muhurta_result,
    'gold-unknown': _assert_gold_muhurta_result,
    'annaprasana-pass': _assert_annaprasana_muhurta_result,
    'annaprasana-preference-miss': _assert_annaprasana_muhurta_result,
    'annaprasana-hard-fail': _assert_annaprasana_muhurta_result,
    'annaprasana-unknown': _assert_annaprasana_muhurta_result,
    'annaprasana-unsupported': _assert_unsupported_muhurta_result,
    'annaprasana-offline': _assert_unavailable_muhurta_result,
    'court-pass': _assert_court_muhurta_result,
    'court-preference-miss': _assert_court_muhurta_result,
    'court-hard-fail': _assert_court_muhurta_result,
    'court-unknown': _assert_court_muhurta_result,
    'karnavedha-unsupported': _assert_unsupported_muhurta_result,
    'karnavedha-offline': _assert_unavailable_muhurta_result,
    'failure': _assert_failure_muhurta_result,
    'mixed': _assert_mixed_muhurta_result,
    'unsupported': _assert_unsupported_muhurta_result,
    'offline': _assert_unavailable_muhurta_result,
    'malformed': _assert_unavailable_muhurta_result,
    'manual-only': _assert_manual_only_muhurta_result,
    'not-run': _assert_not_run_muhurta_result,
}

def _assert_muhurta_result_for_scenario(page, result, status, calls, scenario):
    _MUHURTA_SCENARIO_ASSERTIONS[scenario](
        page, result, status, calls, scenario,
    )

def _assert_muhurta_result_common(
    page, result, status, scenario, expected_state, width,
):
    if expected_state != 'screened':
        status_text = status.inner_text()
        assert 'event-specific clauses were computed' not in status_text
        assert 'event-specific clauses computed' not in status_text

    details = result.locator('.mu-reason-details')
    if details.count():
        details.first.locator(':scope > summary').click()
    if scenario in {'karnavedha-unsupported', 'karnavedha-offline'}:
        validation = result.locator('.mu-rg-validation').first
        assert validation.is_visible()
        assert 'leave the 8th house unoccupied' in validation.inner_text()
    _assert_no_horizontal_overflow(
        page, f'{scenario} chart-aware Muhurtam at {width}px',
    )
