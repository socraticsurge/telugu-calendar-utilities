"""Public documentation must preserve the browser-local profile boundary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_security_policy_describes_local_profile_data_and_analytics_boundary():
    policy = _read('SECURITY.md')

    assert "origin-scoped `localStorage`" in policy
    assert 'at most four guest profiles' in policy
    assert 'there is no account, cloud sync, or recovery' in policy
    assert 'must never be sent to' in policy
    assert 'GoatCounter' in policy


def test_user_features_document_profile_fields_readiness_and_lifecycle():
    features = _read('docs/reference/04-user-facing-features.md')

    for field in ('Name', 'Nakshatra', 'Padam', 'Lagna'):
        assert f'**{field}**' in features
    for capability in ('create', 'edit', 'delete', 'clear-all'):
        assert capability in features
    assert '**Muhurtam-ready**' in features
    assert '**Daily\nHoroscope-ready**' in features
    assert 'private-browsing storage may disappear' in features
    assert 'other browsers, devices, domains, protocols, and ports' in features
    assert 'Analytics must\nnever receive profile names' in features
