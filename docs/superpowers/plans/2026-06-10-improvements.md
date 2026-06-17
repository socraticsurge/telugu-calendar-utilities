# Panchangam Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seven targeted improvements across MCP tools, ICS feeds, the landing page, and feed generation performance — no new dependencies, no architectural changes.

**Architecture:** Each task is self-contained. Tasks 1–3 are one-file fixes. Tasks 4–5 add new capabilities to existing modules. Tasks 6–7 are frontend and performance work. Any order works except Task 7 (eclipse precomputation) which touches the same engines as Tasks 1–3; do Task 7 last to avoid merge conflicts.

**Tech Stack:** Python 3.11, pyswisseph, icalendar, FastMCP, plain HTML/JS (no build step for the landing page)

---

## File Map

| File | Tasks that touch it |
|------|---------------------|
| `telugu_panchangam/mcp/tools.py` | 1, 5 |
| `telugu_panchangam/mcp/server.py` | 5 |
| `telugu_panchangam/generators/ics.py` | 2 |
| `docs/index.html` | 3, 6 |
| `telugu_panchangam/special_yogas.py` | 4 |
| `telugu_panchangam/eclipses.py` | 7 |
| `telugu_panchangam/engines/drik.py` | 7 |
| `telugu_panchangam/engines/surya_siddhanta.py` | 7 |
| `telugu_panchangam/engines/vakya.py` | 7 |
| `telugu_panchangam/generate.py` | 7 |
| `tests/test_mcp_tools.py` | 1, 5 |
| `tests/test_ics_generator.py` | 2 |
| `tests/test_special_yogas.py` | 4 |
| `tests/test_eclipses.py` | 7 |

---

## Task 1: Choghadiya end times in MCP output

The `tool_get_panchangam` response returns Choghadiya as `[{name, start}]` — no `end`. The `Window` model already has an `end` field. One-line fix in `tools.py`.

**Files:**
- Modify: `telugu_panchangam/mcp/tools.py` (around line 167)
- Modify: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_mcp_tools.py`:

```python
def test_choghadiya_has_end_time():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    chog = result['choghadiya']
    assert len(chog) == 8
    for entry in chog:
        assert 'end' in entry, "Choghadiya entry missing 'end'"
        # end must be a valid HH:MM string
        assert len(entry['end']) == 5
        assert entry['end'][2] == ':'
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_mcp_tools.py::test_choghadiya_has_end_time -v
```

Expected: FAIL — `AssertionError: Choghadiya entry missing 'end'`

- [ ] **Step 3: Fix the choghadiya serialisation in `tools.py`**

Find the choghadiya block (search for `'name': w.name`) and change:

```python
# Before
'choghadiya': [
    {'name': w.name, 'start': _fmt_time(w.start, tz)}
    for w in day.choghadiya
],

# After
'choghadiya': [
    {'name': w.name, 'start': _fmt_time(w.start, tz), 'end': _fmt_time(w.end, tz)}
    for w in day.choghadiya
],
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_mcp_tools.py::test_choghadiya_has_end_time -v
```

Expected: PASS

- [ ] **Step 5: Run full suite to check for regressions**

```bash
pytest tests/ -q
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/mcp/tools.py tests/test_mcp_tools.py
git commit -m "fix: include end time in MCP choghadiya output"
```

---

## Task 2: Ayanam and Rituvu in ICS event description

Both fields exist on `PanchangamDay` (`day.ayanam` e.g. `"Uttarayanam"`, `day.rituvu` e.g. `"Vasanta"`) and are already in the MCP output, but are dropped from the ICS description. Adding them to the header line costs nothing.

**Files:**
- Modify: `telugu_panchangam/generators/ics.py`
- Modify: `tests/test_ics_generator.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_ics_generator.py`:

```python
def test_ayanam_and_rituvu_in_description():
    days = _make_days(1)
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Ayanam:' in description
    assert 'Rituvu:' in description
