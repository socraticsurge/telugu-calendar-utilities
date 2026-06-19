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

- The published feeds and landing page are static files on GitHub Pages; there is no server-side code or user data anywhere in this project.
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
