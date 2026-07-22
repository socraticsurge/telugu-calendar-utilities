# Reference Docs — Telugu Panchangam Utilities

> **Audience:** the maintainer (you). A deep, diagram-first map of everything
> the project computes, everything it exposes, and how it all fits together.
> **Status:** generated 2026-06-17 from a full read of the codebase at master
> (HEAD `045d828`, the jules-free rewrite). **Gitignored** — local only, per the
> project's docs convention.
>
> These complement — they do not replace — the on-GitHub docs:
> [`ARCHITECTURE.md`](../../ARCHITECTURE.md) (layer cake + engine boundary),
> [`MAINTENANCE_RUNBOOK.md`](../../MAINTENANCE_RUNBOOK.md) (release/cron/recipes),
> [`README.md`](../../README.md) / [`README_PYPI.md`](../../README_PYPI.md) (user-facing),
> and [`CHANGELOG.md`](../../CHANGELOG.md) (what shipped when).

## The one-paragraph mental model

A **Telugu panchangam (Hindu almanac) engine** computes the five *angas*
(Tithi, Nakshatra, Yoga, Karana, Vaaram) plus solar/lunar metadata, auspicious
and inauspicious windows, festivals, and eclipses for **any date, any city**,
under **three calculation systems** (Drik Ganita, Surya Siddhanta, Vakya). The
engine emits one canonical object — `PanchangamDay`. Everything else is a
**consumer** of that object: a muhurta (electional-timing) scorer, a Tarabalam /
Gochara / Rasi-Phalalu personal layer, a set of standalone jyotisha calendars
(combustion, planetary war, ingress, eclipse, panchanga-shuddhi), an ICS
calendar-feed generator (22 cities × 3 systems), and an MCP server exposing
**17 tools**. It ships to three surfaces: a landing page, webcal feeds, and a
PyPI MCP package.

## Doc map