```

- [ ] **Step 2: Check what `_make_days` produces for ayanam/rituvu**

Open `tests/test_ics_generator.py` and find `_make_days`. If `PanchangamDay` is constructed manually in that helper, confirm `ayanam` and `rituvu` fields have non-empty default values (they should — they're required string fields on the dataclass set to `'Uttarayanam'` and `'Vasanta'` by the test helper). If the helper doesn't set them, add them:

```python
# In _make_days, ensure these are present in the PanchangamDay constructor call:
ayanam='Uttarayanam',
rituvu='Vasanta',
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_ics_generator.py::test_ayanam_and_rituvu_in_description -v
```

Expected: FAIL — `AssertionError: assert 'Ayanam:' in ...`

- [ ] **Step 4: Add ayanam and rituvu to the ICS header line**

In `telugu_panchangam/generators/ics.py`, inside `_description()`, change the first line of the `lines` list:

```python
# Before
f'{day.samvatsara}  ·  {day.maasam} Maasam  ·  {day.paksham} Paksham  ·  {day.vaaram}',

# After
f'{day.samvatsara}  ·  {day.maasam} Maasam  ·  {day.paksham} Paksham  ·  {day.vaaram}',
f'Ayanam: {day.ayanam}  ·  Rituvu: {day.rituvu}',
```

This inserts a second header line. The blank line that follows already separates it from Pancha Anga.

- [ ] **Step 5: Run the test**

```bash
pytest tests/test_ics_generator.py::test_ayanam_and_rituvu_in_description -v
```

Expected: PASS

- [ ] **Step 6: Run full suite**

```bash
pytest tests/ -q
```

Expected: all pass

- [ ] **Step 7: Update landing page parser to skip the new line**

The `parseDescription` function in `docs/index.html` iterates all lines and ignores anything it doesn't match. The new `Ayanam: X  ·  Rituvu: Y` line won't break existing parsing, but optionally capture it:

Find the `parseDescription` function and add after the sky-events regex:

```javascript
if ((m = line.match(/^Ayanam:\s+(.+?)\s+·\s+Rituvu:\s+(.+)$/))) {
  data.ayanam = m[1].trim();
  data.rituvu = m[2].trim();
  continue;
}
```

Also add `ayanam: null, rituvu: null` to the initial `data` object.

Then in `renderPreview`, add the row to the "Sky" section:

```javascript
if (data.ayanam) rows += row('Ayanam / Rituvu', `${data.ayanam} · ${data.rituvu}`);
```

Insert this line just before `rows += groupHead('Sky')`.

- [ ] **Step 8: Commit**

```bash
git add telugu_panchangam/generators/ics.py docs/index.html tests/test_ics_generator.py
git commit -m "feat: add Ayanam and Rituvu to ICS description and landing page preview"
```

---

## Task 3: webcal:// URL — add testable https:// link

Users who paste a `webcal://` URL into a browser get a blank page or an error. Adding a small secondary link that swaps `webcal://` to `https://` lets anyone verify the feed renders before subscribing.

**Files:**
- Modify: `docs/index.html`

No tests needed — this is purely presentational HTML/JS.

- [ ] **Step 1: Add an "Open in browser" link below the URL box**

Find the subscribe card section. After the `<div class="url-box" id="sub-url">` and the Copy button, add:

```html
<a id="sub-https-link" href="#" target="_blank" rel="noopener"
   style="margin-left:0.75rem;font-size:0.8rem;color:var(--indigo);font-weight:600;">
  Open feed in browser ↗
</a>
```

- [ ] **Step 2: Keep the https link in sync with the webcal URL**

Find the `updateSubscribeUrl()` function in the `<script>` block and add the https link update:

```javascript
function updateSubscribeUrl() {
  const city = document.getElementById('sub-city').value;
  const system = document.getElementById('sub-system').value;
  const url = `webcal://${FEED_BASE_URL.replace('https://', '')}${feedFilename(city, system)}`;
  document.getElementById('sub-url').textContent = url;
  // New: keep the https preview link in sync
  const httpsUrl = `${FEED_BASE_URL}${feedFilename(city, system)}`;
  document.getElementById('sub-https-link').href = httpsUrl;
}
```

- [ ] **Step 3: Verify visually**

Open `docs/index.html` in a browser (or via the local preview). Change city/system — confirm the "Open feed in browser" link updates and clicking it opens the `.ics` file.

- [ ] **Step 4: Commit**

```bash
git add docs/index.html
git commit -m "feat: add 'open in browser' https link alongside webcal URL"
```

---

## Task 4: Dvipushkara and Tripushkara yogas

Two more commonly observed South Indian yogas that require a three-way match (Vara + Tithi + Nakshatra simultaneously).

**Dvipushkara Yoga:**
- Vara: Sunday, Tuesday, or Saturday
- Tithi number (1–15 within paksha): 2, 7, or 12
- Nakshatra: Mrigashira, Chitra, or Dhanishtha

**Tripushkara Yoga:**
- Vara: Sunday, Tuesday, or Saturday  
- Tithi number: 3, 8, or 13
- Nakshatra: Krittika, Punarvasu, Uttara Phalguni, Vishakha, Uttara Ashadha, or Purva Bhadrapada

**Files:**
- Modify: `telugu_panchangam/special_yogas.py`
- Modify: `tests/test_special_yogas.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_special_yogas.py`:

```python
def test_dvipushkara_yoga_match():
    # Adivaram (Sunday) + Dwitiya (tithi 2) + Mrigashira → Dvipushkara
    # Dwitiya = TITHI_NAMES[1], (1 % 15) + 1 = 2. Use 'Shukla Dwitiya'.
    result = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Mrigashira')
    assert 'Dvipushkara Yoga' in result


