# Design

Captured from the live site (index.html tokens), July 2026. Identity-preserving: these are the committed brand values, not aspirations. The one-shell redesign keeps this visual language and changes structure, not voice.

## Theme

Light, warm, print-like. The feel of a well-made almanac page: cream paper ground, deep maroon ink for brand and emphasis, muted earth accents for meaning (green = auspicious, amber = caution, maroon = inauspicious/brand). No dark mode currently.

## Colors

| Token | Value | Role |
|---|---|---|
| `--brand` / `--indigo` | `#8E2A1F` | Deep maroon — brand, links, inauspicious markers, primary emphasis |
| `--indigo-bg` | `rgba(142,42,31,0.08)` | Maroon tint surfaces |
| `--indigo-border` | `rgba(142,42,31,0.22)` | Maroon tint borders |
| `--amber` | `#8F5C18` | Caution / neutral-special (Ekadashi, observances) — darkened from `#A56B1E` for AA on cream (4.81:1) |
| `--amber-bg` / `--amber-border` | `rgba(143,92,24,0.09/0.30)` | Amber tints |
| `--green` | `#4F6B2C` | Auspicious windows, favourable verdicts |
| `--green-bg` / `--green-border` | `rgba(79,107,44,0.09/0.30)` | Green tints |
| Ink | `#1F1A17` | Body text (14.6:1 on cream) |
| Muted ink | `#58504A` | Secondary text (6.7:1 on cream — passes AA; earlier worry was miscalibrated) |
| Hint | `#6B6357` | Labels, hints, help chrome — darkened from `#8B8377` (3.18 → 5.03 on cream) |
| Faint | `#746B5E` | Footer, source lines — darkened from `#B5AC9C` (1.91 → 4.45 on cream) |
| Ground | `#F2ECDF` | Page background (warm cream) |

Semantic tone triple (green/amber/maroon) carries jyotisha meaning — auspicious/mixed/avoid — and must stay consistent everywhere times are shown.

## Typography

- **Display**: `Libre Baskerville`, `Fraunces`, Georgia, serif — brand name, panel headings, the shloka. Italic for devotional/Sanskrit voice.
- **Body/UI**: `Inter`, system-ui, sans-serif — everything functional.
- Pairing is serif-display over sans-body; keep this contrast axis.
- Body line-height 1.6; content column max-width 760px.
- Transliterated terms (Tithi, Varjyam, Choghadiya) set in body face, not italicized.

## Layout

- Single centered content column, `max-width: 760px` (already the committed rhythm).
- One shell: persistent left sidebar nav on wide screens; the same nav collapses to a drawer behind a hamburger below the breakpoint. No parallel mobile shell.
- Cards for day-data groupings (at-a-glance anga grid, window lists); avoid nested cards.
- At-a-glance grids reflow via `repeat(auto-fit, minmax(...))`, not breakpoint forks.

## Components (target vocabulary for the one-shell refactor)

`AppShell` · `SideNav` (drawer-capable) · `SelectionStore`-backed `CitySystemPicker` · `DayHeaderCard` · `AngaGrid` · `WindowList` (tone: auspicious/inauspicious) · `ChoghadiyaStrip` · `RasiChart` · `SlotResults` + `TierBadge` · `ShareButton` (per-panel payload) · `HelpPopover` · `SkeletonCard`

## Motion

Minimal and calm: smooth scroll, no entrance theatrics. Any added motion must be `prefers-reduced-motion` safe and serve comprehension (e.g., drawer slide). No bounce, no parallax.

## Known debts (do not copy into new work)

- Hero `em` uses gradient `background-clip: text` — legacy (the hero is currently
  hidden at every width post-one-shell; markup removal is pending cleanup).

## Resolved (2026-07-18 Phase 4 polish)

- Sub-AA grays darkened site-wide (see Colors); amber deepened for small-chip AA.
- Sidebar active state is a tinted pill (bg + 1px border, radius), not a left-stripe.
- Drawer + help sheet get `role="dialog"`/`aria-modal` + focus trap while open.
- `<main>` landmark + skip-to-content link.
- Settings recede behind a one-line summary ("All times in <city> local
  time · <system> · <fmt>h" + Change chip); pickers expand on demand.
  City/system persist in localStorage — set once, forget.
