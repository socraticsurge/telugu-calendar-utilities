"""Panchanga Shuddhi — five-limb purity assessment for muhurta.

Panchanga Shuddhi evaluates whether each of the five Panchangam limbs
(Tithi, Vaara, Nakshatra, Yoga, Karana) is "shuddha" (pure/auspicious)
for general muhurta purposes. The count of pure limbs (0–5) gives the
overall quality:

  5 — Sarva Shuddha   (all five pure — excellent)
  4 — Chatushka Shuddha
  3 — Tri Shuddha
  2 — Dvi Shuddha
  1 — Eka Shuddha
  0 — Sarva Ashuddha  (avoid)

Classical rules used
--------------------
Tithi   : Rikta tithis (4th, 9th, 14th of either paksha) are ashuddha.
Vaara   : Monday, Wednesday, Thursday, Friday are shuddha; Sun, Tue, Sat
          are ashuddha for gentle/auspicious activities.
Nakshatra: Laghu, Mridu, Dhruva, and Chara nakshatras are shuddha; Tikshna
          (fierce) and Ugra (cruel) are ashuddha; Krittika and Vishakha
          (Mishra) are mixed.
Yoga    : 17 Nitya auspicious yogas are shuddha; Vyatipata and Vaidhriti
          (hard-avoid) are ashuddha; partial-avoid yogas (Vishkambha, Atiganda,
          Shoola, Ganda, Vyaghata, Parigha) are mixed.
Karana  : Vishti (Bhadra) and the four fixed karanas (Shakuni, Chatushpada,
          Naga, Kimstughna) are ashuddha; all other movable karanas are shuddha.

Assessment is done at the sunrise values of the panchangam day. For slot-level
Shuddhi (e.g. the exact muhurta time), use ``find_muhurta`` which applies
these rules inside the full scoring pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from telugu_panchangam.models.panchangam_day import PanchangamDay
from telugu_panchangam.personal.nitya_yoga import (
    NITYA_AUSPICIOUS,
    NITYA_HARD_AVOID,
    NITYA_PARTIAL_DOSHA_WINDOW,
)
from telugu_panchangam.personal.tithi_class import is_rikta

# ── Nakshatra quality table ───────────────────────────────────────────────────

_NAK_LAGHU = frozenset({
    'Ashvini', 'Hasta', 'Pushya',
})
_NAK_MRIDU = frozenset({
    'Mrigashira', 'Chitra', 'Anuradha', 'Revati',
})
_NAK_DHRUVA = frozenset({
    'Rohini', 'Uttara Phalguni', 'Uttara Ashadha', 'Uttara Bhadrapada',
})
_NAK_CHARA = frozenset({
    'Punarvasu', 'Swati', 'Shravana', 'Dhanishtha', 'Shatabhisha',
})
_NAK_SHUDDHA = _NAK_LAGHU | _NAK_MRIDU | _NAK_DHRUVA | _NAK_CHARA

_NAK_TIKSHNA = frozenset({'Ardra', 'Ashlesha', 'Jyeshtha', 'Mula'})
_NAK_UGRA    = frozenset({
    'Bharani', 'Magha', 'Purva Phalguni', 'Purva Ashadha', 'Purva Bhadrapada',
})
_NAK_ASHUDDHA = _NAK_TIKSHNA | _NAK_UGRA

_NAK_MISHRA = frozenset({'Krittika', 'Vishakha'})   # mixed — treated as neutral

_NAK_QUALITY: dict[str, str] = {}
for _n in _NAK_SHUDDHA:  _NAK_QUALITY[_n] = 'shuddha'
for _n in _NAK_ASHUDDHA: _NAK_QUALITY[_n] = 'ashuddha'
for _n in _NAK_MISHRA:   _NAK_QUALITY[_n] = 'mixed'

_NAK_CATEGORY: dict[str, str] = {}
for _n in _NAK_LAGHU:    _NAK_CATEGORY[_n] = 'Laghu (light)'
for _n in _NAK_MRIDU:    _NAK_CATEGORY[_n] = 'Mridu (soft)'
for _n in _NAK_DHRUVA:   _NAK_CATEGORY[_n] = 'Dhruva (fixed)'
for _n in _NAK_CHARA:    _NAK_CATEGORY[_n] = 'Chara (movable)'
for _n in _NAK_TIKSHNA:  _NAK_CATEGORY[_n] = 'Tikshna (sharp)'
for _n in _NAK_UGRA:     _NAK_CATEGORY[_n] = 'Ugra (fierce)'
for _n in _NAK_MISHRA:   _NAK_CATEGORY[_n] = 'Mishra (mixed)'

# ── Weekday quality ───────────────────────────────────────────────────────────

_VARA_SHUDDHA = frozenset({
    'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
})
_VARA_ASHUDDHA = frozenset({'Adivaram', 'Mangalavaram', 'Shanivaram'})

# ── Karana quality ────────────────────────────────────────────────────────────

_KARANA_ASHUDDHA = frozenset({
    'Vishti',        # Bhadra — universally inauspicious
    'Shakuni',       # fixed karana
    'Chatushpada',   # fixed karana
    'Naga',          # fixed karana
    'Kimstughna',    # fixed karana
})

# ── Verdict labels ────────────────────────────────────────────────────────────

_VERDICTS = [
    'Sarva Ashuddha',     # 0
    'Eka Shuddha',        # 1
    'Dvi Shuddha',        # 2
    'Tri Shuddha',        # 3
    'Chatushka Shuddha',  # 4
    'Sarva Shuddha',      # 5
]


# ── Output types ──────────────────────────────────────────────────────────────

@dataclass
class LimbAssessment:
    limb: str       # 'Tithi' | 'Vaara' | 'Nakshatra' | 'Yoga' | 'Karana'
    value: str      # e.g. 'Shukla Dvitiya', 'Guruvaram', 'Rohini', 'Siddhi', 'Bava'
    quality: str    # 'shuddha' | 'ashuddha' | 'mixed'
    shuddha: bool   # True iff quality == 'shuddha'
    reason: str     # one-line explanation


@dataclass
class PanchangaShuddhi:
    date: date
    shuddha_count: int                    # 0–5 pure limbs
    verdict: str                          # e.g. 'Sarva Shuddha'
    limbs: list[LimbAssessment] = field(default_factory=list)


# ── Limb assessors ────────────────────────────────────────────────────────────

def _assess_tithi(day: PanchangamDay) -> LimbAssessment:
    name = day.tithi.name
    if is_rikta(name):
        return LimbAssessment(
            limb='Tithi', value=name,
            quality='ashuddha', shuddha=False,
            reason='Rikta tithi (4th, 9th, or 14th) — depleting, universally avoided',
        )
    return LimbAssessment(
        limb='Tithi', value=name,
        quality='shuddha', shuddha=True,
        reason='Not a Rikta tithi',
    )


def _assess_vaara(day: PanchangamDay) -> LimbAssessment:
    vara = day.vaaram
    if vara in _VARA_SHUDDHA:
        return LimbAssessment(
            limb='Vaara', value=vara,
            quality='shuddha', shuddha=True,
            reason='Auspicious weekday (Soma/Budha/Guru/Shukra)',
        )
    if vara in _VARA_ASHUDDHA:
        return LimbAssessment(
            limb='Vaara', value=vara,
            quality='ashuddha', shuddha=False,
            reason='Inauspicious weekday for gentle/auspicious activities (Ravi/Kuja/Shani)',
        )
    return LimbAssessment(
        limb='Vaara', value=vara,
        quality='mixed', shuddha=False,
        reason=f'{vara} — unrecognized weekday; consult a Jyotishi',
    )


def _assess_nakshatra(day: PanchangamDay) -> LimbAssessment:
    nak = day.nakshatra.name
    quality = _NAK_QUALITY.get(nak, 'mixed')
    category = _NAK_CATEGORY.get(nak, 'Unknown')
    shuddha = quality == 'shuddha'
    if quality == 'shuddha':
        reason = f'{category} — auspicious for most activities'
    elif quality == 'ashuddha':
        reason = f'{category} — avoided for auspicious works'
    else:
        reason = f'{category} — dual nature; suitable for some activities'
    return LimbAssessment(
        limb='Nakshatra', value=nak,
        quality=quality, shuddha=shuddha,
        reason=reason,
    )


def _assess_yoga(day: PanchangamDay) -> LimbAssessment:
    yoga = day.yoga.name
    if yoga in NITYA_HARD_AVOID:
        return LimbAssessment(
            limb='Yoga', value=yoga,
            quality='ashuddha', shuddha=False,
            reason=f'{yoga} — hard-avoid; strongly inauspicious for all works',
        )
    if yoga in NITYA_PARTIAL_DOSHA_WINDOW:
        mins = int(NITYA_PARTIAL_DOSHA_WINDOW[yoga].total_seconds() / 60)
        return LimbAssessment(
            limb='Yoga', value=yoga,
            quality='mixed', shuddha=False,
            reason=f'{yoga} — dosha during first {mins} min; avoid that window',
        )
    if yoga in NITYA_AUSPICIOUS:
        return LimbAssessment(
            limb='Yoga', value=yoga,
            quality='shuddha', shuddha=True,
            reason=f'{yoga} — auspicious Nitya yoga',
        )
    return LimbAssessment(
        limb='Yoga', value=yoga,
        quality='mixed', shuddha=False,
        reason=f'{yoga} — neutral yoga (neither auspicious nor hard-avoid)',
    )


def _assess_karana(day: PanchangamDay) -> LimbAssessment:
    # Use the karana active at sunrise (first in the list)
    karana = day.karana[0].name if day.karana else 'Unknown'
    if karana in _KARANA_ASHUDDHA:
        reason = (
            'Vishti (Bhadra) — universally inauspicious; hard-avoid Mukha window'
            if karana == 'Vishti'
            else f'{karana} — fixed (immovable) karana; avoided for auspicious works'
        )
        return LimbAssessment(
            limb='Karana', value=karana,
            quality='ashuddha', shuddha=False,
            reason=reason,
        )
    return LimbAssessment(
        limb='Karana', value=karana,
        quality='shuddha', shuddha=True,
        reason=f'{karana} — movable karana; auspicious',
    )


# ── Public API ────────────────────────────────────────────────────────────────

def assess_shuddhi(day: PanchangamDay) -> PanchangaShuddhi:
    """Assess Panchanga Shuddhi for a computed PanchangamDay.

    Values are taken at sunrise (the canonical Panchangam snapshot).

    Parameters
    ----------
    day : PanchangamDay
        A fully-computed day from any engine.

    Returns
    -------
    PanchangaShuddhi with per-limb breakdown and overall verdict.
    """
    limbs = [
        _assess_tithi(day),
        _assess_vaara(day),
        _assess_nakshatra(day),
        _assess_yoga(day),
        _assess_karana(day),
    ]
    count = sum(1 for lb in limbs if lb.shuddha)
    return PanchangaShuddhi(
        date=day.date,
        shuddha_count=count,
        verdict=_VERDICTS[count],
        limbs=limbs,
    )