def test_dvipushkara_yoga_no_match_wrong_vara():
    # Somavaram is not a Dvipushkara vara
    result = get_special_yogas('Somavaram', 'Shukla Dwitiya', 'Mrigashira')
    assert 'Dvipushkara Yoga' not in result


def test_dvipushkara_yoga_no_match_wrong_nakshatra():
    result = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Rohini')
    assert 'Dvipushkara Yoga' not in result


def test_tripushkara_yoga_match():
    # Mangalavaram (Tuesday) + Tritiya (tithi 3) + Krittika → Tripushkara
    # Tritiya = TITHI_NAMES[2], (2 % 15) + 1 = 3. Use 'Shukla Tritiya'.
    result = get_special_yogas('Mangalavaram', 'Shukla Tritiya', 'Krittika')
    assert 'Tripushkara Yoga' in result


def test_tripushkara_yoga_no_match_wrong_vara():
    result = get_special_yogas('Guruvaram', 'Shukla Tritiya', 'Krittika')
    assert 'Tripushkara Yoga' not in result


def test_dvipushkara_and_other_yoga_can_coexist():
    # Adivaram + Saptami (7) + Hasta → Dvipushkara (Sunday+Saptami+Mrigashira? No.)
    # Adivaram + Saptami + Mrigashira: Saptami tithi number is 7 (TITHI_NAMES[6], (6%15)+1=7)
    # Use 'Shukla Saptami'. Also Adivaram+Hasta is Sarvartha Siddhi AND Amrita Siddhi.
    # Hasta is NOT a Dvipushkara nakshatra so no Dvipushkara. Test coexistence differently:
    # Adivaram + Dwitiya (2) + Hasta: Sarvartha Siddhi (Adivaram+Hasta) + Amrita Siddhi (Adivaram+Hasta)
    # but NOT Dvipushkara (Hasta not in Dvipushkara nakshatras).
    result = get_special_yogas('Adivaram', 'Shukla Dwitiya', 'Mrigashira')
    # Mrigashira is NOT in Adivaram's Sarvartha Siddhi set and NOT Amrita Siddhi for Adivaram (Hasta is)
    # so only Dvipushkara
    assert 'Dvipushkara Yoga' in result
    assert 'Amrita Siddhi Yoga' not in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_special_yogas.py::test_dvipushkara_yoga_match tests/test_special_yogas.py::test_tripushkara_yoga_match -v
```

Expected: FAIL — `AssertionError: assert 'Dvipushkara Yoga' in []`

- [ ] **Step 3: Add the tables and logic to `special_yogas.py`**

Add after the `_DAGDHA_YOGA` dict:

```python
_PUSHKARA_VARAS: set[str] = {'Adivaram', 'Mangalavaram', 'Shanivaram'}

_DVIPUSHKARA_TITHIS: set[int] = {2, 7, 12}
_DVIPUSHKARA_NAKSHATRAS: set[str] = {'Mrigashira', 'Chitra', 'Dhanishtha'}

