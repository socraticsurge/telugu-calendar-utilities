"""Browser smoke calendar fixtures; no automatic test collection."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tests.browser_smoke.constants import (
    MUHURTA_FEED_FIXTURE,
    MUHURTA_FIXTURE_DATE,
    MUHURTA_PLANET_NAMES,
    MUHURTA_PLANET_RASHIS,
)


def _karnavedha_feed_fixture(scenario):
    """Control only the two daylight-transition predicates in the real ICS."""
    endings = {
        'karnavedha-pass': ('23:30', '23:40'),
        'karnavedha-chart-fail': ('23:30', '23:40'),
        'karnavedha-chart-unknown': ('23:30', '23:40'),
        'karnavedha-unsupported': ('23:30', '23:40'),
        'karnavedha-offline': ('23:30', '23:40'),
        'karnavedha-tithi-fail': ('12:00', '23:40'),
        'karnavedha-nakshatra-fail': ('23:30', '12:30'),
        'karnavedha-both-fail': ('12:00', '12:30'),
        'karnavedha-unknown': ('18:50', '23:40'),
    }
    tithi_end, nakshatra_end = endings[scenario]
    # read_text normalizes CRLF; unfold the generated continuations so each
    # DESCRIPTION can be adjusted without relying on its physical fold width.
    feed = MUHURTA_FEED_FIXTURE.read_text(encoding='utf-8').replace('\n ', '')
    for limb, end in (('Tithi', tithi_end), ('Nakshatra', nakshatra_end)):
        feed, count = re.subn(
            rf'({limb}:\s+.+?\s+\d{{2}}:\d{{2}}'
            rf'(?: \([+-]1\))? – )\d{{2}}:\d{{2}}(?: \([+-]1\))?',
            rf'\g<1>{end}',
            feed,
        )
        assert count == 3, f'expected all three {limb} fixture rows'
    return feed

def _karnavedha_bounded_feed_fixture(day_count=15):
    """Repeat the reviewed passing day until the chart safety budget binds."""
    feed = _karnavedha_feed_fixture('karnavedha-pass')
    header, remainder = feed.split('BEGIN:VEVENT\n', 1)
    event, _ = remainder.split('END:VEVENT\n', 1)
    base = datetime.fromisoformat(MUHURTA_FIXTURE_DATE)
    events = []
    for offset in range(day_count):
        current = base + timedelta(days=offset)
        following = current + timedelta(days=1)
        block = event.replace(
            '20260611', current.strftime('%Y%m%d'),
        ).replace(
            '20260612', following.strftime('%Y%m%d'),
        ).replace(
            '2026-06-11', current.strftime('%Y-%m-%d'),
        )
        events.append(f'BEGIN:VEVENT\n{block}END:VEVENT\n')
    return f'{header}{"".join(events)}END:VCALENDAR\n'

# Captured from /feeds/hyderabad-lagna.json on 2026-09-04. The complete
# downloaded artifact had SHA-256
# 91833798aa0571a962ce9a337b899c1cbf7d7ac9f0ab993a78611d9aec4c5d70.
PUBLIC_HYDERABAD_2026_09_17_LAGNA_DAY = {
    'date': '2026-09-17',
    'sunrise': '06:04',
    'guruCombust': False,
    'shukraCombust': False,
    'lagna0': 4,
    'transitions': [
        [4, 5], [129, 6], [259, 7], [393, 8], [519, 9],
        [630, 10], [728, 11], [823, 0], [928, 1], [1049, 2],
        [1181, 3], [1313, 4], [1440, 5],
    ],
    'cycleEnd': 1440,
}

def _muhurta_lagna_fixture():
    """Known per-day boundary map used by exact-window browser checks."""
    return {
        'start': MUHURTA_FIXTURE_DATE,
        'days': [
            {
                'date': date,
                'sunrise': '05:41',
                'lagna0': 3,
                'transitions': [
                    [60, 4], [120, 5], [180, 6], [240, 7],
                    [300, 8], [360, 9], [410, 10], [480, 11],
                    [540, 0], [600, 1], [660, 2], [720, 3],
                ],
                'cycleEnd': 1440,
            }
            for date in ('2026-06-11', '2026-06-12', '2026-06-13')
        ],
    }

def _court_lagna_fixture():
    """Keep all pinned Court candidate windows inside one stable Mesha span."""
    return {
        'start': MUHURTA_FIXTURE_DATE,
        'days': [
            {
                'date': date,
                'sunrise': '05:41',
                'lagna0': 11,
                'transitions': [
                    [50, 0], [900, 1], [901, 2], [902, 3],
                    [903, 4], [904, 5], [905, 6], [906, 7],
                    [907, 8], [908, 9], [909, 10], [910, 11],
                ],
                'cycleEnd': 1440,
            }
            for date in ('2026-06-11', '2026-06-12', '2026-06-13')
        ],
    }

def _terminal_boundary_lagna_fixture():
    """Use the exact public boundary shape with the pinned browser feed dates.

    Only the join key changes because the browser matrix intentionally uses the
    immutable June ICS fixture; sunrise, Lagna and transition evidence remain
    field-for-field equivalent to the public Hyderabad 2026-09-17 day object.
    """
    return {
        'start': MUHURTA_FIXTURE_DATE,
        'days': [
            {
                **PUBLIC_HYDERABAD_2026_09_17_LAGNA_DAY,
                'date': date,
            }
            for date in ('2026-06-11', '2026-06-12', '2026-06-13')
        ],
    }

def _karnavedha_boundary_lagna_fixture():
    """Place one validated Lagna transition on a surviving slot edge."""
    fixture = json.loads(json.dumps(_muhurta_lagna_fixture()))
    for day in fixture['days']:
        day['transitions'][6] = [368, 10]
    return fixture

def _karnavedha_bounded_lagna_fixture(day_count=15):
    """Provide validated per-day Lagna evidence for the expanded fixture."""
    template = _muhurta_lagna_fixture()['days'][0]
    base = datetime.fromisoformat(MUHURTA_FIXTURE_DATE)
    return {
        'start': MUHURTA_FIXTURE_DATE,
        'days': [
            {
                **template,
                'date': (base + timedelta(days=offset)).strftime('%Y-%m-%d'),
                'transitions': [list(item) for item in template['transitions']],
            }
            for offset in range(day_count)
        ],
    }

def _install_direct_route_runtime_assets(page):
    """Stage production-generated dependencies for direct-route smoke tests."""
    feed_text = MUHURTA_FEED_FIXTURE.read_text(encoding='utf-8')
    today = time.strftime('%Y-%m-%d')
    gochara = {
        'start': today,
        'grahas': list(MUHURTA_PLANET_NAMES),
        'rasis': list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena'],
        'days': [[0, 1, 2, 3, 4, 5, 6, 7, 8]],
        'retro': [[False, False, False, False, False, False, True, True, True]],
    }
    page.route(
        '**/feeds/*.ics',
        lambda route: route.fulfill(
            status=200, content_type='text/calendar', body=feed_text,
        ),
    )
    page.route(
        '**/feeds/*-lagna.json',
        lambda route: route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps(_muhurta_lagna_fixture()),
        ),
    )
    page.route(
        '**/gochara.json',
        lambda route: route.fulfill(
            status=200, content_type='application/json',
            body=json.dumps(gochara),
        ),
    )
    page.route(
        '**/rasi_phalalu/latest.json',
        lambda route: route.fulfill(
            status=200, content_type='application/json',
            body=json.dumps({'date': '', 'rashis': {}}),
        ),
    )

def _festival_navigation_feed_fixture():
    """Reuse a real feed shape on the date pinned by the navigation test.

    This fixture checks only that the public window function selects and
    renders its requested date. It deliberately does not establish a
    Panchangam calculation claim for the shifted dates.
    """
    feed_text = MUHURTA_FEED_FIXTURE.read_text(encoding='utf-8')
    replacements = (
        ('20260611', '20260831'),
        ('20260612', '20260901'),
        ('20260613', '20260902'),
        ('20260614', '20260903'),
        ('2026-06-11', '2026-08-31'),
        ('2026-06-12', '2026-09-01'),
        ('2026-06-13', '2026-09-02'),
    )
    for source, target in replacements:
        feed_text = feed_text.replace(source, target)
    return feed_text

def _current_day_feed_fixture():
    """Shift the real three-day feed shape onto the browser's current date.

    The responsive-shell test needs populated day-cycle markup, not a live
    Panchangam claim. Keeping the request local makes that UI contract
    deterministic while preserving the fixture's reviewed data shape.
    """
    feed_text = MUHURTA_FEED_FIXTURE.read_text(encoding='utf-8')
    source_start = datetime.fromisoformat(MUHURTA_FIXTURE_DATE)
    target_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for offset in range(4):
        source = source_start + timedelta(days=offset)
        target = target_start + timedelta(days=offset)
        feed_text = feed_text.replace(
            source.strftime('%Y%m%d'), target.strftime('%Y%m%d'),
        ).replace(
            source.strftime('%Y-%m-%d'), target.strftime('%Y-%m-%d'),
        )
    return feed_text

def _fixture_lagna_for_instant(instant, lagna_fixture=None):
    """Resolve the same canonical fixture Lagna the browser will project."""
    local = datetime.fromisoformat(instant.replace('Z', '+00:00')).astimezone(
        ZoneInfo('Asia/Kolkata')
    )
    minute = local.hour * 60 + local.minute
    day = (lagna_fixture or _muhurta_lagna_fixture())['days'][0]
    sunrise_hour, sunrise_minute = map(int, day['sunrise'].split(':'))
    offset = minute - (sunrise_hour * 60 + sunrise_minute)
    starts = [(0, day['lagna0']), *day['transitions']]
    rashi_index = day['lagna0']
    for start, candidate in starts:
        if start > offset:
            break
        rashi_index = candidate
    return (
        list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    )[rashi_index]

def _fixture_navamsa_rashi(rashi, degree):
    rashis = list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    rashi_index = rashis.index(rashi)
    modality = rashi_index % 3
    start = (
        rashi_index if modality == 0
        else (rashi_index + 8) % 12 if modality == 1
        else (rashi_index + 4) % 12
    )
    return rashis[(start + int(degree / (30 / 9))) % 12]