| # | Doc | What's inside |
|---|-----|---------------|
| 00 | **this file** | Mental model, doc map, glossary |
| 01 | [System mindmap & architecture](01-system-mindmap.md) | The deep mindmap (engines → features → surfaces), layer-cake, class hierarchy |
| 02 | [Engines & the PanchangamDay model](02-engines-and-model.md) | The 3 engines, how they differ algorithmically, the full field reference |
| 03 | [Computational features](03-computational-features.md) | Every jyotisha computation, grouped, with classical source + output field |
| 04 | [User-facing features](04-user-facing-features.md) | The 17 MCP tools, the ICS feeds, the landing page — how each works |
| 05 | [Data flow & the muhurta pipeline](05-data-flow-and-muhurta.md) | End-to-end flow; the muhurta scorer in depth (the crown-jewel consumer) |
| 06 | [Roadmap & backlog](06-roadmap-and-backlog.md) | Shipped phases, paused/parked work, and one governance inconsistency to reconcile |
| 08 | [Provenance & authority](08-provenance-and-authority.md) | Evidence classes, source editions, claim-level citation status, and the verification ledger |
| 13 | [Bhumi Puja / foundation profile](13-bhumi-puja-foundation-profile.md) | Raman page-level crosswalk, conservative automation, and practitioner checks |
| 14 | [Well-digging source profile](14-well-digging-profile.md) | Raman's admitted Nakshatras/Lagnas, hard-rock caution, and manual chart checks |
| 15 | [Land-purchase source profile](15-land-purchase-profile.md) | Raman's building-land criteria, scope correction, and election-chart checks |
| 16 | [Muhurtam activity provenance coverage](16-activity-provenance-coverage.md) | Machine-checked verified-profile coverage and the remaining citation debt |
| 17 | [Namakarana source profile](17-namakarana-profile.md) | Raman Chapter VIII crosswalk, conservative gates, and practitioner checks |
| 18 | [Annaprasana source profile](18-annaprasana-profile.md) | Raman Chapter VIII and Panchanga-Suddhi crosswalk with explicit limitations |
| 19 | [Karnavedha source profile](19-karnavedha-profile.md) | Daytime-only Chapter VIII profile with exact weekday, Tithi and Lagna gates |
| 20 | [Mundana / Chaula source profile](20-mundana-profile.md) | Chapter VIII Paksha, combustion, forenoon and conservative Lagna contract |
| 21 | [Vidyarambha source profile](21-vidyarambha-profile.md) | Chapter VIII weekday, Nakshatra and movable/common-Lagna crosswalk |
| 22 | [Upanayana source profile](22-upanayana-profile.md) | Paksha-exact Tithis, Uttarayana signs, before-noon gate and chart caveats |
| 23 | [Vehicle-acquisition source profile](23-vehicle-acquisition-profile.md) | Precisely scoped Chapter IV movable-Nakshatra preference and non-inherited heuristics |
| 24 | [Roof-laying source profile](24-construction-roof-profile.md) | Chapter XII's stage-specific Vrishabha-or-Tula Lagna gate and explicit scope boundary |
| 25 | [Coronation source profile](25-coronation-profile.md) | Chapter XVI's incorporated head-of-state rules, exact gates, and chart-level alternatives |
| 26 | [Wood-cutting source profile](26-wood-cutting-profile.md) | Chapter XIII's last-quarter rule, dry-sign manual check, and separate Panchaka provenance |
| 27 | [Surgery source profile](27-surgery-profile.md) | Chapter XV's exact election, chart cautions, and non-negotiable clinical safety boundary |
| 28 | [Gold / jewelry source profile](28-gold-jewelry-profile.md) | Chapter X's limited chart instruction and explicit separation from project ranking heuristics |
| 29 | [Pilgrimage source profile](29-pilgrimage-profile.md) | Chapter XIV's incorporated journey rules, Guru conditions, and heuristic boundary |
| 30 | [Travel source profile](30-travel-profile.md) | Chapter XIV's hard exclusions, preferred stars, chart checks, and isolated Disha Shoola debt |
| 31 | [Wedding source profile](31-wedding-evidence-audit.md) | Complete Raman crosswalk, manual Pada/chart boundary and published-practice divergence |
| 32 | [Gochara source crosswalk](32-gochara-source-crosswalk.md) | Verified favourable houses and Vedha, a known Rahu/Ketu conflict, and a precisely bounded named-Shani evidence layer |
| 33 | [Gruhapravesha evidence audit](33-gruhapravesha-evidence-audit.md) | Exact Chapter XII crosswalk and approval-gated conflicts in the current home-entry profile |
| 34 | [Lawsuit-filing source profile](34-court-evidence-audit.md) | Exact Raman crosswalk, disclosed Tithi shorthand, conservative Mesha-Lagna automation and legal-safety boundary |
| 35 | [Litigation alias and Bhadra audit](35-litigation-evidence-audit.md) | Retired duplicate profile, explicit Court alias, exact Chintamani verses and isolated 5:8:3 approximation debt |
| 36 | [Mutual engagement evidence audit](36-engagement-evidence-audit.md) | Exact Kanyavarana/Varavarana Nakshatra intersection and manual boundary |
| 37 | [Cremation evidence audit](37-cremation-evidence-audit.md) | Muhurta Chintamani verse 48 and the whole-Dhanishtha precision conflict |
| 38 | [Homa offering evidence audit](38-yajna-homam-evidence-audit.md) | Exact Homahuti and Agnivasa election gates |
| 39 | [General purchase source profile](39-purchase-profile.md) | Buyer-side Kraya verse, marketplace checks, and object-specific boundaries |
| 40 | [Service-entry source profile](40-job-contract-evidence-audit.md) | Exact verse-26 gates, chart and employer/employee compatibility boundary |
| 41 | [Capital-deployment source profile](41-business-evidence-audit.md) | Exact verse-27 stars and Chara gate, chart prerequisites, commercial and legal boundary |
| 42 | [Shantika / Paushtika source profile](42-ceremony-evidence-audit.md) | Exact verse-34 gates, chart prerequisites, narrow rite scope and remedial exception |
| 43 | [Dharma-kriya commencement profile](43-beginning-evidence-audit.md) | Exact verse-30 gates, meritorious-work scope, Varga and personal Guru-bala boundary |
| 44 | [Activity provenance states](44-activity-provenance-states.md) | Enforced verified, contradicted and heuristic claim contract across Python, MCP and browser |
| 45 | [Muhurtam activity coverage roadmap](45-muhurta-activity-coverage-roadmap.md) | Source-backed gap inventory, priorities, safety boundaries, and one-feature-at-a-time expansion order |
| 46 | [Panchangam provenance disclosure](46-panchangam-provenance-disclosure.md) | Field-group evidence states in the MCP response and the exact remaining source debt |
| 47 | [Seemantha source profile](47-seemantha-profile.md) | Exact prenatal-rite crosswalk, conservative chart boundaries, and medical precedence |
| 48 | [Completed-house purchase source profile](48-completed-house-purchase-profile.md) | House-specific Chapter XII formula, independent buyer-rule comparison, and practical safeguards |
| 49 | [Home-repair source profile](49-home-repair-profile.md) | Repair-commencement weekday semantics, conditional chart checks, and construction-safety boundary |
| 50 | [Trade-inventory purchase profile](50-trade-inventory-purchase-profile.md) | Buyer-side inventory scope, exact preference semantics, and commercial safeguards |
| 51 | [Borrowing-money source profile](51-borrowing-money-profile.md) | Debtor-side Nakshatra gates, Chintamani divergence, and financial-safety boundary |
| 52 | [Lending-money source profile](52-lending-money-profile.md) | Creditor-side conditional gates, published-practice conflict, and financial safeguards |