_TRIPUSHKARA_TITHIS: set[int] = {3, 8, 13}
_TRIPUSHKARA_NAKSHATRAS: set[str] = {
    'Krittika', 'Punarvasu', 'Uttara Phalguni',
    'Vishakha', 'Uttara Ashadha', 'Purva Bhadrapada',
}
```

Then extend `get_special_yogas` to append these after the existing Dagdha check:

```python
    if vaaram in _PUSHKARA_VARAS:
        if tithi_number in _DVIPUSHKARA_TITHIS and nakshatra_name in _DVIPUSHKARA_NAKSHATRAS:
            yogas.append('Dvipushkara Yoga')
        if tithi_number in _TRIPUSHKARA_TITHIS and nakshatra_name in _TRIPUSHKARA_NAKSHATRAS:
            yogas.append('Tripushkara Yoga')

    return yogas
```

- [ ] **Step 4: Run all special yoga tests**

```bash
pytest tests/test_special_yogas.py -v
```

Expected: all pass

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -q
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/special_yogas.py tests/test_special_yogas.py
git commit -m "feat: add Dvipushkara and Tripushkara yoga detection"
```

---

## Task 5: MCP `get_panchangam_range` tool

Lets an AI agent retrieve a compact summary for a date span in a single call instead of N calls. Capped at 31 days to keep responses tractable.

**Files:**
- Modify: `telugu_panchangam/mcp/tools.py`
- Modify: `telugu_panchangam/mcp/server.py`
- Modify: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_tools.py`:

```python
def test_get_panchangam_range_basic():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-10', '2026-06-12', 'Hyderabad'))
    assert 'days' in result
    assert len(result['days']) == 3
    day = result['days'][0]
    for key in ('date', 'vaaram', 'tithi', 'nakshatra', 'sunrise', 'sunset',
                'auspicious', 'inauspicious', 'special_days', 'special_yogas'):
        assert key in day, f"Missing key in range day: {key}"


def test_get_panchangam_range_exceeds_limit():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-01-01', '2026-06-01', 'Hyderabad'))
    assert 'error' in result


def test_get_panchangam_range_invalid_dates():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-12', '2026-06-10', 'Hyderabad'))
    assert 'error' in result


def test_get_panchangam_range_auspicious_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam_range
    result = json.loads(tool_get_panchangam_range('2026-06-10', '2026-06-10', 'Hyderabad'))
    day = result['days'][0]
    assert 'brahma_muhurta' in day['auspicious']
    assert 'rahu_kalam' in day['inauspicious']
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_mcp_tools.py::test_get_panchangam_range_basic -v
```

Expected: FAIL — `ImportError: cannot import name 'tool_get_panchangam_range'`

- [ ] **Step 3: Implement `tool_get_panchangam_range` in `tools.py`**

Add this function after `tool_get_muhurta`:

```python
def tool_get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    """Return a compact Panchangam summary for each day in [start_date, end_date].
    Maximum span: 31 days."""
    try:
        from datetime import timedelta
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError(f"end_date must be >= start_date.")
        if (end - start).days > 30:
            raise ValueError("Date range exceeds 31-day limit. Use multiple calls for longer spans.")
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]
        tz = loc.timezone

        days = []
        d = start
        while d <= end:
            day = engine.calculate(d, loc)
            days.append({
                'date': d.isoformat(),
                'vaaram': day.vaaram,
                'tithi': day.tithi.name,
                'nakshatra': day.nakshatra.name,
                'yoga': day.yoga.name,
                'sunrise': _fmt_time(day.sunrise, tz),
                'sunset': _fmt_time(day.sunset, tz),
                'auspicious': {
                    'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                    'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                    'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
                },
                'inauspicious': {
                    'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                    'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                    'yamagandam':   _window_to_dict(day.yamagandam, tz),
                    'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                    'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
                },
                'eclipse': _eclipse_to_dict(day.eclipse, tz),
                'special_yogas': day.special_yogas,
                'special_days': _special_events(day),
                'is_special': bool(_special_events(day)),
            })
            d += timedelta(days=1)

        return json.dumps({
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'system': system,
            'days': days,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})
