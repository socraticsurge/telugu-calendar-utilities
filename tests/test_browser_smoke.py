"""End-to-end browser smoke against the built Vite site (dist/).

This is the regression net the v1.8.0 hotfix would have benefited
from: even when every endpoint returns 200, the deployed page can
still fail at runtime if the bundle omits functions the page
expects. A real browser load surfaces those errors immediately as
`ReferenceError` in the JS console.

The fixture runs `npm run build` (tsc --noEmit + vite build) so the
tests exercise a deployment artifact, with the structured-data flag
disabled to preserve the legacy compatibility lane. The structured
calendar browser tests cover the enabled production lane.
Pre-Vite this file served the old docs/index.html
mega-page; that page is deleted and this net now watches dist/.

This test is conditionally skipped when Playwright or npm is not
installed locally — keep `pytest` runnable for dev environments
without the browser/Node dependency. CI installs both explicitly.

Install (one-time, ~120 MB):

    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import http.server
import os
import shutil
import socket
import socketserver
import subprocess
import threading
import time

import pytest

from tests.browser_smoke import (
    birth_profile_cases,
    contextual_profile_cases,
    fixture_cases,
    gochara_cases,
    karnavedha_cases,
    muhurta_matrix_cases,
    muhurta_privacy_cases,
    navigation_cases,
    profile_cases,
    profile_events_cases,
)
from tests.browser_smoke.calendar_fixtures import (
    _install_direct_route_runtime_assets as _install_direct_route_runtime_assets,
)
from tests.browser_smoke.constants import DIST_DIR as DIST_DIR
from tests.browser_smoke.constants import MUHURTA_FIXTURE_DATE as MUHURTA_FIXTURE_DATE
from tests.browser_smoke.constants import REPO_ROOT as REPO_ROOT
from tests.browser_smoke.muhurta_support import (
    _run_muhurta_browser_search as _run_muhurta_browser_search,
)
from tests.browser_smoke.profile_support import (
    _keep_profile_smoke_offline as _keep_profile_smoke_offline,
)
from tests.browser_smoke.profile_support import (
    _wait_for_profile_app as _wait_for_profile_app,
)

playwright_sync = pytest.importorskip(
    'playwright.sync_api',
    reason='Playwright not installed; install with `pip install playwright '
           '&& playwright install chromium` to run browser smoke tests.',
)

sync_playwright = playwright_sync.sync_playwright

def build_site_artifact(*, structured_calendar: bool = False):
    """Build the site into dist/ with the same command the deploy
    workflows use. Skips (not fails) when npm is unavailable so
    Python-only dev environments keep a green `pytest`; a FAILING
    build, however, fails loudly — that's a real regression."""
    npm = shutil.which('npm')
    if npm is None:
        pytest.skip('npm not installed; browser smoke needs the Vite build.')
    if not (REPO_ROOT / 'node_modules').is_dir():
        subprocess.run([npm, 'ci', '--ignore-scripts'], cwd=REPO_ROOT, check=True,
                       capture_output=True, text=True)
    build_env = {**os.environ, 'VITE_STRUCTURED_CALENDAR_ENABLED': str(structured_calendar).lower()}
    proc = subprocess.run([npm, 'run', 'build'], cwd=REPO_ROOT, check=False,
                          capture_output=True, text=True, env=build_env)
    assert proc.returncode == 0, (
        f'`npm run build` failed (exit {proc.returncode}) — the smoke '
        f'tests exercise dist/, so a broken build is a broken site.\n'
        f'stdout: {proc.stdout[-2000:]}\nstderr: {proc.stderr[-2000:]}'
    )
    assert (DIST_DIR / 'index.html').is_file(), (
        'npm run build succeeded but dist/index.html is missing — '
        'check vite.config.ts build.outDir.'
    )
    return DIST_DIR


@pytest.fixture(scope='module')
def vite_build():
    return build_site_artifact()

