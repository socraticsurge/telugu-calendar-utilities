# Product

## Register

product

## Users

Telugu-speaking devotees and their diaspora across 22 cities (Telugu heartland, Indian metros, US/UK/AU/AE). Two modes of use:

- **The daily glance** — morning check of tithi, nakshatra, Rahu Kalam, festival status before starting the day. Seconds, not minutes. Often arrives via a WhatsApp forward.
- **The occasional deep task** — hunting a muhurta window for a family event (wedding, gruhapravesham, travel, surgery), setting up a calendar subscription, reading gochara/rasi phalalu.

Traffic is ~2/3 desktop, 1/3 phone (GoatCounter, July 2026). The site is also the public face of the owner's astrology practice (Astro Chaganti), but the tool serves first.

## Product Purpose

The authoritative Telugu panchangam utility: three independent calculation systems (Drik, Surya Siddhanta, Vakya), every value engine-computed and pinned against drikpanchang.com in tests. Delivered as subscribable ICS feeds, a daily web toolkit, and an MCP server. Success looks like: habitual daily return visits, calendar subscriptions that quietly keep working for years, and WhatsApp shares that carry the site into family groups.

## Brand Personality

**Sacred, precise, calm.** A quiet instrument for daily ritual — accuracy presented with reverence, zero noise. The footer shloka is the voice: *satyam brūyāt priyam brūyāt* — be truthful, be kind.

## Anti-references

The owner's standard is stated positively: *"the simpler and the more elegant it is, and the more efficient the information architecture is — the more I will love it."* Its inversions are the anti-references:

- **The dual-shell compromise** — parallel desktop/mobile UIs that are each half-right (the failure mode that paused the last UI round).
- **Decoration that doesn't inform** — ornament, kitsch astrology styling, or brand flourish at the cost of glanceability.
- **Portal density** — the cramped table-of-everything layout of typical panchangam sites.

## Design Principles

1. **One shell, one truth.** A single layout system that adapts; never two parallel presentations of the same content.
2. **Information architecture earns its pixels.** Every element on screen answers a devotee's question. Density comes from hierarchy, not accumulation.
3. **Glanceable first, deep on demand.** The morning answers (tithi, nakshatra, windows to avoid) readable in three seconds; research tools one deliberate step away.
4. **Reverence through restraint.** Sacred and calm are achieved with space, the serif brand voice, and the muted maroon — never with cosmic imagery or mystical decoration.
5. **Times are the product.** Timing data is always primary, legible, and unambiguous — explicit city, explicit 12/24h, explicit next-day markers.

## Accessibility & Inclusion

WCAG AA is the target. The July 2026 accessibility pass corrected muted-text
contrast, added dialog semantics and focus management to the drawer/help sheet,
and added the `<main>` landmark and skip link. Reduced motion is respected
throughout. Transliterated Telugu terms (Tithi, Varjyam) are kept as-is per
project policy, with plain-English explanations available in context. New UI
work must preserve these contracts and pass the browser review gate.
