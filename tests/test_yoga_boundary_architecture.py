"""New Yoga identity adapter is additive and remains visible in architecture."""
from tools.architecture_report.scope import source_scope_class


def test_yoga_identity_adapter_does_not_reclassify_established_core():
    assert source_scope_class('src/scorer/nitya-yoga-names.ts') == 'additive-feature'