```

- [ ] **Step 4: Register the tool in `server.py`**

Add the import:

```python
from telugu_panchangam.mcp.tools import (
    tool_list_supported_cities,
    tool_get_panchangam,
    tool_get_muhurta,
    tool_get_special_days,
    tool_get_panchangam_range,   # new
)
```

Add the tool registration after `get_muhurta`:

```python
@mcp.tool()
def get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns a compact Panchangam summary for each day in a date range (max 31 days). Each day includes: Tithi, Nakshatra, Yoga, Sunrise/Sunset, all auspicious and inauspicious windows, eclipse (if any), special yogas, and special day flags. Useful for planning muhurtas over a week or comparing multiple days. Args: start_date=YYYY-MM-DD, end_date=YYYY-MM-DD, city=city name, system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_panchangam_range(start_date, end_date, city, system, latitude, longitude, timezone)
```

- [ ] **Step 5: Run all new tests**

```bash
pytest tests/test_mcp_tools.py::test_get_panchangam_range_basic \
       tests/test_mcp_tools.py::test_get_panchangam_range_exceeds_limit \
       tests/test_mcp_tools.py::test_get_panchangam_range_invalid_dates \
       tests/test_mcp_tools.py::test_get_panchangam_range_auspicious_keys -v
```

Expected: all PASS

- [ ] **Step 6: Run full suite**

```bash
pytest tests/ -q
```

Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add telugu_panchangam/mcp/tools.py telugu_panchangam/mcp/server.py tests/test_mcp_tools.py
git commit -m "feat: add get_panchangam_range MCP tool for multi-day queries"
```

---

## Task 6: Landing page date picker

The preview card currently shows today only. Adding a date input lets users browse to any date covered by the feed (roughly today − a few days to 18 months ahead).

**Files:**
- Modify: `docs/index.html`

No Python tests. Verify manually by opening the page in a browser.

- [ ] **Step 1: Add a date selector to the preview card**

In the "Today's Panchangam" card, find the `selector-row` div (the one with `tp-city` and `tp-system`) and add a third selector:

```html
<div class="selector">
  <label for="tp-date">Date</label>
  <input type="date" id="tp-date"
         style="font-size:0.85rem;padding:0.4rem 0.6rem;border-radius:8px;
                border:1px solid var(--indigo-border);background:var(--indigo-bg);
                color:var(--indigo);font-weight:600;min-width:140px;font-family:inherit;">
</div>
```

- [ ] **Step 2: Set the date input default to today on page load**

In the `// --- Init ---` section at the bottom of the script, add before `loadPreview()`:

```javascript
const todayISO = new Date().toISOString().slice(0, 10);
document.getElementById('tp-date').value = todayISO;
```

Also wire up the change event:

```javascript
document.getElementById('tp-date').addEventListener('change', loadPreview);
```

- [ ] **Step 3: Update `todayStamp()` to read from the date input**

Replace the existing `todayStamp` function:

```javascript
// Before
function todayStamp() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
}

// After
function todayStamp() {
  const val = document.getElementById('tp-date')?.value;
  if (val) return val.replace(/-/g, '');
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
}
```

- [ ] **Step 4: Update `formatToday()` to show the selected date, not always today**

Replace `formatToday`:

```javascript
// Before
function formatToday() {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

// After
function formatToday() {
  const val = document.getElementById('tp-date')?.value;
  const d = val ? new Date(val + 'T00:00:00') : new Date();
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}
```

- [ ] **Step 5: Verify in browser**

Open `docs/index.html` directly (or via a local server). Confirm:
- Defaults to today's panchangam
- Changing the date re-renders the preview for the chosen date
- A date with a known special yoga (e.g. 2026-06-11, Sarvartha Siddhi Yoga) shows the yoga section
- A date outside the feed window shows the "Preview unavailable" error message

- [ ] **Step 6: Commit**

```bash
git add docs/index.html
git commit -m "feat: add date picker to landing page preview — browse any date in feed window"
```

---

## Task 7: Eclipse precomputation for faster feed generation

**Problem:** `generate.py` calls `swe.sol_eclipse_when_glob` and `swe.lun_eclipse_when` once per day per feed. With 66 feeds × 540 days × 2 eclipse searches = ~71,000 pyswisseph calls just for eclipse detection. There are only 3–5 eclipses in any 18-month window.

**Fix:** Pre-compute all eclipses in the generation window once (not per city), yielding ~20 total swe calls. Then for each day, skip the search entirely if no eclipse falls on that day; only compute per-location visibility for the 3–5 days that do have an eclipse.

This change is backward-compatible: single-day queries from the MCP server continue to call `get_eclipse_for_date()` as before.

**Files:**
- Modify: `telugu_panchangam/eclipses.py`
- Modify: `telugu_panchangam/engines/drik.py`
- Modify: `telugu_panchangam/engines/surya_siddhanta.py`
- Modify: `telugu_panchangam/engines/vakya.py`
- Modify: `telugu_panchangam/generate.py`
- Modify: `tests/test_eclipses.py`

