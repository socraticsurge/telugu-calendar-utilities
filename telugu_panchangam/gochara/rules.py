# Gochara: transit verdicts from the janma rasi, per the classical
# Brihat Samhita scheme. Each graha gives good results only in certain
# houses counted from the natal Moon sign; a favourable transit is
# obstructed (vedha) when another graha occupies its vedha point —
# except between Surya and Shani, and between Chandra and Budha
# (the father-son exemptions). Rahu and Ketu follow the Shani house
# convention and neither cause nor receive vedha.
from telugu_panchangam.engines.base import RASHI_NAMES

GOCHARA_FAVOURABLE: dict[str, frozenset[int]] = {
    'Surya':   frozenset({3, 6, 10, 11}),
    'Chandra': frozenset({1, 3, 6, 7, 10, 11}),
    'Kuja':    frozenset({3, 6, 11}),
    'Budha':   frozenset({2, 4, 6, 8, 10, 11}),
    'Guru':    frozenset({2, 5, 7, 9, 11}),
    'Shukra':  frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
    'Shani':   frozenset({3, 6, 11}),
    'Rahu':    frozenset({3, 6, 11}),
    'Ketu':    frozenset({3, 6, 11}),
}

# favourable house -> house whose occupant obstructs it (Brihat Samhita)
VEDHA: dict[str, dict[int, int]] = {
    'Surya':   {3: 9, 6: 12, 10: 4, 11: 5},
    'Chandra': {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    'Kuja':    {3: 12, 6: 9, 11: 5},
    'Budha':   {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    'Guru':    {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    'Shukra':  {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    'Shani':   {3: 12, 6: 9, 11: 5},
}

_VEDHA_EXEMPT = {('Surya', 'Shani'), ('Shani', 'Surya'),
                 ('Chandra', 'Budha'), ('Budha', 'Chandra')}

_NODES = {'Rahu', 'Ketu'}


def _house_from(janma_rasi: str, rasi: str) -> int:
    return (RASHI_NAMES.index(rasi) - RASHI_NAMES.index(janma_rasi)) % 12 + 1


def gochara_for(janma_rasi: str, sky: dict[str, str]) -> list[dict]:
    """Per-graha gochara verdicts for a janma rasi.

    `sky` maps graha name -> current rasi name. Verdict is 'favourable',
    'blocked' (favourable house, but vedha) or 'adverse'.
    """
    if janma_rasi not in RASHI_NAMES:
        raise ValueError(f'Unknown rashi {janma_rasi!r} — expected one of {RASHI_NAMES}')
    occupants: dict[int, list[str]] = {}
    for g, rasi in sky.items():
        occupants.setdefault(_house_from(janma_rasi, rasi), []).append(g)

    out = []
    for graha, rasi in sky.items():
        pos = _house_from(janma_rasi, rasi)
        entry = {'graha': graha, 'rasi': rasi, 'position': pos,
                 'verdict': 'adverse', 'vedha_by': None}
        if pos in GOCHARA_FAVOURABLE[graha]:
            entry['verdict'] = 'favourable'
            if graha not in _NODES:
                vedha_house = VEDHA[graha].get(pos)
                for other in occupants.get(vedha_house, []):
                    if other == graha or other in _NODES:
                        continue
                    if (graha, other) in _VEDHA_EXEMPT:
                        continue
                    entry['verdict'] = 'blocked'
                    entry['vedha_by'] = other
                    break
        out.append(entry)
    return out


def named_conditions(janma_rasi: str, sky: dict[str, str]) -> list[str]:
    """Headline Shani conditions devotees know by name."""
    pos = _house_from(janma_rasi, sky['Shani'])
    conditions = []
    if pos == 12:
        conditions.append('Sade Sati (rising phase)')
    elif pos == 1:
        conditions.append('Sade Sati (peak phase)')
    elif pos == 2:
        conditions.append('Sade Sati (setting phase)')
    elif pos == 8:
        conditions.append('Ashtama Shani')
    elif pos == 4:
        conditions.append('Ardhastama Shani')
    return conditions
