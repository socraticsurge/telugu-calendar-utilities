# Feature Proposal: Panchaka Rahita Muhurta

## 1. Missing Highly Valuable Feature
Currently, the `telugu-calendar-utilities` platform provides extensive daily metadata and evaluates Muhurta slots using parameters such as Choghadiya, Tithi, Tarabalam, Chandrabalam, Lagna, and Hora. However, it lacks a critical classical filter for verifying auspicious timings: **Panchaka Rahita** (or Panchaka Dosha evaluation).

Panchaka refers to the summation of five astrological variables: Tithi, Vaaram (Weekday), Nakshatra, Lagna, and sometimes Ayana/Maasa depending on the specific tradition, divided by 9. The remainder of this division determines the presence of one of five specific doshas (flaws) or indicates a dosha-free (Rahita) state. Adding **Panchaka Rahita** evaluation is highly valuable because traditional Vedic customers consider a Muhurta incomplete or fundamentally flawed if it falls within a negative Panchaka, regardless of how favorable the Tarabalam or Choghadiya might be.

## 2. Alignment with Traditional Scriptural Rules
According to classical Jyotisha texts (like *Muhurta Chintamani* and *Kala Prakashika*):
- **Panchaka Calculation:** The number of the Tithi (1-30), Vaaram (Sunday=1 to Saturday=7), Nakshatra (Ashvini=1 to Revati=27), and Lagna (Mesha=1 to Meena=12) at the time of the Muhurta are added together.
- **Dosha Evaluation:** The sum is divided by 9. The remainder determines the Panchaka:
  - 1: Mrityu Panchaka (Danger, avoided for all auspicious acts)
  - 2: Agni Panchaka (Fire hazard, avoided for house construction/entry)
  - 4: Raja Panchaka (Trouble from authority, avoided for joining a job)
  - 6: Chora Panchaka (Theft, avoided for travel)
  - 8: Roga Panchaka (Disease, avoided for medical treatments)
  - 3, 5, 7, 0: Panchaka Rahita (Auspicious/Flawless)
- The calculations strictly require precise Lagna transitions (which are now available) and Nakshatra/Tithi values at the exact moment of the slot.

## 3. Justification for Computational Astrology Value
- **Differentiator:** While many apps offer basic "good/bad time" windows, very few compute real-time Panchaka because it requires crossing Lagna boundaries with Tithi and Nakshatra positions. Providing Panchaka Rahita brings an elite layer of scriptural rigor to the platform.
- **Enhanced Muhurta Engine:** This feature seamlessly integrates into the existing `telugu_panchangam/personal/muhurta.py` module. It can act as a hard filter (excluding slots with Mrityu Panchaka) or a soft penalty (downgrading a slot if the specific dosha conflicts with the activity, e.g., Agni Panchaka for Gruhapravesha).
- **Algorithmic Leverage:** It leverages the recently built `lagna_hora` module and the core `pyswisseph` engine to perform a dynamic, cross-variable calculation at any given timestamp, showcasing the power of the platform's astrological infrastructure.

## 4. Step-by-Step Feature Execution Plan

### Task 1: Create the Panchaka Module (Respecting the Frozen Core)
**Goal:** Implement Panchaka calculations in a new module without modifying the `telugu_panchangam/engines/` internals.
*   **Requirement 1.1:** Create a new file `telugu_panchangam/personal/panchaka.py`.
*   **Requirement 1.2:** Implement a function `get_panchaka_remainder(tithi_num: int, vaaram_num: int, nakshatra_num: int, lagna_num: int) -> int` that returns the remainder of the sum divided by 9.
*   **Requirement 1.3:** Implement a function `evaluate_panchaka(tithi_name: str, vaaram_name: str, nakshatra_name: str, lagna_name: str) -> dict` that translates the names to their respective indices (1-indexed), computes the remainder, and returns the dosha name and whether it is auspicious.
*   **Requirement 1.4:** Define the specific doshas and their activity-specific avoidances (e.g., Agni -> avoiding property acts) as constants within the module.

### Task 2: Muhurta Integration
**Goal:** Consume the Panchaka evaluation in the personal muhurta logic.
*   **Requirement 2.1:** Update `telugu_panchangam/personal/muhurta.py` to import `evaluate_panchaka`.
*   **Requirement 2.2:** Modify the `_evaluate_slot` function. For each slot, calculate the exact Tithi, Nakshatra, and Lagna at the slot's start time.
*   **Requirement 2.3:** Add logic to penalize or reject slots based on the Panchaka dosha. Specifically:
    *   Mrityu Panchaka (1) should act as a hard day/slot dosha, capping the tier (similar to Rikta Tithi).
    *   Activity-specific conflicts (e.g., Agni Panchaka for 'ceremony' or 'purchase') should apply a negative score penalty (-1 or -2) and add a reason to the `slot_quality` or `day_quality` group.

### Task 3: MCP Exposure
**Goal:** Expose the Panchaka status in the Muhurta tools.
*   **Requirement 3.1:** Ensure that the output of `tool_find_muhurta` in `telugu_panchangam/mcp/tools.py` includes the Panchaka status in the `reasons` list for each slot.
*   **Requirement 3.2:** Do **not** modify `telugu_panchangam/generators/ics.py` or the `PanchangamDay` base dataclass. The Panchaka evaluation is purely for the Muhurta generation pathway.

### Task 4: Testing & Validation
**Goal:** Ensure mathematical accuracy and zero regressions.
*   **Requirement 4.1:** Write new tests in a new file `tests/test_panchaka.py` to verify the mathematical correctness of `get_panchaka_remainder` and `evaluate_panchaka` against known classical examples.
*   **Requirement 4.2:** Update or add tests in `tests/test_muhurta_finder.py` to assert that Mrityu Panchaka correctly caps a slot's tier and that activity-specific doshas apply the correct penalties.
*   **Requirement 4.3:** Run the full test suite (`python -m pytest tests/`) to guarantee no existing assertions are broken.
*   **Requirement 4.4:** Ensure MCP server output version is bumped in `pyproject.toml` since the muhurta tool output is being refined.

### Task 5: Documentation Updates
**Goal:** Update developer documentation while respecting read-only restrictions.
*   **Requirement 5.1:** Document the inclusion of Panchaka Rahita evaluation in the `find_muhurta` tool description within `README.md`.
*   **Requirement 5.2:** (Crucial) Do **not** modify anything under `docs/`.