- [ ] **Step 1: Write tests for the new precomputation function**

Add to `tests/test_eclipses.py`:

```python
def test_list_eclipses_in_range_finds_known_lunar():
    from telugu_panchangam.eclipses import list_eclipses_in_range
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    # The 2025-09-07 total lunar eclipse should be in a range spanning that month
    jd_start = local_midnight_jd(date(2025, 9, 1), 'Asia/Kolkata')
    jd_end = local_midnight_jd(date(2025, 9, 30), 'Asia/Kolkata')
    eclipses = list_eclipses_in_range(jd_start, jd_end)
    kinds = [e['kind'] for e in eclipses]
    assert 'Lunar' in kinds


def test_list_eclipses_in_range_no_eclipse_empty_period():
    from telugu_panchangam.eclipses import list_eclipses_in_range
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    # A two-day window with no eclipse should return an empty list
    jd_start = local_midnight_jd(date(2024, 6, 14), 'UTC')
    jd_end = local_midnight_jd(date(2024, 6, 16), 'UTC')
    eclipses = list_eclipses_in_range(jd_start, jd_end)
    assert eclipses == []


def test_get_eclipse_from_precomputed_matches_get_eclipse_for_date():
    from telugu_panchangam.eclipses import (
        list_eclipses_in_range, get_eclipse_from_precomputed, get_eclipse_for_date
    )
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    eclipse_date = date(2025, 9, 7)
    jd_start = local_midnight_jd(date(2025, 9, 1), 'Asia/Kolkata')
    jd_end = local_midnight_jd(date(2025, 9, 30), 'Asia/Kolkata')
    precomputed = list_eclipses_in_range(jd_start, jd_end)
    # Both paths should return equivalent results for Hyderabad
    direct = get_eclipse_for_date(eclipse_date, HYD)
    from_cache = get_eclipse_from_precomputed(eclipse_date, precomputed, HYD)
    assert direct is not None
    assert from_cache is not None
    assert direct.kind == from_cache.kind
    assert direct.subtype == from_cache.subtype
    assert direct.visible == from_cache.visible
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_eclipses.py::test_list_eclipses_in_range_finds_known_lunar -v
```

Expected: FAIL — `ImportError: cannot import name 'list_eclipses_in_range'`

- [ ] **Step 3: Add `list_eclipses_in_range` and `get_eclipse_from_precomputed` to `eclipses.py`**

Add after the existing `_lunar_eclipse` helper function:

```python
def list_eclipses_in_range(jd_start: float, jd_end: float) -> list[dict]:
    """Return all solar and lunar eclipses whose maximum falls within [jd_start, jd_end].
    Each dict has: kind, subtype, jd_max, jd_start, jd_end.
    Does NOT compute per-location visibility — that is done in get_eclipse_from_precomputed."""
    eclipses: list[dict] = []

    # Walk solar eclipses forward through the range
    jd = jd_start
    while True:
        try:
            retflag, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
        except Exception:
            break
        if retflag == 0 or tret[0] > jd_end:
            break
        if tret[0] >= jd_start:
            eclipses.append({
                'kind': 'Solar',
                'subtype': _subtype(retflag, _SOLAR_SUBTYPE_BITS),
                'jd_max': tret[0],
                'jd_start': tret[2],
                'jd_end': tret[3],
            })
        jd = tret[0] + 1.0  # advance past this eclipse

    # Walk lunar eclipses forward through the range
    jd = jd_start
    while True:
        try:
            retflag, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
        except Exception:
            break
        if retflag == 0 or tret[0] > jd_end:
            break
        jd_s, jd_e = (tret[2], tret[3]) if tret[2] else (tret[6], tret[7])
        if tret[0] >= jd_start:
            eclipses.append({
                'kind': 'Lunar',
                'subtype': _subtype(retflag, _LUNAR_SUBTYPE_BITS),
                'jd_max': tret[0],
                'jd_start': jd_s,
                'jd_end': jd_e,
            })
        jd = tret[0] + 1.0

    return eclipses


def get_eclipse_from_precomputed(
    d: date, precomputed: list[dict], location: Location
) -> EclipseInfo | None:
    """Look up whether day `d` has an eclipse from the precomputed list, then compute
    per-location visibility. Equivalent to get_eclipse_for_date() but avoids the global search."""
    geopos = [location.lon, location.lat, 0.0]
    jd_midnight = local_midnight_jd(d, location.timezone)
    jd_next_midnight = local_midnight_jd(d + timedelta(days=1), location.timezone)

    for result in precomputed:
        if not (jd_midnight <= result['jd_max'] < jd_next_midnight):
            continue
        # Recompute visibility for this location
        if result['kind'] == 'Solar':
            how_flag, _attr = swe.sol_eclipse_how(result['jd_max'], geopos, swe.FLG_SWIEPH)
            visible = how_flag != 0
        else:
            _how_flag, attr = swe.lun_eclipse_how(result['jd_max'], geopos, swe.FLG_SWIEPH)
            visible = attr[6] > 0

        if visible:
            sutak_hours = _SUTAK_HOURS[result['kind']]
            sutak_start = jd_to_utc(result['jd_start'] - sutak_hours / 24.0)
            sutak_end = jd_to_utc(result['jd_end'])
        else:
            sutak_start = None
            sutak_end = None

        return EclipseInfo(
            kind=result['kind'],
            subtype=result['subtype'],
            visible=visible,
            start=jd_to_utc(result['jd_start']),
            end=jd_to_utc(result['jd_end']),
            sutak_start=sutak_start,
            sutak_end=sutak_end,
        )
    return None
```

