"""Unit tests for the kendra/trikona/Ashtama classification helpers."""
import pytest

from telugu_panchangam.personal.lagna_position import (
    lagna_position, lagna_verdict, is_favourable_lagna, is_ashtama_lagna,
    LAGNA_KENDRA, LAGNA_TRIKONA,
    LAGNA_CHARA, LAGNA_STHIRA, LAGNA_DVISVABHAVA,
    lagna_class_of, lagnas_in_class,
)


def test_position_is_inclusive_count_from_janma():
    """Mesha→Mesha is 1, Mesha→Vrishabha is 2, ..., Mesha→Meena is 12."""
    assert lagna_position('Mesha', 'Mesha') == 1
    assert lagna_position('Mesha', 'Vrishabha') == 2
    assert lagna_position('Mesha', 'Karka') == 4       # kendra
    assert lagna_position('Mesha', 'Simha') == 5       # trikona
    assert lagna_position('Mesha', 'Tula') == 7        # kendra
    assert lagna_position('Mesha', 'Vrischika') == 8   # Ashtama
    assert lagna_position('Mesha', 'Makara') == 10     # kendra
    assert lagna_position('Mesha', 'Meena') == 12


def test_position_wraps_modulo_12():
    """Janma=Meena: Mesha is 2nd, Vrishabha is 3rd, ..., Meena is 1st."""
    assert lagna_position('Meena', 'Meena') == 1
    assert lagna_position('Meena', 'Mesha') == 2
    assert lagna_position('Meena', 'Tula') == 8        # Ashtama from Meena


def test_unknown_rashi_raises():
    with pytest.raises(ValueError):
        lagna_position('Mesha', 'NotARashi')
    with pytest.raises(ValueError):
        lagna_position('NotARashi', 'Mesha')


def test_kendra_trikona_classification():
    """Position 1 is in both kendra AND trikona (own rashi)."""
    assert LAGNA_KENDRA == {1, 4, 7, 10}
    assert LAGNA_TRIKONA == {1, 5, 9}
    assert 1 in LAGNA_KENDRA and 1 in LAGNA_TRIKONA


def test_verdict_labels_each_position():
    assert lagna_verdict(1) == 'own'
    assert lagna_verdict(4) == 'kendra'
    assert lagna_verdict(5) == 'trikona'
    assert lagna_verdict(7) == 'kendra'
    assert lagna_verdict(8) == 'ashtama'
    assert lagna_verdict(9) == 'trikona'
    assert lagna_verdict(10) == 'kendra'
    # Dusthana positions other than 8 are reported as neutral here —
    # we don't penalise them yet (could be a follow-up).
    assert lagna_verdict(6) == 'neutral'
    assert lagna_verdict(12) == 'neutral'


def test_is_favourable_lagna_covers_kendra_or_trikona():
    favourable = {1, 4, 5, 7, 9, 10}
    for p in range(1, 13):
        assert is_favourable_lagna(p) == (p in favourable), \
            f'pos {p}: expected fav={p in favourable}'


def test_is_ashtama_lagna_is_only_position_8():
    for p in range(1, 13):
        assert is_ashtama_lagna(p) == (p == 8)


# ── Lagna class helpers (Chara / Sthira / Dvisvabhava) ─────────────

def test_lagna_classes_partition_all_12_rashis():
    """Every rashi belongs to exactly one class — Chara, Sthira, or
    Dvisvabhava. No overlap, no gaps."""
    union = LAGNA_CHARA | LAGNA_STHIRA | LAGNA_DVISVABHAVA
    assert len(union) == 12, f'expected 12 rashis total, got {len(union)}'
    assert not (LAGNA_CHARA & LAGNA_STHIRA)
    assert not (LAGNA_CHARA & LAGNA_DVISVABHAVA)
    assert not (LAGNA_STHIRA & LAGNA_DVISVABHAVA)
    assert len(LAGNA_CHARA) == 4
    assert len(LAGNA_STHIRA) == 4
    assert len(LAGNA_DVISVABHAVA) == 4


def test_class_membership_matches_classical_assignment():
    """Spot-check the classical mapping (Muhurta Chintamani)."""
    # Chara (movable): Mesha, Karka, Tula, Makara
    assert lagna_class_of('Mesha') == 'Chara'
    assert lagna_class_of('Makara') == 'Chara'
    # Sthira (fixed): Vrishabha, Simha, Vrischika, Kumbha
    assert lagna_class_of('Vrishabha') == 'Sthira'
    assert lagna_class_of('Simha') == 'Sthira'
    # Dvisvabhava (dual): Mithuna, Kanya, Dhanu, Meena
    assert lagna_class_of('Mithuna') == 'Dvisvabhava'
    assert lagna_class_of('Meena') == 'Dvisvabhava'


def test_lagna_class_of_unknown_rashi_returns_none():
    assert lagna_class_of('NotARashi') is None


def test_lagnas_in_class_returns_the_right_set():
    assert lagnas_in_class('Chara') == LAGNA_CHARA
    assert lagnas_in_class('Sthira') == LAGNA_STHIRA
    assert lagnas_in_class('Dvisvabhava') == LAGNA_DVISVABHAVA


def test_lagnas_in_class_raises_on_unknown_class():
    import pytest
    with pytest.raises(ValueError):
        lagnas_in_class('Bogus')
