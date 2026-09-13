"""Browser smoke profile support; no automatic test collection."""

from __future__ import annotations


def _capture_console(page):
    """Returns a list that page-error and console events will
    append to. The test then inspects the list."""
    captured = []
    page.on('pageerror', lambda exc: captured.append(('pageerror', str(exc))))
    page.on('console', lambda msg: (
        captured.append(('console.error', msg.text)) if msg.type == 'error'
        else None
    ))
    return captured

PROFILE_VIEWPORTS = (
    (390, 844, 'mobile'),
    (768, 1024, 'mobile'),
    (853, 900, 'mobile'),
    (1024, 768, 'desktop'),
    (1440, 900, 'desktop'),
)

HOSTILE_PROFILE_NAME = (
    '<img src=x onerror="window.__hostileExecuted=true"> Ready'
)

LONG_PROFILE_NAME = 'N' * 80

READY_PROFILE_ID = 'guest_ready_001'

INCOMPLETE_PROFILE_ID = 'guest_needs_001'

def _profile_rows():
    """Exact persisted v1 shape used by the browser profile store.

    The first name is deliberately executable if a renderer ever regresses to
    innerHTML. Every personalized surface must preserve it as literal text.
    """
    return [
        {
            'id': READY_PROFILE_ID,
            'schemaVersion': 1,
            'name': HOSTILE_PROFILE_NAME,
            'nak': 'Rohini',
            'pada': '',
            'lagna': 'Kanya',
        },
        {
            'id': INCOMPLETE_PROFILE_ID,
            'schemaVersion': 1,
            'name': LONG_PROFILE_NAME,
            'nak': '',
            'pada': '',
            'lagna': '',
        },
    ]

def _keep_profile_smoke_offline(target):
    """Make profile smoke deterministic without hiding local build failures."""
    target.route(
        'https://gc.zgo.at/**',
        lambda route: route.fulfill(
            status=200,
            content_type='application/javascript',
            body='',
        ),
    )
    target.route(
        'https://panchangam.goatcounter.com/**',
        lambda route: route.fulfill(status=204, body=''),
    )
    target.route(
        'https://panchangam.astrochaganti.com/**',
        lambda route: route.fulfill(
            status=404,
            content_type='application/json',
            body='{}',
        ),
    )

def _wait_for_profile_app(page):
    page.wait_for_function(
        "typeof window.switchTool === 'function' && "
        "['mobile', 'desktop'].includes(document.body.dataset.mode)",
        timeout=10000,
    )

def _seed_profile_surfaces(page):
    page.evaluate(
        """profiles => {
            localStorage.clear();
            localStorage.setItem('tc-tb-profiles', JSON.stringify(profiles));
            localStorage.setItem('tc-go-view', 'profile:guest_ready_001');
            localStorage.setItem(
                'tc-mu-profile-ids', JSON.stringify(['guest_ready_001'])
            );
        }""",
        _profile_rows(),
    )
    page.reload(wait_until='domcontentloaded', timeout=15000)
    _wait_for_profile_app(page)