- [ ] **Step 4: Run the eclipse tests**

```bash
pytest tests/test_eclipses.py -v
```

Expected: all pass (including the new ones)

- [ ] **Step 5: Add `include_eclipse` parameter to all three engines**

In each of `telugu_panchangam/engines/drik.py`, `surya_siddhanta.py`, and `vakya.py`, find the `calculate` method signature and add the parameter:

```python
# Before (in each engine)
def calculate(self, d: date, location: Location) -> PanchangamDay:

# After
def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
```

Then find the line that calls `get_eclipse_for_date` inside each engine's `calculate` and wrap it:

```python
# Before
eclipse = get_eclipse_for_date(d, location)

# After
eclipse = get_eclipse_for_date(d, location) if include_eclipse else None
```

- [ ] **Step 6: Update `generate.py` to use the precomputed path**

Replace the generation loop in `generate_feeds`:

```python
# Add import at top of generate.py
from telugu_panchangam.eclipses import list_eclipses_in_range, get_eclipse_from_precomputed
from telugu_panchangam.engines.utils import local_midnight_jd

# Inside generate_feeds(), before the for-loop over systems, add:
jd_start = local_midnight_jd(start, 'UTC')
jd_end   = local_midnight_jd(end + timedelta(days=1), 'UTC')
print('  Pre-computing eclipses for the generation window...')
precomputed_eclipses = list_eclipses_in_range(jd_start, jd_end)
print(f'  Found {len(precomputed_eclipses)} eclipse(s).')

# Then inside the inner "for location in locations" loop, change:
#   days.append(engine.calculate(d, location))
# to:
days = []
d = start
while d <= end:
    day = engine.calculate(d, location, include_eclipse=False)
    day.eclipse = get_eclipse_from_precomputed(d, precomputed_eclipses, location)
    days.append(day)
    d += timedelta(days=1)
```

- [ ] **Step 7: Run full test suite**

```bash
pytest tests/ -q
```

Expected: all pass. The MCP tools are unchanged (they still call `get_eclipse_for_date` directly with `include_eclipse=True` default).

- [ ] **Step 8: Spot-check generation speed**

```bash
time python -m telugu_panchangam.generate
```

Compare runtime before and after. You should see a meaningful reduction (rough expectation: 30–60% faster overall generation for a full 18-month window due to eliminating redundant eclipse searches).

- [ ] **Step 9: Commit**

```bash
git add telugu_panchangam/eclipses.py \
        telugu_panchangam/engines/drik.py \
        telugu_panchangam/engines/surya_siddhanta.py \
        telugu_panchangam/engines/vakya.py \
        telugu_panchangam/generate.py \
        tests/test_eclipses.py
git commit -m "perf: precompute eclipses once per generation run instead of per-day per-feed"
```

---

## Execution order

Tasks 1–6 are fully independent. Task 7 touches the engines — do it last to avoid conflicts if running sequentially.

Suggested order for fastest feedback: 1 → 2 → 3 → 4 → 6 → 5 → 7
