# Feature Proposal: Daily Lagna (Ascendant) Transitions & Hora Muhurta

## 1. Missing Highly Valuable Feature
Currently, the `telugu-calendar-utilities` platform provides extensive daily metadata (Tithi, Nakshatra, Yoga, Karana, Choghadiya, etc.). However, it lacks two tightly coupled, fundamental components for precise daily astrological timing:
- **Daily Lagna (Ascendant) Transitions:** The exact times when the Ascendant changes sign throughout the day.
- **Hora Muhurta:** The planetary hour division, which assigns specific times of day to planetary rulers.

Adding **Daily Lagna Transitions and Hora** is highly valuable because while Choghadiya offers generic temporal divisions, advanced Vedic customers and Jyotish practitioners rely heavily on the *Lagna* and *Hora* for setting precise Muhurtas (auspicious timings) for critical life events (marriages, property purchases, entering a new home, etc.).

## 2. Alignment with Traditional Scriptural Rules
According to classical Jyotisha texts (like *Brihat Parashara Hora Shastra* and *Muhurta Chintamani*):
- **Lagna (Udaya Lagna):** The rising sign at the eastern horizon determines the core auspiciousness of a moment. A structurally sound Lagna neutralizes numerous doshas (flaws) in the Panchangam. The transitions (Sandhis) between Lagnas are typically avoided (Lagna Gandanta).
- **Hora:** Each day is divided into 24 Horas (planetary hours), starting with the Hora of the weekday lord at sunrise. They follow a strict sequence (Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars). The nature of the action must align with the planetary ruler of the Hora.
- The calculations must be geocentric and location-specific, dependent on precise Sunrise times.

## 3. Justification for Computational Astrology Value
- **Differentiator:** Most standard digital Panchangams only give daily overarching parameters. Providing precise Lagna and Hora timings brings professional-grade Jyotisha tooling to the average user.
- **Enhanced Muhurta Engine:** This data can be consumed by the existing `telugu_panchangam/personal/muhurta.py` module to significantly refine the `find_muhurta` tool. Instead of just relying on Choghadiya and avoiding bad windows, it can prioritize specific Lagnas (e.g., fixed signs for laying foundations) or Horas.
- **Algorithmic Complexity:** Accurately calculating Lagna transitions using the Swiss Ephemeris (`pyswisseph`) demonstrates the high-end computational power of the system, leveraging existing infrastructure to output mathematically rigorous astrological data.

## 4. Step-by-Step Feature Execution Plan

### Task 1: Create the New Module (Respecting the Frozen Core)
**Goal:** Implement Lagna and Hora calculations in a new, separate package without modifying the `telugu_panchangam/engines/` internals.
*   **Requirement 1.1:** Create a new module `telugu_panchangam/personal/lagna_hora.py`.
*   **Requirement 1.2:** This module must consume standard engine outputs, specifically `PanchangamDay` (for sunrise/sunset times and the day's weekday).
*   **Requirement 1.3:** Implement a function `get_horas(day: PanchangamDay) -> list[Window]` that calculates the 24 planetary hours (12 daytime, 12 nighttime) strictly based on the provided `day.sunrise` and `day.sunset`.
*   **Requirement 1.4:** Implement a function `get_lagna_transitions(day: PanchangamDay) -> list[Window]` that independently uses `pyswisseph.houses` (or an equivalent non-invasive calculation based on the location in `PanchangamDay`) to find Ascendant sign boundaries.

### Task 2: Data Generation & MCP Exposure
**Goal:** Expose the new data in the MCP Server without touching the ICS Generator.
*   **Requirement 2.1:** Update `telugu_panchangam/mcp/server.py` and `telugu_panchangam/mcp/tools.py` to add new tools `get_daily_horas` and `get_lagna_transitions` that wrap the new module's outputs.
*   **Requirement 2.2:** (Crucial) Do **not** modify `telugu_panchangam/generators/ics.py` or the `PanchangamDay` base dataclass. The new data will be strictly supplementary/personal outputs.

### Task 3: Personalization & Muhurta Integration
**Goal:** Consume the new data in the personal muhurta logic.
*   **Requirement 3.1:** Update `telugu_panchangam/personal/muhurta.py` to import and call `get_horas` from the new module.
*   **Requirement 3.2:** Modify the scoring logic in `telugu_panchangam/personal/muhurta.py` to optionally boost slot scores if the slot aligns with a favorable Hora or Lagna.

### Task 4: Testing & Validation
**Goal:** Ensure mathematical accuracy and zero regressions.
*   **Requirement 4.1:** Write new tests in a new file `tests/test_lagna_hora.py` pinning Lagna transition times for specific dates and locations against verified outputs from drikpanchang.com.
*   **Requirement 4.2:** Run the full test suite (`python -m pytest tests/`) to guarantee no existing assertions are broken.
*   **Requirement 4.3:** Ensure MCP server output version is bumped in `pyproject.toml` since the MCP tools are being updated.

### Task 5: Documentation Updates
**Goal:** Update developer documentation while respecting read-only restrictions.
*   **Requirement 5.1:** Document the new tools and modules in `README.md`.
*   **Requirement 5.2:** (Crucial) Do **not** modify anything under `docs/`.
