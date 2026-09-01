# Security Policy

## Supported versions

| Component | Supported |
|-----------|-----------|
| `mcp-server-panchangam` on PyPI | latest release only |
| Published calendar feeds (`panchangam.astrochaganti.com`) | always current (regenerated monthly) |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Instead, email **cvk.atreya@gmail.com** with:

- A description of the issue and where it lives (PyPI package, MCP server tools, feed generation workflow, or the landing page)
- Steps to reproduce
- Impact as you understand it

You will get an acknowledgement within 72 hours. Once a fix ships, the issue can be disclosed publicly — credit is gladly given unless you prefer otherwise.

## Scope notes

- The published feeds and landing page are static files on GitHub Pages. The
  landing page can hold optional guest-profile data in the browser's
  origin-scoped `localStorage`. A calculated profile can contain a display name,
  exact birth date/time, selected place and coordinates, IANA timezone,
  Nakshatra, Padam, Janma Rashi, Lagna, D1 graha positions, and calculation
  provenance. This is sensitive user data even though it is not persisted by
  an application database.
- Birth-profile calculation uses two stateless operations hosted by the Astro
  Chaganti application. Place search sends only the submitted city/town query.
  Calculation sends date, time, coordinates, and IANA timezone through the
  gateway to an authenticated DashaFlow sidecar. The profile name is never part
  of either request. These routes must not create sessions, database rows, or
  application logs containing request bodies, and every response must use
  `Cache-Control: private, no-store`.
- Public browser builds keep those operations disabled unless
  `VITE_BIRTH_PROFILE_API_ENABLED` is the exact string `true`; the flag is not
  a secret or server authorization. Public pages route only to the canonical
  `https://astrochaganti.com/api/guest` gateway and reject loopback or arbitrary
  base overrides. The server-side routes must remain independently disabled
  until licensing and place-provider approval are recorded.
- Muhurtam election-chart projection has a separate public activation gate:
  `VITE_ELECTION_CHART_API_ENABLED` must be the exact string `true`. An absent
  flag permits only loopback development. Public requests use only the same
  canonical HTTPS guest gateway and contain candidate coordinates, timezone,
  and instants—never profile identity or birth data. This browser flag does
  not activate or authorize the gateway or DashaFlow sidecar.
- A browser can keep at most four guest profiles. People using the same browser
  profile on the same site origin can see, edit, delete, or clear them. Profiles
  do not follow the guest to another browser, device, domain, protocol, or port.
  Clearing site data removes them, private-browsing storage may disappear when
  the private session ends, and there is no account, cloud sync, or recovery.
- The profile-bearing page does not load third-party scripts, stylesheets, or
  font files. Its optional analytics hook accepts only fixed, content-free
  identifiers and is inert unless a trusted first-party integration is
  deliberately supplied.
  Profile names, birth details, profile IDs, and stored selections must never be sent to
  GoatCounter or any other analytics service. Built-in share text also omits
  profile names. Reports of profile content leaving either boundary are in
  scope.
- The MCP server runs locally on the user's machine and makes no network calls at runtime; its inputs are date/city strings validated at the tool layer. Input-validation bypasses there are still welcome reports.

## Past findings

**2024-06-14 — DOM XSS in static landing page (fixed)**

The landing page renders UI dynamically via client-side JS. User-controlled inputs
(birth star profile names, dates) were being concatenated into template literals and
assigned directly to `innerHTML`, enabling Self-XSS even though there is no
server-side persistence or query-parameter reflection.

Fix: a generic `htmlEsc()` helper (renamed from the narrower `muEsc`) is now applied
to all user-controlled values before DOM insertion. Ensure any future client-side
templating follows the same pattern — never concatenate untrusted input into
`innerHTML` without escaping.