## How to read the diagrams

Diagrams are [Mermaid](https://mermaid.js.org/) fenced code blocks. They render
natively on GitHub, in VS Code (with the *Markdown Preview Mermaid* extension),
in Obsidian, and in most modern markdown viewers. Where a diagram carries the
load, the same information is also given as prose or a table so the file is
useful as plain text too.

## Glossary (transliterated terms, as used in code & UI)

| Term | Meaning |
|------|---------|
| **Anga** | "Limb" — one of the five panchangam elements |
| **Tithi** | Lunar day (1–30); Moon−Sun elongation / 12° |
| **Nakshatra** | Lunar mansion (27); Moon's sidereal longitude / 13°20′ |
| **Yoga** | *Nitya* yoga (27); (Sun+Moon longitude) / 13°20′ |
| **Karana** | Half-tithi (60 total, 11 types); 2 per day |
| **Vaaram** | Weekday, anchored at sunrise |
| **Paksham** | Lunar fortnight — Shukla (waxing) / Krishna (waning) |
| **Maasam** | Lunar month (Chaitra … Phalguna); `Adhika`/`Nija` for intercalary |
| **Rituvu** | Tropical season (6) |
| **Samvatsara** | Year in the 60-year cycle |
| **Rasi / Rashi** | Zodiac sign (12) |
| **Lagna** | Ascendant — the rising sign on the eastern horizon |
| **Hora** | Planetary hour (24/day, weekday-lord sequence) |
| **Muhurta** | An auspicious time window / the art of electing one |
| **Choghadiya** | 8 weekday-keyed day/night blocks, auspicious or not |
| **Rahu Kalam / Gulika / Yamagandam** | Inauspicious 1/8-day windows |
| **Brahma / Abhijit Muhurta, Amrita Kalam** | Auspicious windows |
| **Varjyam / Durmuhurtham / Vishaghati** | Inauspicious sub-windows |
| **Tarabalam** | 9-fold star strength from a birth nakshatra |
| **Chandrabalam** | 12-fold Moon-sign strength from a birth rasi |
| **Gochara** | Planetary transit (and its verdicts from a natal sign) |
| **Maudhya / Asta-Udaya** | Combustion / heliacal setting & rising |
| **Graha Yuddha** | "Planetary war" — two planets within 1° |
| **Sankramana** | Sun's ingress into a new rasi |
| **Ayanamsa** | Sidereal–tropical offset (Lahiri default) |

## Classical sources cited across the codebase

The codebase draws on Muhurta Chintamani, Brihat Samhita, Brihat Parashara
Hora Shastra (BPHS), Dharmasindhu, Surya Siddhanta, B. V. Raman's *Muhurtha*,
and modern astronomical references. These sources do different jobs: a text
may establish a rule, while an ephemeris or published panchangam may verify a
computed time. They are not interchangeable. Exact editions, locators, and
the current verification state are recorded in
[Provenance & authority](08-provenance-and-authority.md); missing locators are
listed there as open evidence work rather than treated as verified.