def _pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Same as SimpleHTTPRequestHandler but doesn't spam stderr per
    request. Tests can be noisy enough already."""

    def do_GET(self):  # noqa: N802 (matches base API)
        if self.path.split('?', 1)[0] == '/rasi_phalalu/latest.json':
            # Production layers this daily runtime artifact onto gh-pages; it
            # must not be checked into or copied from the landing-site source.
            body = b'{"date":"","rashis":{}}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, format, *args):  # noqa: A002 (matches base API)
        return

@pytest.fixture(scope='module')
def docs_server(vite_build):
    """Serve the freshly built dist/ on a free localhost port for the
    duration of the module. Yields the base URL (http://127.0.0.1:PORT).
    (Fixture name kept from the docs/-serving era so the test diff
    stays reviewable; it now serves the deploy artifact.)"""
    port = _pick_free_port()
    def handler(*args, **kwargs):
        return _QuietHandler(*args, directory=str(vite_build), **kwargs)

    httpd = socketserver.TCPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        # Brief wait so the first request doesn't race the bind.
        time.sleep(0.1)
        yield f'http://127.0.0.1:{port}'
    finally:
        httpd.shutdown()
        httpd.server_close()

@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            yield b
        finally:
            b.close()

# Keep the original collection order and node IDs for CI and focused reruns.
test_muhurta_planet_fixture_preserves_scenario_houses = fixture_cases.test_muhurta_planet_fixture_preserves_scenario_houses
test_gold_planet_fixture_preserves_cap_unknown_and_lagna_projection = fixture_cases.test_gold_planet_fixture_preserves_cap_unknown_and_lagna_projection
test_index_loads_without_referenceerror = navigation_cases.test_index_loads_without_referenceerror
test_inline_onclick_surface_is_on_window = navigation_cases.test_inline_onclick_surface_is_on_window
test_daily_surface_is_responsive_and_navigation_remains_usable = navigation_cases.test_daily_surface_is_responsive_and_navigation_remains_usable
test_direct_hash_routes_open_the_expected_surface = navigation_cases.test_direct_hash_routes_open_the_expected_surface
test_guest_profiles_and_consumers_are_responsive_safe_and_ordered = profile_cases.test_guest_profiles_and_consumers_are_responsive_safe_and_ordered
test_profile_detail_onward_actions_carry_the_selected_person = profile_cases.test_profile_detail_onward_actions_carry_the_selected_person
test_birth_details_profile_calls_the_stateless_contract_and_reuses_result = birth_profile_cases.test_birth_details_profile_calls_the_stateless_contract_and_reuses_result
test_guest_profile_keyboard_order_and_native_confirmation = profile_events_cases.test_guest_profile_keyboard_order_and_native_confirmation
test_guest_profile_storage_events_refresh_consumers_without_losing_a_draft = profile_events_cases.test_guest_profile_storage_events_refresh_consumers_without_losing_a_draft
test_chart_aware_muhurta_built_browser_state_matrix = muhurta_matrix_cases.test_chart_aware_muhurta_built_browser_state_matrix
test_karnavedha_daylight_and_chart_browser_matrix = karnavedha_cases.test_karnavedha_daylight_and_chart_browser_matrix
test_karnavedha_bounded_chart_search_is_not_presented_as_resolved = karnavedha_cases.test_karnavedha_bounded_chart_search_is_not_presented_as_resolved
test_gold_screening_accepts_public_terminal_lagna_boundary = muhurta_privacy_cases.test_gold_screening_accepts_public_terminal_lagna_boundary
test_role_copy_never_claims_evaluation_when_chart_facts_were_not_used = muhurta_privacy_cases.test_role_copy_never_claims_evaluation_when_chart_facts_were_not_used
test_chart_aware_muhurta_profile_role_and_share_stay_private = muhurta_privacy_cases.test_chart_aware_muhurta_profile_role_and_share_stay_private
test_muhurta_finder_search_does_not_throw_referenceerror = contextual_profile_cases.test_muhurta_finder_search_does_not_throw_referenceerror
test_daily_horoscope_contextual_profile_returns_and_stays_isolated = contextual_profile_cases.test_daily_horoscope_contextual_profile_returns_and_stays_isolated
test_muhurta_contextual_profile_preserves_task_and_other_journey = contextual_profile_cases.test_muhurta_contextual_profile_preserves_task_and_other_journey
test_gochara_unavailable_state_spans_the_chart = gochara_cases.test_gochara_unavailable_state_spans_the_chart
test_documentation_diagrams_and_tables_do_not_overflow_page = gochara_cases.test_documentation_diagrams_and_tables_do_not_overflow_page
test_gochara_rasi_view_renders_verdicts_and_phalalu = gochara_cases.test_gochara_rasi_view_renders_verdicts_and_phalalu
