"""Simha-Stha Guru / Shukra — when Jupiter or Venus is in Simha rasi.

Classical wedding-muhurta restrictions:
- Simha-Stha Guru (12-year cycle): widely observed across regional
  traditions; particularly strong in south Indian custom.
- Simha-Stha Shukra: observed in some traditions; commonly treated as
  a penalty rather than a hard skip.
"""


def is_simha_stha(rasi_name: str | None) -> bool:
    """True iff the graha is in Simha rasi."""
    return rasi_name == 'Simha'
