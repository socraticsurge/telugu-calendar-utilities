# Landing Page Redesign — Design Spec

**Date:** 2026-06-10
**Status:** approved

---

## Overview

Redesign `docs/index.html` (the GitHub Pages landing page at
https://socraticsurge.github.io/telugu-calendar-utilities/) for better aesthetics, organization,
and interactivity. The page is a static HTML file with inline CSS/JS — no build step, no
framework — and is copied as-is to `public/index.html` by `scripts/build_landing_page.py` during
the monthly feed-generation workflow. This redesign keeps that constraint: everything ships in a
single self-contained HTML file.

---

## Goals

- Visual refresh: light, "Bright & Colorful" theme — indigo as the primary accent, with each
  calculation system getting a consistent color (Drik Ganita = indigo, Surya Siddhanta = amber,
  Vakya = green) used throughout the page.
- Add a live "Today's Panchangam" preview so visitors see real value before subscribing.
- Expand the calculation-system guidance into a proper explainer: who uses Drik Ganita vs. Surya
  Siddhanta vs. Vakya, and why — with credible external references.
- More polish/interactivity (subtle animation, organized tables) without adding a build step or
  external dependencies.

## Non-Goals

- No new backend/API — the live preview is built entirely from the existing `.ics` feed files,
  fetched and parsed client-side.
- No JS framework or bundler — vanilla JS, inline in `index.html`, as today.
- No new generated data files — Task in [2026-06-10-mcp-server.md](2026-06-10-mcp-server.md) /
  the feed generator are unchanged.

---

## Page Structure

Three stacked cards below the hero, in this order:

1. **🔆 Today's Panchangam** — live preview
2. **📅 Subscribe to your calendar** — picker + subscription URL + per-app instructions
3. **🧭 Choosing a calculation system** — expanded guidance with references

The previous "What's in each day's event" section is removed — its content is now demonstrated
live by the "Today's Panchangam" card and explained inline via the table's grouped row headers
(Sky / Auspicious / Inauspicious), so a separate explanatory section is redundant.

---

## Hero

- Title "Telugu Panchangam" + tagline, centered.
- A small sun emoji (`🌅`) with a slow CSS `bob` keyframe animation (translateY loop, ~3s) for a
  touch of life — purely decorative, no JS.

---

## Card 1: Today's Panchangam (live preview)

**Controls:** independent City and System `<select>` dropdowns, defaulting to **Hyderabad** /
**Drik Ganita**. Independent from Card 2's controls — a user can explore the preview for several
city/system combinations before deciding what to subscribe to.

**Preview rendering:**
- Header bar (indigo background): the date being shown (today, in the browser's local date) and
  the Samvatsara / Maasam / Paksham line.
- A table of label/value rows, grouped with small section headers:
  - (ungrouped) Tithi, Nakshatra, Yoga, Karana — each with start/end times where available
  - **Sky** — Sunrise/Sunset, Moonrise/Moonset
  - **🟢 Auspicious** — Brahma Muhurta, Abhijit Muhurta (if present), Amrita Kalam
  - **🔴 Inauspicious** — Rahu Kalam, Yamagandam, Gulika Kalam
- If today is a special day (Ekadashi, Amavasya, Pournami, Pradosham, Sankranti — derivable from
  the `⚡` marker in the feed's `SUMMARY`), show a small badge in the header bar.
- Helper text below: "Defaults to Hyderabad · Drik Ganita — try other cities and systems before
  you subscribe below."

**Data source & parsing (client-side):**
- On page load and on dropdown change, `fetch()` the relevant feed:
  `./feeds/{city-slug}-{system-slug}.ics` (same-origin relative path — works both at the repo root
  during local preview and at the deployed GitHub Pages root).
- Parse the ICS text:
  1. Unfold lines per RFC 5545 (a line starting with a single space is a continuation of the
     previous line — strip the leading space and concatenate).
  2. Find the `VEVENT` block whose `DTSTART;VALUE=DATE` equals today's date in `YYYYMMDD` format
     (browser's local date — acceptable approximation; the feed is generated per-city but the
     calendar day boundary mismatch only matters very close to midnight).
  3. From that event's `DESCRIPTION` (with `\n` escapes converted to real newlines), extract
     fields with line-prefix matching, e.g. lines starting with `Samvatsara:`, `Sunrise:`,
     `Tithi:`, `Brahma Muhurta`, `Rahu Kalam`, etc. The description format is stable (produced by
     `ICSGenerator`), so straightforward prefix/regex matching per known label is reliable.
  4. From `SUMMARY`, detect the `⚡` special-day marker.
- If fetch/parsing fails (e.g. offline, feed not yet generated for a brand-new city), show a small
  inline message in the preview card ("Preview unavailable — try the subscription link below")
  rather than breaking the page.

---

## Card 2: Subscribe to your calendar

- Independent City and System `<select>` dropdowns (same option lists as Card 1, separate
  state), defaulting to Hyderabad / Drik Ganita.
- **Step 1 — subscription URL**: monospace box showing the `webcal://` URL for the selected
  city/system, plus a "Copy URL" button (existing copy-to-clipboard behavior, kept).
- **Step 2 — add to your calendar**: tabbed instructions for Google Calendar / Apple Calendar /
  Outlook, each with a numbered step list (more detailed than the current single bullet per app).
  Tabs are simple show/hide via JS, default to "Google".
- Footer note: "Updated automatically on the 1st of every month, 18 months ahead. No account
  needed."

---

## Card 3: Choosing a calculation system

Intro paragraph: panchangams aren't one-size-fits-all; different traditions can disagree on
Tithi/Nakshatra/muhurtam timing by minutes to a full day (e.g. for Ekadashi).

Three color-coded cards, stacked, **all visible by default** (not tabs — better for SEO/crawling
and side-by-side comparison):

- **☀️ Drik Ganita — Modern Observational Astronomy** (indigo)
  Always-visible paragraph: Swiss Ephemeris + Lahiri ayanamsa, most accurate for sky events,
  default in most modern apps.
  "Read more" expand (inline accordion, no navigation): additional context + references.

- **🛕 Surya Siddhanta — The Classical Temple Standard** (amber)
  Always-visible paragraph: classical mean-motion system, used by TTD and most South Indian
  temples for ritual timing.
  "Read more" expand: longer history/context — why institutions retain it despite small
  divergence from observational positions, and that divergence can occasionally shift a
  tithi-based festival by a day. References:
  - Wikipedia — Surya Siddhanta
  - Tirumala Tirupati Devasthanams (official panchangam reference)

- **📜 Vakya — Traditional Printed Panchangam** (green)
  Always-visible paragraph: Surya Siddhanta + pre-computed correction tables ("Vakyas"), basis for
  most printed Telugu/Tamil panchangams.
  "Read more" expand: additional context + references. References:
  - Wikipedia — Vakya Panchangam / Pancanga
  - A popular panchangam reference site (e.g. drikpanchang.com) explaining traditional vs. drik
    systems

Each "Read more" toggles a `<div class="expanded">` via a small inline JS function — same pattern
for all three, parameterized by element id.

Closing tip line: "Not sure? Drik Ganita is a safe modern default. If your family or temple
follows a specific printed panchangam, match it to Surya Siddhanta or Vakya instead."

---

## Visual Design

- Palette: light background (`#f8fafc` page background, white cards), indigo primary (`#4338ca`
  / `#eef2ff`), with system-specific accents:
  - Drik Ganita → indigo (`#4338ca` / `#eef2ff` / `#c7d2fe`)
  - Surya Siddhanta → amber (`#92400e` / `#fffbeb` / `#fde68a`)
  - Vakya → green (`#166534` / `#f0fdf4` / `#bbf7d0`)
- Cards: white background, `1px solid #e2e8f0` border, `14px` border-radius, subtle box-shadow.
- Typography: system font stack (unchanged), section headers (`h2`) with a leading emoji.
- The hero sun emoji uses a `bob` keyframe animation (translateY, infinite, ease-in-out, ~3s).
- Mobile: cards remain single-column (already the natural flow); dropdown rows wrap via flexbox.

---

## Implementation Notes

- Single file: `docs/index.html`. All CSS in a `<style>` block, all JS in a `<script>` block at
  the end, as today.
- Reuse existing city list, slug function, and webcal URL construction from the current
  `index.html` script.
- New JS additions:
  - ICS fetch + parse + render function for Card 1, triggered on load and on Card 1's
    dropdown changes.
  - Tab switching for Card 2's per-app instructions.
  - Accordion toggle for Card 3's "Read more" sections.
- No changes to `telugu_panchangam/`, feed generation, or `scripts/build_landing_page.py` —
  this is a frontend-only change to `docs/index.html`.

---

## Testing / Verification

- No Python test changes needed (no backend changes).
- Manual verification: serve `docs/` locally (e.g. `python -m http.server` from repo root, or
  from `docs/` with feeds copied/symlinked alongside) and check in a browser:
  - Today's Panchangam preview loads and updates on dropdown change, for at least one city per
    calculation system.
  - Subscription URL and copy button work for several city/system combinations.
  - Tab switching and "Read more" accordions work.
  - Page renders correctly on a narrow (mobile) viewport.
