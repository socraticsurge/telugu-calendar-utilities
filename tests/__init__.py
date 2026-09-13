"""Repository test package; shared helpers never load optional browsers."""

import pytest

# Register before the support package is imported, preserving rich diagnostics.
pytest.register_assert_rewrite('tests.browser_smoke')
